# Changelog

## [0.6.3](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.3...v0.6.3) (2023-04-18)


### Documentation

* fix config settings ([20e130d](https://github.com/engisalor/sketch-grammar-explorer/commit/20e130d4cd3bfe1842ffc4f71766bfa76ccf6268))


### Miscellaneous Chores

* release 0.6.3.post1 ([a3b3425](https://github.com/engisalor/sketch-grammar-explorer/commit/a3b342508babcc5e2fc87932f99eb4140dbd0800))

## [0.6.3](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.2...v0.6.3) (2023-04-17)


### Bug Fixes

* fixes [#12](https://github.com/engisalor/sketch-grammar-explorer/issues/12) Set configuration once ([fb8e1dc](https://github.com/engisalor/sketch-grammar-explorer/commit/fb8e1dc5d0b4fdd48f8af438808b7b303c803f67))
* fixes [#14](https://github.com/engisalor/sketch-grammar-explorer/issues/14) Labeled attributes cause problems ([f66d1f4](https://github.com/engisalor/sketch-grammar-explorer/commit/f66d1f4f429e520cb071db9b0d6c93a84ee708b6))
* fixes [#15](https://github.com/engisalor/sketch-grammar-explorer/issues/15) simple_query escaping ([4b46c60](https://github.com/engisalor/sketch-grammar-explorer/commit/4b46c608d9ad36e313b03404a8c7146490673cde))
* fixes [#16](https://github.com/engisalor/sketch-grammar-explorer/issues/16) Warn if max_responses reached ([1025ba3](https://github.com/engisalor/sketch-grammar-explorer/commit/1025ba31441f72909d8d2f430adb9d4cc3a299dc))

## [0.6.2](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.1...v0.6.2) (2023-03-01)

This release excludes testing files from package distribution.

### Bug Fixes

* add imports for intellisense ([32589be](https://github.com/engisalor/sketch-grammar-explorer/commit/32589be4fccde146a7f5db4c76a337f705ed4ead))

## [0.6.1](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.0...v0.6.1) (2023-03-01)

This release fixes an issue where setuptools ignored subpackages.

### Bug Fixes

* simplify import paths fixes [#10](https://github.com/engisalor/sketch-grammar-explorer/issues/10) ([6175cd9](https://github.com/engisalor/sketch-grammar-explorer/commit/6175cd980e5c864ef8db23528483f277ed688f4e))

## [0.6.0](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.5.5...v0.6.0) (2023-02-28)

### ⚠ BREAKING CHANGES

**NOTE** this release was yanked to resolve an issue with package distribution settings

This release is a complete rebuild of the package; it improves and simplifies API call management in a number of ways. 

- More modules, more customization, more logical workflows
- Caching has been offloaded to the [requests-cache package](https://github.com/requests-cache/requests-cache). 
- Methods from `0.5.5` are intact still but may later be deprecated. Import paths have also moved. 
- Unit testing has also been implemented; logging has been reduced to a minimum.

See documentation for changes.
