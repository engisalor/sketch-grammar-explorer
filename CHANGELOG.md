# Changelog

## [0.6.1](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.0...v0.6.1) (2023-03-01)


### Bug Fixes

* simplify import paths fixes [#10](https://github.com/engisalor/sketch-grammar-explorer/issues/10) ([6175cd9](https://github.com/engisalor/sketch-grammar-explorer/commit/6175cd980e5c864ef8db23528483f277ed688f4e))


### Documentation

* readme ([bba5819](https://github.com/engisalor/sketch-grammar-explorer/commit/bba5819b83d79c1106ae9d9379c3e3a74ea68b9d))
* update readme ([ff63af4](https://github.com/engisalor/sketch-grammar-explorer/commit/ff63af487a09a22aeca69196aa08cfda7a77c7a6))

## [0.6.0](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.5.5...v0.6.0) (2023-02-28)

### ⚠ BREAKING CHANGES

This release is a complete rebuild of the package; it improves and simplifies API call management in a number of ways. 

- More modules, more customization, more logical workflows
- Caching has been offloaded to the [requests-cache package](https://github.com/requests-cache/requests-cache). 
- Methods from `0.5.5` are intact still but may later be deprecated. Import paths have also moved. 
- Unit testing has also been implemented; logging has been reduced to a minimum.

See current documentation for changes.
