# Changelog

## [0.7.4](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.7.3...v0.7.4) (2024-05-11)


### Bug Fixes

* add makefile w/ api-doc curl command ([37f8f65](https://github.com/engisalor/sketch-grammar-explorer/commit/37f8f65fa1e22749dde5ccff64b76214a42a3332))


### Documentation

* add stratified random sampling example ([ba011d7](https://github.com/engisalor/sketch-grammar-explorer/commit/ba011d794c748c1853f04ad4075364814e13d430))

## [0.7.3](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.7.2...v0.7.3) (2024-02-08)


### Bug Fixes

* add util functions ([c1d8470](https://github.com/engisalor/sketch-grammar-explorer/commit/c1d8470b51c9cc43758fb1d06f50adc4a3a64d72))


### Documentation

* fix timeout doctest ([216064c](https://github.com/engisalor/sketch-grammar-explorer/commit/216064c774dc4713065007113b37ac24f7668a54))

## [0.7.2](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.7.1...v0.7.2) (2023-11-21)


### Bug Fixes

* enforce verbose type, params type hint ([f06011b](https://github.com/engisalor/sketch-grammar-explorer/commit/f06011b17ca7f67fa35c91f2cfd316219785c8b6))
* rename View.lines_to_annotation to ..._tacred ([cc42973](https://github.com/engisalor/sketch-grammar-explorer/commit/cc4297344781aa863edd338dd4e875a4e8b1f792))
* use unicode for json.dumps and yaml.dump ([68bb90b](https://github.com/engisalor/sketch-grammar-explorer/commit/68bb90b739f948b2aa42ade110bf8004ceb3de26))


### Documentation

* update readme ([d9fba24](https://github.com/engisalor/sketch-grammar-explorer/commit/d9fba24f3b21c0823dc845f3d3460b7a6fb2f170))

## [0.7.1](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.7.0...v0.7.1) (2023-10-10)


### Bug Fixes

* argparse verbose store_true ([79d7065](https://github.com/engisalor/sketch-grammar-explorer/commit/79d7065303cd80b9260f91cf54677f06438fbf48))

## [0.7.0](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.6.3...v0.7.0) (2023-10-10)


### ⚠ BREAKING CHANGES

* remove deprecated files: breaks 0.6.3

### Features

* rewrite main API controller script (WIP) ([54245cb](https://github.com/engisalor/sketch-grammar-explorer/commit/54245cb837660aeedf511fbd0493c593aaa9e15e))

### Bug Fixes

* add Data class and various call type methods ([352a0d6](https://github.com/engisalor/sketch-grammar-explorer/commit/352a0d63fc75f11b152f7a5f4edf6c040fcb3ca7))
* add json, yaml loading functions ([937bf57](https://github.com/engisalor/sketch-grammar-explorer/commit/937bf573058437ce40479bb19a2b3f23e16dd9cf))
* add json() method to CachedResponse ([74e6684](https://github.com/engisalor/sketch-grammar-explorer/commit/74e668461740008d4a38b0fb1a6395f8bf90e9c2))
* add query module w/ simple & fuzzy funcs ([ed78595](https://github.com/engisalor/sketch-grammar-explorer/commit/ed78595cc538e90ea338a4db4577403a305b3a74))
* Call.validate_params make format explicit ([4bd0f9c](https://github.com/engisalor/sketch-grammar-explorer/commit/4bd0f9c48ab5010e3c3402cce2f20ac5d00a4fc1))
* disable thread for ske server, refactor ([b253a59](https://github.com/engisalor/sketch-grammar-explorer/commit/b253a598e0bc231917d54aac1c83fed94213cb85))
* move CachedResponse to call, rename to_ funcs ([d9b0b22](https://github.com/engisalor/sketch-grammar-explorer/commit/d9b0b2273a8d2071e542c2807fe5d793444414e0))
* redo CachedResponse ([63c13ea](https://github.com/engisalor/sketch-grammar-explorer/commit/63c13ea570aad81fdbfec40cbff96890db3c61f5))
* remove initial 'q' from simple_query output ([b66f6d6](https://github.com/engisalor/sketch-grammar-explorer/commit/b66f6d6828e4a01fa5558c7531737876da64b8cd))
* remove xlsx as an available format ([ea79ba0](https://github.com/engisalor/sketch-grammar-explorer/commit/ea79ba03371578317aec96f6efc96f5fc1fb3810))
* rewrite api call classes ([820fb06](https://github.com/engisalor/sketch-grammar-explorer/commit/820fb0643552e0361ed7536175dfa472cbe9f2ba))
* set call_type in params, new Data dataclass ([d07e573](https://github.com/engisalor/sketch-grammar-explorer/commit/d07e573d8830829b6a0f5951e48a664fdbd4e2c9))
* upate package init, gh workflow ([47143e6](https://github.com/engisalor/sketch-grammar-explorer/commit/47143e652dd701d9034711318c7aeca048b129ad))
* update query ([453de4c](https://github.com/engisalor/sketch-grammar-explorer/commit/453de4c6ebcf98561e346c515105bbc6a65c949d))
* update repr strings ([954d170](https://github.com/engisalor/sketch-grammar-explorer/commit/954d170b78ecfd4ac1ee6cc1c90167f5bc18e8bf))
* various improvements to job module ([5ebbaba](https://github.com/engisalor/sketch-grammar-explorer/commit/5ebbaba7924942a332c4f7868321860e7dcc21c0))
* various job improvements ([606b82c](https://github.com/engisalor/sketch-grammar-explorer/commit/606b82c62ac8893c647be66f5ccef2d9fa0b6e79))


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
