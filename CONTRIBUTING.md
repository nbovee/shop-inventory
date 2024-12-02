# Contributing guidelines

## Setup
1. Clone this repository

2. Install recommended VSCode Extensions:
   - Python extension for VSCode
   - Ruff
   - Prettier formatter
   - Docker extension for VSCode

3. Disable any conflicting VSCode Extensions:
   - Pylint (it doesn't handle Django's runtime generated code well)

4. Set up your development environment:
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create and activate virtual environment
   uv venv

   # Install dependencies
   uv sync

   # Initialize pre-commit hooks
   uvx pre-commit install
   ```

## Development Workflow
1. Create a new branch for your feature/fix
2. Make your changes
3. Run tests:
   ```bash
   cd shop-inventory
   ./pytest.sh
   ```
4. Commit your changes - pre-commit hooks will automatically:
   - Format code with Ruff
   - Run linting checks
   - Check for common issues

5. Push your changes and create a pull request

## Dependencies
- Use `pyproject.toml` for managing dependencies
- Add new dependencies to the appropriate section:
  - Main dependencies under `dependencies`
  - Development tools under `dependency-groups.dev`
  - Production requirements under `dependency-groups.prod`

## Code Style
- Follow PEP 8 guidelines
- Use Ruff for formatting (configured in pyproject.toml)
- Keep functions and methods focused and well-documented
- Write tests for new functionality

## Testing
- Write tests in the appropriate `tests.py` file
- Run tests with coverage reporting using `./pytest.sh`
- Aim to maintain or improve test coverage
