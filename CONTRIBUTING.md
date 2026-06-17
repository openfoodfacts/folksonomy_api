# Contributing to Folksonomy Engine API

Welcome! As a collaborative, civic-minded project, we always welcome new participants.

This project shares the global [Open Food Facts Code of Conduct](https://world.openfoodfacts.org/code-of-conduct).

## Very First Steps

Suggestions for better understanding what we do and how we work:

- [Explore our database](https://world.openfoodfacts.org/) – This is the core of our project.
- Install and explore [our mobile app](https://world.openfoodfacts.org/open-food-facts-mobile-app):
  - Scan a few products and enjoy.
  - Update a product: update photos, fill in missing data.
- Check our [latest blog posts](https://blog.openfoodfacts.org) to better understand how the project is evolving.
- Review our [Major Components Map](https://github.com/openfoodfacts/.github/blob/main/profile/README.md#major_components_map) to understand our ecosystem.
- Visit [our wiki](https://wiki.openfoodfacts.org) for useful knowledge.

## Contributing

The Folksonomy Engine is fully developed on GitHub. You will need a GitHub account to participate.

- All contributions [start with an issue](https://github.com/openfoodfacts/folksonomy_api/issues):
  - Issues are prioritized:
    - `P0` tag means high-priority, while `P4` means lower priority.
    - [Good first issues](https://github.com/openfoodfacts/folksonomy_api/issues?q=state%3Aopen%20label%3A%22%F0%9F%8F%84%E2%80%8D%E2%99%80%EF%B8%8F%20good%20first%20issue%22) are a great starting point for beginners.

## Development Practices

- We use an [.editorconfig](https://editorconfig.org/) file to help maintain a consistent coding style.
- Before starting work, comment on the corresponding issue to express your interest.
- Create your own Git branches – one branch per topic/feature/bugfix.
- Commit frequently and open Pull Requests (PRs) when ready.
- We implement automated tests using [Pytest](https://docs.pytest.org/en/stable/); see the `tests/` directory.
- Handle database migrations using [Yoyo](https://ollycope.com/software/yoyo/latest/); see `db-migration.py`.

## Code Style and Linting

We use [Ruff](https://docs.astral.sh/ruff/) for Python linting and code formatting, along with [pre-commit](https://pre-commit.com/) hooks to maintain code quality and consistency.

### Pre-commit Hooks

The project uses pre-commit hooks to automatically handle:

- Fixing trailing whitespace
- Ensuring files end with a newline
- Checking JSON and YAML files
- Linting and formatting Python code with Ruff

**Pre-commit** is installed with the project dependencies.

To manually run all hooks:

```bash
poetry run pre-commit run --all-files
```

**Note**: Our CI pipeline runs these same checks on all PRs. Ensuring your code passes them locally will make your PR easier and faster to merge!
