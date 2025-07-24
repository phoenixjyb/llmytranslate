# Contributing to LLM Translation Service

## Git Workflow

This project follows a standard Git workflow with feature branches and pull requests.

### Branch Structure

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development branches
- `hotfix/*` - Critical bug fixes
- `release/*` - Release preparation branches

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

3. **Keep your branch updated**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a pull request** to merge into `main`

### Commit Message Convention

We use conventional commits for clear and consistent commit messages:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add Chinese language detection
fix: resolve Ollama connection timeout issue
docs: update API documentation
test: add integration tests for translation service
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

This will run:
- Black (code formatting)
- Flake8 (linting)
- MyPy (type checking)
- Tests

### Release Process

1. Create a release branch: `git checkout -b release/v1.0.0`
2. Update version numbers and CHANGELOG
3. Test thoroughly
4. Merge to main and tag: `git tag v1.0.0`
5. Deploy to production

## Code Review Guidelines

- All changes must go through pull request review
- At least one approval required
- All tests must pass
- Code coverage should not decrease
- Documentation must be updated for API changes

## Issue Tracking

- Use GitHub Issues for bug reports and feature requests
- Label issues appropriately (bug, enhancement, documentation, etc.)
- Reference issues in commit messages: `fixes #123`

## Getting Help

- Check existing documentation first
- Search closed issues for similar problems
- Create a new issue with detailed reproduction steps
- Join our development discussions
