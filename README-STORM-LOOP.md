# STORM-Loop: Enhanced Academic Knowledge Curation System

[![CI](https://github.com/huluobohua/storm-loop/actions/workflows/ci.yml/badge.svg)](https://github.com/huluobohua/storm-loop/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/huluobohua/storm-loop/branch/main/graph/badge.svg)](https://codecov.io/gh/huluobohua/storm-loop)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

STORM-Loop is an enhanced version of the [STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking)](https://github.com/stanford-oval/storm) system, specifically designed for academic research and knowledge curation.

## 🚀 Features

### Core Enhancements over STORM
- **Academic Source Integration**: OpenAlex and Crossref APIs for peer-reviewed papers
- **Perplexity Fallback**: General knowledge retrieval via Perplexity when academic sources lack results
- **Multi-Agent Research Architecture**: Specialized agents for research, criticism, and verification
- **Enhanced Quality Assurance**: Multi-level validation and academic rigor checking
- **Citation Management**: Real-time verification and formatting in multiple styles
- **Collaborative Features**: Human expert integration and review workflows
- **AI-Driven Research Planning**: Intelligent topic analysis and strategy generation

### Operation Modes
- **Academic Mode**: Full academic rigor with peer-review prioritization
- **Wikipedia Mode**: Original STORM behavior for general knowledge
- **Hybrid Mode**: Balanced approach combining both academic and general sources

## 🏗️ Project Structure

```
storm_loop/
├── __init__.py                 # Package initialization
├── config.py                  # Configuration management
├── main.py                     # FastAPI application entry point
├── agents/                     # Multi-agent framework
├── models/                     # Data models
├── services/                   # Service layer
└── utils/                      # Utility modules
    └── logging.py             # Logging configuration

tests/                          # Test suite
├── conftest.py                # Pytest configuration
├── test_config.py             # Configuration tests
└── test_utils.py              # Utility tests

.github/workflows/              # CI/CD pipelines
├── ci.yml                     # Main CI workflow

Configuration Files:
├── pyproject.toml             # Project metadata and tool config
├── requirements-storm-loop.txt # Enhanced dependencies
├── .pre-commit-config.yaml    # Pre-commit hooks
└── .gitignore                 # Git ignore patterns
```

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- Redis server (for caching)
- Git

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/huluobohua/storm-loop.git
cd storm-loop
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-storm-loop.txt
pip install -e .[dev]
# If tests fail with `ModuleNotFoundError: No module named 'pydantic'`,
# ensure the enhanced requirements file was installed.
```

4. **Install pre-commit hooks**
```bash
pre-commit install
```

5. **Start Redis server**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally (macOS)
brew install redis
brew services start redis
```

## 🔧 Configuration

Create a `.env` file in the project root:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
# Omit to disable Perplexity fallback

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAlex Configuration (recommended for better rate limits)
OPENALEX_EMAIL=your_email@example.com

# Operation Mode (academic/wikipedia/hybrid)
STORM_LOOP_MODE=hybrid

# Logging
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### Start the Application

```bash
# Development mode with auto-reload
python -m storm_loop.main

# Or using uvicorn directly
uvicorn storm_loop.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for the interactive API documentation.

### Basic API Usage

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Get configuration
response = requests.get("http://localhost:8000/config")
print(response.json())
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=storm_loop --cov-report=html

# Run specific test categories
pytest -m "unit"          # Unit tests only
pytest -m "integration"   # Integration tests only
pytest -m "not slow"      # Skip slow tests
```

## 🔍 Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code
black storm_loop tests

# Lint code
flake8 storm_loop tests

# Sort imports
isort storm_loop tests

# Type checking
mypy storm_loop

# Run all pre-commit hooks
pre-commit run --all-files
```

## 📋 Development Roadmap

This project follows a structured development roadmap aligned with GitHub issues:

### Phase 1: Foundation
- [x] **Task 1**: Project setup and environment configuration
- [ ] **Task 2**: Academic source integration (OpenAlex, Crossref)
- [ ] **Task 3**: Redis caching layer implementation

### Phase 2: Multi-Agent Architecture  
- [ ] **Task 4**: Multi-agent research framework
- [ ] **Task 5**: Enhanced information storage

### Phase 3: Quality Assurance
- [ ] **Task 6**: Citation verification system
- [ ] **Task 7**: Quality assurance pipeline

### Phase 4: Advanced Features
- [ ] **Task 8**: Research planning capabilities
- [ ] **Task 9**: Collaborative features

### Phase 5: Integration & Testing
- [ ] **Task 10**: System integration
- [ ] **Task 15**: Comprehensive testing

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and ensure tests pass
4. **Run code quality checks**: `pre-commit run --all-files`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines (enforced by Black and Flake8)
- Write comprehensive tests for new features
- Update documentation for any API changes
- Ensure all CI checks pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original [STORM](https://github.com/stanford-oval/storm) team at Stanford for the foundational framework
- [OpenAlex](https://openalex.org/) for academic paper data
- [Crossref](https://www.crossref.org/) for publication metadata
- All contributors and the open-source community

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/huluobohua/storm-loop/issues)
- **Documentation**: Available in the `/docs` directory (coming soon)
- **API Docs**: http://localhost:8000/docs when running locally

---

**STORM-Loop**: Enhancing knowledge curation with academic rigor and AI-powered research coordination.