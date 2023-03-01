# Changelog

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
