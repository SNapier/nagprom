# Contributing to NagProm

Thank you for your interest in contributing to NagProm! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Development Setup

### Prerequisites
- Python 3.8+ (recommended: 3.11 or 3.12)
- Git
- Prometheus server (for testing)
- Prometheus node exporter (for testing)
- Nagios Core 4.5.X

### Local Development
```bash
# Clone your fork
git clone https://github.com/yourusername/nagprom.git
cd nagprom

# Install dependencies
pip install -r api/requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black isort

# Run tests
pytest core/test_*.py -v

# Run linters
flake8 api/ analytics/ core/ --max-line-length=100
black api/ analytics/ core/
isort api/ analytics/ core/
```

## 📝 Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and under 50 lines when possible
- Use type hints where appropriate

## 🧪 Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for at least 80% code coverage
- Test on multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)

## 📚 Documentation

- Update README.md if adding new features
- Add docstrings to new functions
- Update API documentation if endpoints change
- Include examples for new features

## 🔍 Pull Request Guidelines

- Provide a clear description of changes
- Include screenshots for UI changes
- Reference related issues
- Ensure CI/CD checks pass
- Request reviews from maintainers

## 🐛 Bug Reports

- Use the bug report template
- Include steps to reproduce
- Provide environment details
- Add screenshots if applicable

## 💡 Feature Requests

- Use the feature request template
- Explain the use case
- Consider implementation complexity
- Discuss with maintainers first

## 📄 License

By contributing to NagProm, you agree that your contributions will be licensed under the MIT License.

## 🤝 Questions?

Feel free to open an issue for questions about contributing or the development process.
