# Contributing to Folksonomy Engine API

Welcome! As a collaborative, civic-minded project, we always welcome new participants.

This project share the global [Open Food Facts' code of conduct](https://world.openfoodfacts.org/code-of-conduct).

## Very first steps

Suggestions for better understanding what we do and how we work:
* [Have a look at our database](https://world.openfoodfacts.org/), this the core of our project
* Install and explore [our mobile app](https://world.openfoodfacts.org/open-food-facts-mobile-app)
  * Scan few products and enjoy
  * Update a product: update photos; fill the missing data
* Check our [last blog posts](https://blog.openfoodfacts.org), allowing you to better understand how the project is growing
* Check our [major components map](https://github.com/openfoodfacts/.github/blob/main/profile/README.md#major_components_map), to understand our components' ecosystem
* Hey, [we also have a wiki](https://wiki.openfoodfacts.org), where we can find useful knowledge

## Contributing

Folksonomy Engine is fully developped on Github. You will need a Github user account to participate.

* All contributions [start with an issue](https://github.com/openfoodfacts/folksonomy_api/issues)
  * Issues are prioritized:
    * P0 tag means high priority issues; while P4 means lower priority
    * [Good first issues](https://github.com/openfoodfacts/folksonomy_api/issues?q=state%3Aopen%20label%3A%22%F0%9F%8F%84%E2%80%8D%E2%99%80%EF%B8%8F%20good%20first%20issue%22), is a good start for beginners

* Development practices
  * We use an [`.editorconfig`](./.editorconfig) file to help developpers maintain consistent coding style (see [EditorConfig](https://editorconfig.org/))
  * Want to start working on something: express your wish in the corresponding issue
  * Create your own git branches, one per topic/feature/bugfix; commit frequently; open Pull Requests when ready
  * We try to implement as many automated tests as possible, thanks to [Pytest](https://docs.pytest.org/en/stable/); see [./tests](./tests) directory
  * DB migrations, if any, needs to be handled by [Yoyo](https://ollycope.com/software/yoyo/latest/); see ./db-migration.py
