# Contributing to Folksonomy Engine API

Welcome! As a collaborative, civic-minded project, we always welcome new participants.

This project shares the global [Open Food Facts' code of conduct](https://world.openfoodfacts.org/code-of-conduct).

## Very First Steps

Suggestions for better understanding what we do and how we work:

* [Explore our database](https://world.openfoodfacts.org/) – This is the core of our project.
* Install and explore [our mobile app](https://world.openfoodfacts.org/open-food-facts-mobile-app):
  * Scan a few products and enjoy.
  * Update a product: update photos, fill in missing data.
* Check our [latest blog posts](https://blog.openfoodfacts.org) to better understand how the project is evolving.
* Review our [major components map](https://github.com/openfoodfacts/.github/blob/main/profile/README.md#major_components_map) to understand our ecosystem.
* Visit [our wiki](https://wiki.openfoodfacts.org) for useful knowledge.

## Contributing

Folksonomy Engine is fully developed on GitHub. You will need a GitHub account to participate.

* All contributions [start with an issue](https://github.com/openfoodfacts/folksonomy_api/issues):
  * Issues are prioritized:
    * `P0` tag means high-priority issues, while `P4` means lower priority.
    * [Good first issues](https://github.com/openfoodfacts/folksonomy_api/issues?q=state%3Aopen%20label%3A%22%F0%9F%8F%84%E2%80%8D%E2%99%80%EF%B8%8F%20good%20first%20issue%22) are a great start for beginners.

### Development Practices

* We use an [.editorconfig](https://editorconfig.org/) file to help developers maintain a consistent coding style.
* Before starting work, express your interest in the corresponding issue.
* Create your own Git branches – one per topic/feature/bugfix, commit frequently, and open Pull Requests when ready.
* We implement automated tests using [Pytest](https://docs.pytest.org/en/stable/); see the `tests` directory.
* Handle database migrations using [Yoyo](https://ollycope.com/software/yoyo/latest/); see `db-migration.py`.

## Code Style and Linting

We use [pre-commit](https://pre-commit.com/) hooks to maintain code quality and consistency. The hooks automatically format code and catch common issues before committing.

### Setting Up Pre-commit (Optional)

While not mandatory, using pre-commit hooks can save you time by automatically fixing issues before they are flagged in CI:

1. Install pre-commit:
   ```sh
   pip install pre-commit
   ```

2. Install the Git hooks:
   ```sh
   pre-commit install
   ```

3. Pre-commit will now run automatically on each commit.

### Running Without Pre-commit

If you prefer not to use pre-commit, you can manually run the same checks:

1. Install Ruff:
   ```sh
   pip install ruff
   ```

2. Run linting and formatting before submitting your PR:
   ```sh
   ruff check --fix .
   ruff format .
   ```

Our CI pipeline runs these same checks on all PRs, so ensuring your code passes these checks locally will help your PR get merged faster.
