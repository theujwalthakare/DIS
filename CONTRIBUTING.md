# Contributing to DIS

We welcome contributions to the Digital Immune System project! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/DIS.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest tests/unit/ -v`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
make test

# Run tests with coverage
make test-cov
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and concise

## Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Use pytest fixtures for common setup

## Documentation

- Update README.md if adding new features
- Add docstrings to all public APIs
- Update ARCHITECTURE.md for design changes
- Include examples in docstrings

## Pull Request Process

1. Update documentation as needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update the README with details of changes
5. The PR will be merged once reviewed and approved

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's code of conduct

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about the code
- Suggestions for improvements

Thank you for contributing!
