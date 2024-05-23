# Contributing guidelines

## Setup
1. Clone this repository
2. Install all recommended VSCode Extensions:
   - Python extension for VSCode
   - Ruff
   - Black formatter
   - Prettier formatter
   - Docker extension for VSCode
3. Disable the following VSCode Extensions if you have them:
   - Pylint (it doesn't like Django's runtime generated code)
4. Create a virtual environment
   - run `python -m venv .venv`
   - select yes on a popup that VSCode may prompt you with about virtual environments
   - restart your built in terminal, allowing the virtual environment to automatically load
   - run `pip install -r requirements.txt -r requirements-dev.txt` to install project and dev dependencies for your linter
   - run `pre-commit install` to initialize `pre-commit`
