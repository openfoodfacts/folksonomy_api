# Changelog

## [1.2.0](https://github.com/openfoodfacts/folksonomy_api/compare/v1.1.0...v1.2.0) (2025-06-19)


### Features

* add Docker support for Folksonomy API ([#254](https://github.com/openfoodfacts/folksonomy_api/issues/254)) ([f67dd13](https://github.com/openfoodfacts/folksonomy_api/commit/f67dd13aeabdb86b900dd0fbab38651421027bb8))
* Add message for existing property in product tag API ([#248](https://github.com/openfoodfacts/folksonomy_api/issues/248)) ([5a6b6d1](https://github.com/openfoodfacts/folksonomy_api/commit/5a6b6d1ff5ccd4bb53d4a36d344f9986926b8fd3))
* Add pre-commit configuration for code quality checks ([#258](https://github.com/openfoodfacts/folksonomy_api/issues/258)) ([db07627](https://github.com/openfoodfacts/folksonomy_api/commit/db07627996bfc81ddbf93cf61e111be02fa64c53)), closes [#256](https://github.com/openfoodfacts/folksonomy_api/issues/256)
* Add response models (PUT/POST/DELETE endpoints untouched) ([#238](https://github.com/openfoodfacts/folksonomy_api/issues/238)) ([8e4d800](https://github.com/openfoodfacts/folksonomy_api/commit/8e4d800ea89fff575de226e7d0821f4d95e4f523))
* adds allow_origins URLs for local development ([#284](https://github.com/openfoodfacts/folksonomy_api/issues/284)) ([18ea2ee](https://github.com/openfoodfacts/folksonomy_api/commit/18ea2ee221bc415f7306b81d86b2df039ff59f6b))
* Adds logic to fetch specific keys for a product ([c3bc052](https://github.com/openfoodfacts/folksonomy_api/commit/c3bc05261cbd57c2fbdf5e5267f3082d49c6d5da))
* adds search query for /keys ([0798a27](https://github.com/openfoodfacts/folksonomy_api/commit/0798a27b78341148d12b8472a1e8c525f313d699))
* Adds type for /keys endpoint ([1ef42ff](https://github.com/openfoodfacts/folksonomy_api/commit/1ef42ffdd275b1d8e743fd93ddf641ab4e2209e5))
* Improve setup doc ([962dd32](https://github.com/openfoodfacts/folksonomy_api/commit/962dd326fd4cfb1348406383e6678c457543dbc7))
* Migrate dependency management to Poetry ([#247](https://github.com/openfoodfacts/folksonomy_api/issues/247)) ([45d881a](https://github.com/openfoodfacts/folksonomy_api/commit/45d881af3a6692412d9708ce5d644c6da658cf11))
* New route for values ([48cef31](https://github.com/openfoodfacts/folksonomy_api/commit/48cef3148c0e1d7ec22dedec4dce7860916583a4))


### Bug Fixes

* add newline at end of .github/labeler.yml ([b86b0df](https://github.com/openfoodfacts/folksonomy_api/commit/b86b0dfeb09843932435251eb39d40128892b37c))
* **ci:** skip workflow on forked repos ([#281](https://github.com/openfoodfacts/folksonomy_api/issues/281)) ([d2757f3](https://github.com/openfoodfacts/folksonomy_api/commit/d2757f352d3525fe963d4b7d10e72421b7318240))
* PUT API response does not send ValidationError when expected ([#235](https://github.com/openfoodfacts/folksonomy_api/issues/235)) ([7f3a589](https://github.com/openfoodfacts/folksonomy_api/commit/7f3a5891c73b9508d5b1dcfe0735b61cd20ad5ba))
* pytest error with connection leak ([#270](https://github.com/openfoodfacts/folksonomy_api/issues/270)) ([5c735f5](https://github.com/openfoodfacts/folksonomy_api/commit/5c735f550f3732571a8e5dd92b068db311b5346f))
* Returns a JSON response if desired result is not found ([#234](https://github.com/openfoodfacts/folksonomy_api/issues/234)) ([e83fb5b](https://github.com/openfoodfacts/folksonomy_api/commit/e83fb5bb5da06bc7766d4624b3b49ee63cb39ca6))
* updated labeler.yml file ([#279](https://github.com/openfoodfacts/folksonomy_api/issues/279)) ([77e27d0](https://github.com/openfoodfacts/folksonomy_api/commit/77e27d0edc750b417e525f29986c5cfd36e8b079))

## [1.1.0](https://github.com/openfoodfacts/folksonomy_api/compare/v1.0.1...v1.1.0) (2024-09-06)


### Features

* new auth to enable other instances auth ([#199](https://github.com/openfoodfacts/folksonomy_api/issues/199)) ([b6729d3](https://github.com/openfoodfacts/folksonomy_api/commit/b6729d3984e82005f6d3a04d96466c8a1f1959e3))


### Bug Fixes

* strip keys on CRUD operations ([#165](https://github.com/openfoodfacts/folksonomy_api/issues/165)) ([c0ee55b](https://github.com/openfoodfacts/folksonomy_api/commit/c0ee55b5a2d6527732dc8c0af09a5d86492fa923))
* strip values on insertion ([#167](https://github.com/openfoodfacts/folksonomy_api/issues/167)) ([fbc1194](https://github.com/openfoodfacts/folksonomy_api/commit/fbc1194699d3e38fa58dd69bec4d0eae76921dad))

## [1.0.1](https://github.com/openfoodfacts/folksonomy_api/compare/v1.0.0...v1.0.1) (2023-12-11)


### Bug Fixes

* fix db migration script ([a188613](https://github.com/openfoodfacts/folksonomy_api/commit/a1886131973f088bd3667baa4a4aa9978d6bd167))
* fix transaction handling + use async everywhere ([#148](https://github.com/openfoodfacts/folksonomy_api/issues/148)) ([36f5f27](https://github.com/openfoodfacts/folksonomy_api/commit/36f5f27c17d87de65560dcff077599e79cbecbaf))

## 1.0.0 (2023-04-12)


### Features

* add logging during runtime ([#112](https://github.com/openfoodfacts/folksonomy_api/issues/112)) ([dc2c5db](https://github.com/openfoodfacts/folksonomy_api/commit/dc2c5dbb3e6b31fa033285faf02e2e42f75d8e14))


### Bug Fixes

* changed barcode limit: to 24 digits ([#86](https://github.com/openfoodfacts/folksonomy_api/issues/86)) ([2f33a80](https://github.com/openfoodfacts/folksonomy_api/commit/2f33a80b627d2bd01811d2649e6c54b0b4451a62))
