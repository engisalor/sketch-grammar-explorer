# Changelog

## [0.6.0](https://github.com/engisalor/sketch-grammar-explorer/compare/v0.5.5...v0.6.0) (2023-02-28)


### ⚠ BREAKING CHANGES

* rename old call module to _call

### Features

* add _call module ([9cf3ace](https://github.com/engisalor/sketch-grammar-explorer/commit/9cf3ace42dfa51b2c963c4bbcb23d7f6cabbaa62))


### Bug Fixes

* _call use custom key_fn, add redact hook ([5f191a7](https://github.com/engisalor/sketch-grammar-explorer/commit/5f191a7b7d1d2d076fef777bd14fe809551963b0))
* add _parse dir, modules ([73d118f](https://github.com/engisalor/sketch-grammar-explorer/commit/73d118faea666f4bd5f068e29e3b29fd557b65b5))
* add assemble module ([1003e1d](https://github.com/engisalor/sketch-grammar-explorer/commit/1003e1dd8e06964fda7bde1b785d24bf426536bf))
* add call type to key hash, use p3.8 typehints ([35a7681](https://github.com/engisalor/sketch-grammar-explorer/commit/35a7681c8c1845a8494eee7f39ff5caf7ceeb518))
* add config module ([033aad7](https://github.com/engisalor/sketch-grammar-explorer/commit/033aad78483bf6da617ff9f6735e6c1c47b0e9df))
* add hook module, redact_hook ([d5b9041](https://github.com/engisalor/sketch-grammar-explorer/commit/d5b90418699ae232d859c1ad557ead790fb8842b))
* add io module ([e197c94](https://github.com/engisalor/sketch-grammar-explorer/commit/e197c94158e446ea6d97175ccc2783a7d050de7f))
* add logging to _call, timeout note ([87e8984](https://github.com/engisalor/sketch-grammar-explorer/commit/87e8984927a519455b1d51b83417b27f109148c5))
* add util module ([9bb7f23](https://github.com/engisalor/sketch-grammar-explorer/commit/9bb7f23f88afd3a807e8547a59c29faca80046a2))
* add wait module ([efd9aec](https://github.com/engisalor/sketch-grammar-explorer/commit/efd9aec098ea5dd37d40d682d05d2d7d3da9d692))
* **call:** remove tsv as an accepted format ([fb45559](https://github.com/engisalor/sketch-grammar-explorer/commit/fb455595b1afdce11bbf8fd9b5c7d094a03a9a90))
* **call:** update style, _save_xml ([6fed24d](https://github.com/engisalor/sketch-grammar-explorer/commit/6fed24de7d6f3c9659f6c2144d0898c63b8a6cd2))
* **config:** change "server" to "host" in default ([1918fcc](https://github.com/engisalor/sketch-grammar-explorer/commit/1918fcc4e66a4813582cf788cd92917e5dcb63b1))
* **config:** move keyring import ([ed3d81c](https://github.com/engisalor/sketch-grammar-explorer/commit/ed3d81c8d340df28e289408824dff733d6289c18))
* **config:** simplify config.load, read_keyring ([1a8929d](https://github.com/engisalor/sketch-grammar-explorer/commit/1a8929d3c88fa8c6b7261367a7734bd811bd65a5))
* **hook:** allow float wait intervals ([5a15fac](https://github.com/engisalor/sketch-grammar-explorer/commit/5a15fac982c92428082e2a5ef4210dd8f816219c))
* implement pre-commit, release-please ([13c9552](https://github.com/engisalor/sketch-grammar-explorer/commit/13c9552ffd0c505c0ae88cd31ae7ca2e46273a10))
* **io:** add export_content ([b0288f2](https://github.com/engisalor/sketch-grammar-explorer/commit/b0288f2378819523aabb89cbf2a5607d4f3e5bdf))
* **io:** improve extension handling ([af008b2](https://github.com/engisalor/sketch-grammar-explorer/commit/af008b2071d45629ee1c5f612e080086c9c6567b))
* job module, TTypeanalysis, SimpleFreqsQuery ([2be4576](https://github.com/engisalor/sketch-grammar-explorer/commit/2be4576df0fad34324df62cd9da04175d8950229))
* **job:** add config arg to classes ([eeaffdb](https://github.com/engisalor/sketch-grammar-explorer/commit/eeaffdb65f4f5287ee548b5726aa261cbbc7086d))
* make pandas a required import for io ([3ada768](https://github.com/engisalor/sketch-grammar-explorer/commit/3ada7680e42233aa4294b2e3d688dbe77080b838))
* move call_examples to call module ([1ecf1c3](https://github.com/engisalor/sketch-grammar-explorer/commit/1ecf1c31d31f8aaf9358a99c271ab4307cc400a3))
* move formats , ignored_parameters to config ([14d6061](https://github.com/engisalor/sketch-grammar-explorer/commit/14d6061ad6e4ea06ae499da0c2302cfb5097e737))
* move parse to call module, config syntax ([1998f6d](https://github.com/engisalor/sketch-grammar-explorer/commit/1998f6d3bec07509c865acb41fb73daa71f844d4))
* **package:** set loglevel during init ([c26e2da](https://github.com/engisalor/sketch-grammar-explorer/commit/c26e2da58210b5425f9a696e75b2aa35c7de1baa))
* **package:** update args, self.conf-&gt;self.config ([5077c75](https://github.com/engisalor/sketch-grammar-explorer/commit/5077c75305674784076a1bd37afe2794476b61c6))
* rename list_of_dict func ([f211f0f](https://github.com/engisalor/sketch-grammar-explorer/commit/f211f0f384bf85849d1df9b011fd60ab2457893b))
* rename old call module to _call ([d1d78ff](https://github.com/engisalor/sketch-grammar-explorer/commit/d1d78ff03f1381c7f986bb62b989613e7bfa6f52))
* restructure _parse dir ([b779ec4](https://github.com/engisalor/sketch-grammar-explorer/commit/b779ec4e6b8a61b3099978a599e1e1245e8c9632))
* restructure call package ([184f012](https://github.com/engisalor/sketch-grammar-explorer/commit/184f0129be4dbf61a17f3043d027d9fa9b4968a3))
* **type:** fix __repr__ ([cc6212a](https://github.com/engisalor/sketch-grammar-explorer/commit/cc6212aecb62a9e2aad2bed5296dfd2a3a25904c))
* **type:** improve Call init, child classes ([d5b43fe](https://github.com/engisalor/sketch-grammar-explorer/commit/d5b43fe6327928f3a0b4bd216a63482144358126))
* update config example, setup.cfg ([699a471](https://github.com/engisalor/sketch-grammar-explorer/commit/699a471a95f56e853e64880b679e1b8e462e8dfa))
* update config var names ([bbac641](https://github.com/engisalor/sketch-grammar-explorer/commit/bbac641848defeaa389a1610c961b7e32e5ac2b9))
* update package ([5c60bbe](https://github.com/engisalor/sketch-grammar-explorer/commit/5c60bbe48627f222884b97412e877aea5825cba0))
* update pyproject format, gitignore ([53bcd9a](https://github.com/engisalor/sketch-grammar-explorer/commit/53bcd9ae3a0927cfaecfa24dbafe34eadc46df6c))
* update semver commit _version.py ([d6d1b1f](https://github.com/engisalor/sketch-grammar-explorer/commit/d6d1b1f0e594ed4c2d80875034cb41a1ba5f8c8d))


### Documentation

* _version ([fa5b643](https://github.com/engisalor/sketch-grammar-explorer/commit/fa5b643237294764a765e47d715ffbcd167c418e))
* add readme depr notice ([8613844](https://github.com/engisalor/sketch-grammar-explorer/commit/861384458719ee2aa7d46ca49267896449d5758c))
* add setup ([d0166ff](https://github.com/engisalor/sketch-grammar-explorer/commit/d0166ff89af58595e2f06550651e704fe9d425f3))
* deprecate 0.5.5 readme ([37e8d11](https://github.com/engisalor/sketch-grammar-explorer/commit/37e8d11e5f22b6ca5f5f8c6f9abda35b2c781551))
* doi ([0817306](https://github.com/engisalor/sketch-grammar-explorer/commit/08173066bd4def2f191593ba3f02c385eb053b3f))
* **job:** add detailed docstrings ([83d1f04](https://github.com/engisalor/sketch-grammar-explorer/commit/83d1f046bc7a91fbafd5e712a7e86ee9d8416079))
* **parse:** corp_info docstrings ([a554d88](https://github.com/engisalor/sketch-grammar-explorer/commit/a554d88a4e14cf63600e0d0f1c21c8a86151b795))
* **parse:** ttype_analysis docstring ([5e79d2d](https://github.com/engisalor/sketch-grammar-explorer/commit/5e79d2d1dd845528c741b5173efbb2b177ef4133))
* release-please extra-files ([9fc9498](https://github.com/engisalor/sketch-grammar-explorer/commit/9fc94988454d1bc0889011d6ae2e1c7a6db01449))
* update ([b526f09](https://github.com/engisalor/sketch-grammar-explorer/commit/b526f096b1e39686914844f179b8dcf80e663c2d))
* update ([bc7a76f](https://github.com/engisalor/sketch-grammar-explorer/commit/bc7a76ff60ac63a10e47159f7ea9c57bf9e695a2))
* update readme ([dc13116](https://github.com/engisalor/sketch-grammar-explorer/commit/dc131163b00e82eca974bc8d45464949525a8429))
* update readme ([9f61373](https://github.com/engisalor/sketch-grammar-explorer/commit/9f613738366a20f1347611b938a7fa64258397ff))
* update requirements ([7f20582](https://github.com/engisalor/sketch-grammar-explorer/commit/7f2058229a68524b88601bff1af7d71c2a041721))
