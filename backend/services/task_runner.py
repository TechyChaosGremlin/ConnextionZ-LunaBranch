"""
Async task runner for background processing.

Provides:
- Background task decorator for async functions
- Retry logic with exponential backoff
- Dead letter queue integration
- Task timeout handling
- Task status tracking
"""

from __future__ import annotations

import asyncio
import functools
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Optional, TypeVar, Generic

from app.config import settings
from services.rabbitmq_service import rabbitmq_service

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskError(Exception):
    """Base exception for task-related errors."""
    pass


class TaskRetryError(TaskError):
    """Exception to trigger task retry."""
    pass


class TaskMaxRetriesExceeded(TaskError):
    """Exception raised when max retries are exceeded."""
    pass


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class AsyncTaskRunner:
    """
    Async task runner with retry logic and dead letter handling.

    Features:
    - Decorator-based task definition
    - Configurable retry with exponential backoff
    - Dead letter queue for failed tasks
    - Task timeout handling
    - Task status tracking in Redis
    """

    def __init__(
        self,
        redis_service=None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        task_timeout: float = 300.0,
    ):
        """
        Initialize task runner.

        Args:
            redis_service: Redis service for task status tracking
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            backoff_factor: Exponential backoff multiplier
            task_timeout: Task timeout in seconds
        """
        self.redis = redis_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.task_timeout = task_timeout
        self._tasks: dict[str, Callable] = {}

    def task(
        self,
        name: str | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        timeout: float | None = None,
    ):
        """
        Decorator to register an async function as a background task.

        Args:
            name: Task name (default: function name)
            max_retries: Override default max retries
            retry_delay: Override default retry delay
            timeout: Override default timeout

        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
            task_name = name or func.__name__
            self._tasks[task_name] = func

            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                return await self._execute_task(
                    task_name,
                    func,
                    max_retries or self.max_retries,
                    retry_delay or self.retry_delay,
                    timeout or self.task_timeout,
                    *args,
                    **kwargs,
                )
            return wrapper
        return decorator

    async def _execute_task(
        self,
        task_name: str,
        func: Callable[..., Coroutine[Any, Any, T]],
        max_retries: int,
        retry_delay: float,
        timeout: float,
        *args,
        **kwargs,
    ) -> T:
        """
        Execute a task with retry logic.

        Args:
            task_name: Task name for logging/tracking
            func: Async function to execute
            max_retries: Max retry attempts
            retry_delay: Initial retry delay
            timeout: Task timeout
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            TaskMaxRetriesExceeded: If all retries are exhausted
        """
        task_id = f"{task_name}:{datetime.now().isoformat()}"
        last_error = None

        # Update task status
        await self._update_task_status(task_id, TaskStatus.RUNNING)

        for attempt in range(max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout,
                )

                # Success
                await self._update_task_status(task_id, TaskStatus.SUCCESS)
                return result

            except TaskRetryError as e:
                # Explicit retry request
                last_error = e
                if attempt < max_retries:
                    delay = retry_delay * (self.backoff_factor ** attempt)
                    logger.warning(
                        f"Task {task_name} attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {e}"
                    )
                    await self._update_task_status(task_id, TaskStatus.RETRYING)
                    await asyncio.sleep(delay)
                else:
                    break

            except Exception as e:
                # Unexpected error
                last_error = e
                error_trace = traceback.format_exc()

                if attempt < max_retries:
                    delay = retry_delay * (self.backoff_factor ** attempt)
                    logger.error(
                        f"Task {task_name} attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {e}\n{error_trace}"
                    )
                    await self._update_task_status(task_id, TaskStatus.RETRYING)
                    await asyncio.sleep(delay)
                else:
                    break

        # All retries exhausted
        await self._update_task_status(task_id, TaskStatus.FAILED)
        await self._send_to_dlq(task_name, last_error, args, kwargs)

        raise TaskMaxRetriesExceeded(
            f"Task {task_name} failed after {max_retries + 1} attempts: {last_error}"
        )

    async def _update_task_status(self, task_id: str, status: str) -> None:
        """Update task status in Redis if available."""
        if self.redis:
            try:
                await self.redis.cache_set(
                    f"task_status:{task_id}",
                    {
                        "status": status,
                        "updated_at": datetime.now().isoformat(),
                    },
                    ttl=86400,  # 24 hours
                )
            except Exception as e:
                logger.warning(f"Failed to update task status: {e}")

    async def _send_to_dlq(
        self,
        task_name: str,
        error: Exception,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Send failed task to dead letter queue."""
        try:
            dlq_message = {
                "task_name": task_name,
                "error": str(error),
                "error_type": type(error).__name__,
                "args": str(args),
                "kwargs": str(kwargs),
                "failed_at": datetime.now().isoformat(),
            }

            await rabbitmq_service.publish_to_work_queue(
                f"{task_name}.dlq",
                dlq_message,
                persistent=True,
            )
            logger.info(f"Sent failed task {task_name} to DLQ")
        except Exception as e:
            logger.error(f"Failed to send task {task_name} to DLQ: {e}")

    async def execute_task_async(
        self,
        task_name: str,
        *args,
        **kwargs,
    ) -> None:
        """
        Execute a registered task asynchronously (fire and forget).

        Args:
            task_name: Name of registered task
            *args: Task arguments
            **kwargs: Task keyword arguments
        """
        if task_name not in self._tasks:
            raise ValueError(f"Task {task_name} not registered")

        func = self._tasks[task_name]
        asyncio.create_task(func(*args, **kwargs))
        logger.info(f"Started async task: {task_name}")


# Decorator for easy task definition
def background_task(
    name: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 300.0,
):
    """
    Decorator to define a background task.

    Usage:
        @background_task(name="send_email", max_retries=3)
        async def send_email(to: str, subject: str, body: str):
            # Send email logic
            pass

    Args:
        name: Task name
        max_retries: Maximum retry attempts
        retry_delay: Initial retry delay in seconds
        timeout: Task timeout in seconds

    Returns:
        Decorated function
    """
    runner = AsyncTaskRunner()

    def decorator(func):
        return runner.task(
            name=name,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )(func)
    return decorator
