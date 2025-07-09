# GitHub Actions CI/CD Workflows

This directory contains the CI/CD pipeline configurations for the STORM project.

## Workflows

### CI Workflow (`ci.yml`)

Runs on every push to main/develop and on all pull requests.

**Jobs:**

1. **Lint**: Code quality checks
   - Ruff (linting)
   - Black (formatting)
   - isort (import sorting)
   - MyPy (type checking - optional)

2. **Test**: Unit test execution
   - Runs on Python 3.10 and 3.11
   - Coverage reporting with Codecov
   - Parallel test execution

3. **Security**: Security scanning
   - Trivy for vulnerability scanning
   - Bandit for Python security issues
   - SARIF upload for GitHub Security tab

4. **Build Test**: Docker image validation
   - Builds the Docker image
   - Verifies non-root user setup
   - Uses BuildKit caching

## Environment Variables

- `PYTHON_VERSION`: Default Python version (3.11)

## Caching Strategy

- Pip dependencies cached per Python version
- Docker layers cached using GitHub Actions cache
- Cache keys include requirements.txt hash for invalidation

## Security Considerations

- No secrets in workflow files
- Security scans don't fail builds (yet) to allow gradual adoption
- SARIF results uploaded for GitHub Security tracking

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Test the entire CI workflow
act -j lint
act -j test
act -j security

# Test a specific event
act pull_request
```

## Future Enhancements

- Add integration tests
- Add E2E tests  
- Add deployment workflows
- Add release automation
- Add dependency updates automation