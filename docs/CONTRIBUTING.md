# Contributing to ConnextionZ Platform

Thank you for your interest in contributing to ConnextionZ! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Issue Reporting](#issue-reporting)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Exercise consideration and empathy in your communication
- Focus on what is best for the community and the platform users
- Refrain from demeaning, discriminatory, or harassing behavior

## Getting Started

### Prerequisites

- **Python 3.11+** (Backend development)
- **Node.js 18+** (Frontend development)
- **Docker Desktop** (Local infrastructure)
- **Git** (Version control)
- **VS Code** (Recommended IDE)

### First-Time Setup

1. **Fork the repository** (if external contributor)
   ```bash
   git fork <repository-url>
   ```

2. **Clone your fork**
   ```bash
   git clone <your-fork-url>
   cd ConnextionZ/connextionz-platform
   ```

3. **Set up local infrastructure**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Install backend dependencies**
   ```bash
   cd app
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # source venv/bin/activate    # macOS/Linux
   pip install -r requirements.txt
   ```

5. **Install frontend dependencies**
   ```bash
   cd ..
   npm install
   ```

6. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your local configuration
   ```

7. **Run the development servers**
   ```bash
   # Terminal 1: Backend
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Frontend
   npm start
   ```

## Development Workflow

### Branch Naming Convention

- **Feature branches**: `feature/description` (e.g., `feature/collaboration-marketplace`)
- **Bug fix branches**: `fix/description` (e.g., `fix/login-redirect-issue`)
- **Documentation branches**: `docs/description` (e.g., `docs/api-endpoint-examples`)
- **Refactor branches**: `refactor/description` (e.g., `refactor/repository-layer`)

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```bash
feat(auth): add two-factor authentication support

Implemented TOTP-based 2FA using pyotp library.
Added QR code generation for authenticator apps.
Updated user model with 2FA fields.

Closes #123
```

### Keeping Your Branch Updated

```bash
# Add upstream remote (if forked)
git remote add upstream <original-repo-url>

# Fetch latest changes
git fetch upstream

# Rebase your branch
git checkout feature/your-feature
git rebase upstream/main
```

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** for public functions and classes
- Use **Black** for code formatting (auto-formatter)
- Use **Flake8** for linting
- Use **MyPy** for static type checking

**Example:**
```python
from typing import List, Optional
from fastapi import APIRouter, Depends
from .repositories import UserRepository
from .models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    user_repo: UserRepository = Depends()
) -> User:
    """
    Retrieve a user by their ID.
    
    Args:
        user_id: The unique identifier of the user
        user_repo: Injected user repository dependency
        
    Returns:
        User object if found
        
    Raises:
        HTTPException: If user not found (404)
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### TypeScript/React (Frontend)

- Use **TypeScript** for all new code (no `any` types)
- Follow **Airbnb JavaScript Style Guide**
- Use **ESLint** and **Prettier** for code quality
- Use **functional components** with hooks (avoid class components)
- Use **named exports** for components

**Example:**
```typescript
import React, { useState, useEffect } from 'react';
import { User } from '../types/User';
import { userService } from '../services/userService';

interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ 
  userId, 
  onUpdate 
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const data = await userService.getById(userId);
        setUser(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch user');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="user-profile">
      <h1>{user.name}</h1>
      <p>{user.bio}</p>
    </div>
  );
};
```

### GraphQL

- Use **descriptive names** for queries and mutations
- Implement **pagination** for list queries
- Use **fragments** to share field selections
- Document **all schema types** with descriptions

**Example:**
```graphql
"""
Represents a user in the ConnextionZ platform
"""
type User {
  """
  Unique identifier of the user
  """
  id: ID!
  
  """
  Display name of the user
  """
  name: String!
  
  """
  URL-friendly identifier
  """
  username: String!
  
  """
  User's biography or description
  """
  bio: String
  
  """
  List of collaborations the user has participated in
  """
  collaborations(
    """
    Number of items to return
    """
    first: Int = 10
    
    """
    Pagination cursor
    """
    after: String
  ): CollaborationConnection!
}

type Query {
  """
  Fetch a user by their username
  """
  userByUsername(username: String!): User
}
```

## Testing Requirements

### Test Coverage Requirements

- **Minimum 80% code coverage** for new features
- **Unit tests** for all business logic
- **Integration tests** for API endpoints
- **E2E tests** for critical user flows

### Running Tests

**Backend:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

**Frontend:**
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- UserProfile.test.tsx

# Run in watch mode
npm test -- --watch
```

### Writing Tests

**Python (pytest):**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_user_success():
    """Test successful user retrieval"""
    response = client.get("/users/1")
    assert response.status_code == 200
    assert "id" in response.json()
    assert "name" in response.json()

def test_get_user_not_found():
    """Test user not found scenario"""
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
```

**TypeScript (Jest + React Testing Library):**
```typescript
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { UserProfile } from './UserProfile';
import { userService } from '../services/userService';

jest.mock('../services/userService');

describe('UserProfile', () => {
  it('displays user name after loading', async () => {
    const mockUser = { id: '1', name: 'John Doe', username: 'johndoe' };
    (userService.getById as jest.Mock).mockResolvedValue(mockUser);

    render(<UserProfile userId="1" />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('displays error message on fetch failure', async () => {
    (userService.getById as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<UserProfile userId="1" />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });
});
```

## Pull Request Process

### Before Creating a PR

1. **Ensure all tests pass**
   ```bash
   # Backend
   pytest --cov=app
   
   # Frontend
   npm test -- --coverage
   ```

2. **Run linters and formatters**
   ```bash
   # Backend
   black .
   flake8
   mypy .
   
   # Frontend
   npm run lint
   npm run format
   ```

3. **Update documentation** (if needed)
   - API documentation
   - README updates
   - Architecture decision records (ADRs)

4. **Rebase on latest main**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature
   ```

2. **Create PR via GitHub UI**
   - Use a clear, descriptive title
   - Fill out the PR template completely
   - Link related issues
   - Add screenshots (for UI changes)

3. **PR Title Format**
   ```
   <type>(<scope>): <description>
   
   Example: feat(auth): add two-factor authentication
   ```

4. **PR Description Template**
   ```markdown
   ## Description
   Brief description of what this PR does
   
   ## Changes Made
   - Change 1
   - Change 2
   
   ## Screenshots (if applicable)
   Add screenshots here
   
   ## Testing
   Describe how you tested these changes
   
   ## Checklist
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Lint and format checks pass
   - [ ] All tests pass
   - [ ] No console errors/warnings
   
   ## Related Issues
   Closes #123
   ```

### PR Review Process

- **At least 2 approvals** required for merge
- **All CI checks** must pass
- **Address reviewer feedback** promptly
- **Squash commits** before merging (clean git history)

### After Merge

- Delete your feature branch
- Pull latest main to your local
- Celebrate your contribution! 🎉

## Issue Reporting

### Bug Reports

Use the **Bug Report** issue template and include:
- **Clear title** summarizing the bug
- **Steps to reproduce** (numbered list)
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, browser, etc.)
- **Relevant logs** (error messages, console output)

**Example:**
```markdown
Title: Login fails with valid credentials

## Description
When attempting to log in with correct email and password, the system returns a 500 Internal Server Error.

## Steps to Reproduce
1. Navigate to /login
2. Enter valid email: test@example.com
3. Enter valid password: password123
4. Click "Login" button

## Expected Behavior
User should be redirected to dashboard and authenticated

## Actual Behavior
Server returns 500 Internal Server Error with message "Database connection failed"

## Environment
- OS: Windows 11
- Browser: Chrome 120.0.6099.109
- Local development environment

## Logs
```
ERROR:app.auth:Database connection failed
Traceback (most recent call last):
  File "app/auth.py", line 45, in login
    user = await user_repo.get_by_email(email)
```
```

### Feature Requests

Use the **Feature Request** issue template and include:
- **Clear title** describing the feature
- **Problem statement** (what problem does this solve?)
- **Proposed solution** (how should it work?)
- **Alternatives considered** (other ways to solve the problem)
- **Additional context** (screenshots, mockups, etc.)

## Questions?

If you have questions or need help:
- Check existing [issues](https://github.com/your-org/ConnextionZ/issues)
- Join our [Discord community](https://discord.gg/your-invite-link)
- Reach out to maintainers via [email](mailto:maintainers@connextionz.com)

Thank you for contributing to ConnextionZ! 🚀
