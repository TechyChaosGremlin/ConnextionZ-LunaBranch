"""add notifications

Revision ID: 9cd2fcf2fef2
Revises: 20260819_0010
Create Date: 2026-08-21 07:09:40.607517
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '9cd2fcf2fef2'
down_revision: Union[str, None] = '20260819_0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the notifications table.

    Notifications represent events that should appear in a user's notification
    inbox, such as another user liking one of their posts.

    recipient_id = user receiving the notification
    actor_id     = user who caused the notification
    post_id      = related post, when applicable
    """

    op.create_table(
        "notifications",

        # Unique identifier for each notification.
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        # The user who will RECEIVE the notification.
        #
        # Example:
        # If Billy likes Sarah's post, Sarah's user ID is recipient_id.
        sa.Column(
            "recipient_id",
            sa.Integer(),
            nullable=False,
        ),

        # The user who CAUSED the notification.
        #
        # Example:
        # If Billy likes Sarah's post, Billy's user ID is actor_id.
        #
        # This is nullable because some notification types, such as
        # system messages or milestones, may not have a user actor.
        sa.Column(
            "actor_id",
            sa.Integer(),
            nullable=True,
        ),

        # Describes what caused the notification.
        #
        # Initial example:
        #   "like"
        #
        # This can later support values such as:
        #   "comment"
        #   "follow"
        #   "mention"
        #   "collabRequest"
        #   "collabAccepted"
        #   "milestone"
        #   "system"
        sa.Column(
            "type",
            sa.String(length=40),
            nullable=False,
        ),

        # The post associated with the notification, if one exists.
        #
        # A like notification will have a post_id, while something like
        # a follow notification may not.
        sa.Column(
            "post_id",
            sa.Integer(),
            nullable=True,
        ),

        # Human-readable notification text displayed by the client.
        #
        # Example:
        #   "liked your post"
        sa.Column(
            "text",
            sa.Text(),
            nullable=False,
        ),

        # Tracks whether the recipient has already viewed/read the notification.
        # New notifications will normally begin as unread.
        sa.Column(
            "read",
            sa.Boolean(),
            nullable=False,
        ),

        # Timestamp used for ordering notifications from newest to oldest
        # and displaying relative times such as "12m", "3h", etc.
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        # If the actor deletes their account, preserve the notification but
        # remove the reference to that deleted user.
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),

        # Post-related notifications are removed if their post is deleted.
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            ondelete="CASCADE",
        ),

        # If a user deletes their account, there is no reason to keep
        # notifications belonging to that user.
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes make common notification lookups faster.
    #
    # For example, recipient_id will be frequently used for queries like:
    #
    #   "Give me all notifications belonging to the logged-in user."

    op.create_index(
        op.f("ix_notifications_actor_id"),
        "notifications",
        ["actor_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_notifications_created_at"),
        "notifications",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_notifications_id"),
        "notifications",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_notifications_post_id"),
        "notifications",
        ["post_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_notifications_recipient_id"),
        "notifications",
        ["recipient_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_notifications_type"),
        "notifications",
        ["type"],
        unique=False,
    )


def downgrade() -> None:
    """
    Reverse the notification migration.

    Alembic calls this function if the migration needs to be rolled back.
    Indexes are removed before the notifications table itself is removed.
    """

    op.drop_index(
        op.f("ix_notifications_type"),
        table_name="notifications",
    )

    op.drop_index(
        op.f("ix_notifications_recipient_id"),
        table_name="notifications",
    )

    op.drop_index(
        op.f("ix_notifications_post_id"),
        table_name="notifications",
    )

    op.drop_index(
        op.f("ix_notifications_id"),
        table_name="notifications",
    )

    op.drop_index(
        op.f("ix_notifications_created_at"),
        table_name="notifications",
    )

    op.drop_index(
        op.f("ix_notifications_actor_id"),
        table_name="notifications",
    )

    # Remove the table last, after its indexes have been removed.
    op.drop_table("notifications")