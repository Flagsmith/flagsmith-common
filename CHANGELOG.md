# Changelog

<a name="v1.5.2"></a>

## [2.2.4](https://github.com/Flagsmith/flagsmith-common/compare/v2.2.3...v2.2.4) (2025-11-03)


### Bug Fixes

* `common.core.utils.TemporaryDirectory` dependent on Django settings ([#113](https://github.com/Flagsmith/flagsmith-common/issues/113)) ([7a4b1cb](https://github.com/Flagsmith/flagsmith-common/commit/7a4b1cb2830a2407341a721d75058dfa72eb19f4))

## [2.2.3](https://github.com/Flagsmith/flagsmith-common/compare/v2.2.2...v2.2.3) (2025-11-03)


### CI

* pre-commit autoupdate ([#108](https://github.com/Flagsmith/flagsmith-common/issues/108)) ([a2ce926](https://github.com/Flagsmith/flagsmith-common/commit/a2ce926df24968cab57e81e39e77838575f7f17f))


### Bug Fixes

* reduce sleep time in timeout tests and add elapsed time checks ([#111](https://github.com/Flagsmith/flagsmith-common/issues/111)) ([630e02f](https://github.com/Flagsmith/flagsmith-common/commit/630e02f0483fa629648beb9402cacde8a5188fa2))
* Temporary directories are not removed ([#109](https://github.com/Flagsmith/flagsmith-common/issues/109)) ([5e2f66f](https://github.com/Flagsmith/flagsmith-common/commit/5e2f66ff9c4ea4f8dda19a98444d3644396dbcf5))

## [2.2.2](https://github.com/Flagsmith/flagsmith-common/compare/v2.2.1...v2.2.2) (2025-10-24)


### Bug Fixes

* **tests/timeout:** increase sleep duration ([#106](https://github.com/Flagsmith/flagsmith-common/issues/106)) ([92271df](https://github.com/Flagsmith/flagsmith-common/commit/92271df94e5cd5e86534a8f0dd61f4252e42c590))
* worker thread getting stuck ([#105](https://github.com/Flagsmith/flagsmith-common/issues/105)) ([c0b8dde](https://github.com/Flagsmith/flagsmith-common/commit/c0b8ddeb1419de5d35d717784750070d78a218fa))

## [2.2.1](https://github.com/Flagsmith/flagsmith-common/compare/v2.2.0...v2.2.1) (2025-10-23)


### CI

* pre-commit autoupdate ([#101](https://github.com/Flagsmith/flagsmith-common/issues/101)) ([2703109](https://github.com/Flagsmith/flagsmith-common/commit/2703109ef70bd02f732ca368c0b8eabda37ce546))
* pre-commit autoupdate ([#103](https://github.com/Flagsmith/flagsmith-common/issues/103)) ([232f385](https://github.com/Flagsmith/flagsmith-common/commit/232f385eeb87d0befca012851b6f1e57a079ea0a))

## [2.2.0](https://github.com/Flagsmith/flagsmith-common/compare/v2.1.0...v2.2.0) (2025-09-04)


### CI

* pre-commit autoupdate ([#97](https://github.com/Flagsmith/flagsmith-common/issues/97)) ([a21d125](https://github.com/Flagsmith/flagsmith-common/commit/a21d125e2afade0b3b99cabe6e88a2f258acce10))


### Features

* **utils:** New is_database_replica_setup utility ([#100](https://github.com/Flagsmith/flagsmith-common/issues/100)) ([1c6c522](https://github.com/Flagsmith/flagsmith-common/commit/1c6c5222798ec5866b0d55b9bde1379b2cda8b3f))

## [2.1.0](https://github.com/Flagsmith/flagsmith-common/compare/v2.0.0...v2.1.0) (2025-09-02)


### CI

* pre-commit autoupdate ([#92](https://github.com/Flagsmith/flagsmith-common/issues/92)) ([aeb7520](https://github.com/Flagsmith/flagsmith-common/commit/aeb752000b8c7dbae9b2337bb0e7ee18aa3af6df))


### Features

* **utils:** Allow for explicit use of database replicas ([#95](https://github.com/Flagsmith/flagsmith-common/issues/95)) ([617861b](https://github.com/Flagsmith/flagsmith-common/commit/617861b5cdd1ef9c329463182bddc2d2746a1060))

## [2.0.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.15.1...v2.0.0) (2025-08-07)


### ⚠ BREAKING CHANGES

* Move segment and metadata serializers back to core ([#93](https://github.com/Flagsmith/flagsmith-common/issues/93))

### Refactoring

* Move segment and metadata serializers back to core ([#93](https://github.com/Flagsmith/flagsmith-common/issues/93)) ([a6b997b](https://github.com/Flagsmith/flagsmith-common/commit/a6b997b85b2b5987520bd5ceb8a082f169eb1955))

## [1.15.1](https://github.com/Flagsmith/flagsmith-common/compare/v1.15.0...v1.15.1) (2025-07-29)


### CI

* pre-commit autoupdate ([#87](https://github.com/Flagsmith/flagsmith-common/issues/87)) ([d696487](https://github.com/Flagsmith/flagsmith-common/commit/d696487c57803f19651095d5ad60da6c5848e808))

## [1.15.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.14.0...v1.15.0) (2025-06-12)


### CI

* pre-commit autoupdate ([#82](https://github.com/Flagsmith/flagsmith-common/issues/82)) ([abec78b](https://github.com/Flagsmith/flagsmith-common/commit/abec78bac928faab977faeb82e3bf3761435a062))
* pre-commit autoupdate ([#86](https://github.com/Flagsmith/flagsmith-common/issues/86)) ([b4d45d9](https://github.com/Flagsmith/flagsmith-common/commit/b4d45d98e57a2f62cb497cde7f128443738ea406))


### Features

* **test-tools:** Add `run_tasks` fixture ([#85](https://github.com/Flagsmith/flagsmith-common/issues/85)) ([9bd0855](https://github.com/Flagsmith/flagsmith-common/commit/9bd0855b88bc7680a24243664d8e10352644e892))

## [1.14.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.13.0...v1.14.0) (2025-05-30)


### CI

* pre-commit autoupdate ([#76](https://github.com/Flagsmith/flagsmith-common/issues/76)) ([2ac3408](https://github.com/Flagsmith/flagsmith-common/commit/2ac3408eb772fddd6dc06a6750829085121733e4))


### Docs

* **test-tools:** Clarify installation instructions ([#80](https://github.com/Flagsmith/flagsmith-common/issues/80)) ([b6a250b](https://github.com/Flagsmith/flagsmith-common/commit/b6a250bd49aba0fc7750a389bcf59f2bdeebce27))


### Features

* Support task backoff ([#81](https://github.com/Flagsmith/flagsmith-common/issues/81)) ([a736a68](https://github.com/Flagsmith/flagsmith-common/commit/a736a68cfb8d4cfa9e87601aabe937fbae651b01))

## [1.13.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.12.1...v1.13.0) (2025-05-19)


### CI

* Add test coverage ([#73](https://github.com/Flagsmith/flagsmith-common/issues/73)) ([1cac2c9](https://github.com/Flagsmith/flagsmith-common/commit/1cac2c951b3bb57f44251d729d8090114d217758))
* pre-commit autoupdate ([#69](https://github.com/Flagsmith/flagsmith-common/issues/69)) ([df9f9ee](https://github.com/Flagsmith/flagsmith-common/commit/df9f9ee90e949f99ddc28ada10d7d20e278dd9a3))


### Features

* Separate task processor database ([#68](https://github.com/Flagsmith/flagsmith-common/issues/68)) ([fd2373e](https://github.com/Flagsmith/flagsmith-common/commit/fd2373e2043d1131ac5854fb018547784211126a))

## [1.12.1](https://github.com/Flagsmith/flagsmith-common/compare/v1.12.0...v1.12.1) (2025-05-06)


### Bug Fixes

* metadata-incorrectly-linked-to-entity ([#57](https://github.com/Flagsmith/flagsmith-common/issues/57)) ([707496d](https://github.com/Flagsmith/flagsmith-common/commit/707496da2e3599a8067c2637d8c10566a64d800d))

## [1.12.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.11.0...v1.12.0) (2025-04-30)


### CI

* pre-commit autoupdate ([#66](https://github.com/Flagsmith/flagsmith-common/issues/66)) ([9c38998](https://github.com/Flagsmith/flagsmith-common/commit/9c38998f405ce59bf67b3db7790ec83a0a9abdd9))


### Features

* Generate metrics documentation ([#65](https://github.com/Flagsmith/flagsmith-common/issues/65)) ([c9c4935](https://github.com/Flagsmith/flagsmith-common/commit/c9c4935afd12f24665779c0a0a7b98f3e9da7dc3))
* **test-tools:** Add `snapshot` fixture for snapshot testing ([c9c4935](https://github.com/Flagsmith/flagsmith-common/commit/c9c4935afd12f24665779c0a0a7b98f3e9da7dc3))


### Bug Fixes

* **tests:** `clear_lru_caches` fixture conflicts with `saas_mode`/`enterprise_mode` pytest markers ([c9c4935](https://github.com/Flagsmith/flagsmith-common/commit/c9c4935afd12f24665779c0a0a7b98f3e9da7dc3))

## [1.11.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.10.0...v1.11.0) (2025-04-25)


### CI

* pre-commit autoupdate ([#54](https://github.com/Flagsmith/flagsmith-common/issues/54)) ([49268aa](https://github.com/Flagsmith/flagsmith-common/commit/49268aaf600cba1411ca6000f8936e3afb11d743))


### Features

* Add `flagsmith healthcheck` command ([#60](https://github.com/Flagsmith/flagsmith-common/issues/60)) ([1eb58f3](https://github.com/Flagsmith/flagsmith-common/commit/1eb58f3bd07b19fb6875fbd82a547eca1f24ea1a))
* Deliver the deployed API version to an HTTP response header ([#59](https://github.com/Flagsmith/flagsmith-common/issues/59)) ([64037d3](https://github.com/Flagsmith/flagsmith-common/commit/64037d31ae59af26449e17f6fb36a0f3bcb3e26a))


### Bug Fixes

* **tests:** Inaccurate`freeze_time` for a certain timestamp ([#63](https://github.com/Flagsmith/flagsmith-common/issues/63)) ([74c73b4](https://github.com/Flagsmith/flagsmith-common/commit/74c73b49b908897308dedf2f05400ba7dd65111b))

## [1.10.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.9.0...v1.10.0) (2025-04-22)


### Features

* Ability to log WSGI `environ` in JSON logs, `log_extra` utility ([#55](https://github.com/Flagsmith/flagsmith-common/issues/55)) ([bf48843](https://github.com/Flagsmith/flagsmith-common/commit/bf48843c86214f4b57eeed956ca700e520ab7bba))

## [1.9.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.8.0...v1.9.0) (2025-04-16)


### CI

* pre-commit autoupdate ([#46](https://github.com/Flagsmith/flagsmith-common/issues/46)) ([1d35c43](https://github.com/Flagsmith/flagsmith-common/commit/1d35c43870028885373b5ffcbcd07c41c8a94b29))
* pre-commit autoupdate ([#52](https://github.com/Flagsmith/flagsmith-common/issues/52)) ([e852305](https://github.com/Flagsmith/flagsmith-common/commit/e8523054870215def2489eb7e415116991f00387))


### Features

* Add `flagsmith_http_server_response_size_bytes` metric ([#49](https://github.com/Flagsmith/flagsmith-common/issues/49)) ([8e2b042](https://github.com/Flagsmith/flagsmith-common/commit/8e2b042450f8006d894669a5b5d712df35ca1e8d))
* **task-processor:** Add `task_type` label to task processor metrics ([#51](https://github.com/Flagsmith/flagsmith-common/issues/51)) ([42f7365](https://github.com/Flagsmith/flagsmith-common/commit/42f73657694289865dcf5e2ff25082cbd3ac571d))
* **test-tools:** SaaS/Enterprise mode markers, update documentation ([#53](https://github.com/Flagsmith/flagsmith-common/issues/53)) ([9f23a7d](https://github.com/Flagsmith/flagsmith-common/commit/9f23a7d5d6e93a490d80f6390d9952232436be96))

## [1.8.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.7.1...v1.8.0) (2025-04-07)


### Features

* **utils/is_oss:** Add a function to check oss deployment mode ([#44](https://github.com/Flagsmith/flagsmith-common/issues/44)) ([13c2016](https://github.com/Flagsmith/flagsmith-common/commit/13c2016f5b384818e9e796dea226d045d8769094))


### Bug Fixes

* Trailing slash in default routes, add tests for default routes ([#43](https://github.com/Flagsmith/flagsmith-common/issues/43)) ([29b3256](https://github.com/Flagsmith/flagsmith-common/commit/29b32565b676b9210bcb2608b9e51bfaa28d5883))

## [1.7.1](https://github.com/Flagsmith/flagsmith-common/compare/v1.7.0...v1.7.1) (2025-04-04)


### Bug Fixes

* Regex url paths used as simple url path values ([#41](https://github.com/Flagsmith/flagsmith-common/issues/41)) ([ef1842e](https://github.com/Flagsmith/flagsmith-common/commit/ef1842e6a70d8388d6588e4f1fe290e186719f04))

## [1.7.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.6.0...v1.7.0) (2025-04-04)


### Features

* Add common namespace for metrics ([#40](https://github.com/Flagsmith/flagsmith-common/issues/40)) ([7588379](https://github.com/Flagsmith/flagsmith-common/commit/7588379b19e13ff2173bb34221389cb809ac6513))
* Add Task Processor metrics ([#27](https://github.com/Flagsmith/flagsmith-common/issues/27)) ([d0ea561](https://github.com/Flagsmith/flagsmith-common/commit/d0ea5619b6e711bccd023655dd2858dfdf33aeef))


### Bug Fixes

* `PROMETHEUS_MULTIPROC_DIR` deleted prematurely ([#38](https://github.com/Flagsmith/flagsmith-common/issues/38)) ([ca396df](https://github.com/Flagsmith/flagsmith-common/commit/ca396df49a2b872f0dceca1bde08696f9d45fe43))
* Unnecessary regex path definitions for `/metrics`, `/version`, healthcheck routes ([#36](https://github.com/Flagsmith/flagsmith-common/issues/36)) ([5550108](https://github.com/Flagsmith/flagsmith-common/commit/55501086ca061ee25c3c4e945d86abf6afd94dc0))

## [1.6.0](https://github.com/Flagsmith/flagsmith-common/compare/v1.5.2...v1.6.0) (2025-04-03)


### CI

* Add release-please, publish to PyPI ([#20](https://github.com/Flagsmith/flagsmith-common/issues/20)) ([6fdfe69](https://github.com/Flagsmith/flagsmith-common/commit/6fdfe698e52b814e9c38531af66b3b21656f3152))
* Hide `chore` commits from release-please ([#25](https://github.com/Flagsmith/flagsmith-common/issues/25)) ([328d1b3](https://github.com/Flagsmith/flagsmith-common/commit/328d1b397c79b8a74ca7d83849f8a63655ff14e9))
* pre-commit autoupdate ([#34](https://github.com/Flagsmith/flagsmith-common/issues/34)) ([07920e4](https://github.com/Flagsmith/flagsmith-common/commit/07920e49411ef637c388045fb5f62f86df8c9ba5))


### Docs

* Correct metric tags in README.md ([#21](https://github.com/Flagsmith/flagsmith-common/issues/21)) ([e5050d5](https://github.com/Flagsmith/flagsmith-common/commit/e5050d55950e12cd833635893790a0c8ff1fb457))


### Features

* Add Task processor ([#26](https://github.com/Flagsmith/flagsmith-common/issues/26)) ([9e224f1](https://github.com/Flagsmith/flagsmith-common/commit/9e224f121ffbb32d332f648d31b9089cacfce6c7))
* Provide documented routes as labels ([#33](https://github.com/Flagsmith/flagsmith-common/issues/33)) ([3adfffa](https://github.com/Flagsmith/flagsmith-common/commit/3adfffae866966f2a58c600e66911a3f4446e3ad))


### Bug Fixes

* `psycopg2` dependency causes building from source ([#30](https://github.com/Flagsmith/flagsmith-common/issues/30)) ([63a80ac](https://github.com/Flagsmith/flagsmith-common/commit/63a80ac8470104452e40b8b5b0eaf8849c0e2471))
* **ci:** `poetry-lock` pre-commit hook is failing in CI ([#23](https://github.com/Flagsmith/flagsmith-common/issues/23)) ([fe86fb4](https://github.com/Flagsmith/flagsmith-common/commit/fe86fb440e4afb52566db1639208171472ca3408))
* **ci:** Missing release-please manifest ([#22](https://github.com/Flagsmith/flagsmith-common/issues/22)) ([85aca5a](https://github.com/Flagsmith/flagsmith-common/commit/85aca5ad56b641886cf7aa8663ac82e2c63ac569))
* **docs:** `http_server` metrics not correctly documented in README ([#32](https://github.com/Flagsmith/flagsmith-common/issues/32)) ([16169f8](https://github.com/Flagsmith/flagsmith-common/commit/16169f83a730ff0ece8dc8663b1cccec9de8a0b1))
* **get_recurringtasks_to_process:** Add last_picked_at ([#37](https://github.com/Flagsmith/flagsmith-common/issues/37)) ([7ac2e3b](https://github.com/Flagsmith/flagsmith-common/commit/7ac2e3b36440e5f63da8bb8420dd115717ef278a))
* **test-tools:** Registry state is not properly cleared between tests ([5ad6414](https://github.com/Flagsmith/flagsmith-common/commit/5ad64147b5ccb65df0a7db7d030c5b00e1ccb47f))

## [v1.5.2](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.5.2) - 25 Mar 2025

### What's Changed

- fix: Liveness probe performs database queries by [@khvn26](https://github.com/khvn26) in https://github.com/Flagsmith/flagsmith-common/pull/19

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.5.1...v1.5.2

[Changes][v1.5.2]

<a name="v1.5.1"></a>

## [v1.5.1](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.5.1) - 25 Mar 2025

### What's Changed

- fix: Rule is asserted in `SegmentSerializer` when `segment` is not `None` by [@khvn26](https://github.com/khvn26) in https://github.com/Flagsmith/flagsmith-common/pull/18

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.5.0...v1.5.1

[Changes][v1.5.1]

<a name="v1.5.0"></a>

## [v1.5.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.5.0) - 25 Mar 2025

### What's Changed

- feat: Add `version_of` to rules and conditions serializers by [@zachaysan](https://github.com/zachaysan) in https://github.com/Flagsmith/flagsmith-common/pull/11
- feat: Add healthcheck views + urls, typing, ruff linting, src layout by [@khvn26](https://github.com/khvn26) in https://github.com/Flagsmith/flagsmith-common/pull/13
- feat: Prometheus support, core entrypoint, packaging improvements by [@khvn26](https://github.com/khvn26) and [@rolodato](https://github.com/rolodato) in https://github.com/Flagsmith/flagsmith-common/pull/17
- feat: Add `MANAGE_SEGMENT_OVERRIDES` permission by [@francescolofranco](https://github.com/francescolofranco) in https://github.com/Flagsmith/flagsmith-common/pull/14
- feat: Add Makefile for development setup and installation instructions by [@francescolofranco](https://github.com/francescolofranco) in https://github.com/Flagsmith/flagsmith-common/pull/15
- fix: Clarify change request wording by [@zachaysan](https://github.com/zachaysan) in https://github.com/Flagsmith/flagsmith-common/pull/10
- fix: Handle missing condition by [@zachaysan](https://github.com/zachaysan) in https://github.com/Flagsmith/flagsmith-common/pull/12
- fix: `self_hosted_data` is cached indefinitely by [@khvn26](https://github.com/khvn26) in https://github.com/Flagsmith/flagsmith-common/pull/16

### New Contributors

- [@francescolofranco](https://github.com/francescolofranco) made their first contribution in https://github.com/Flagsmith/flagsmith-common/pull/15
- [@rolodato](https://github.com/rolodato) made their first contribution in https://github.com/Flagsmith/flagsmith-common/pull/17

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.2...v1.5.0

[Changes][v1.5.0]

<a name="v1.4.2"></a>

## [v1.4.2](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.4.2) - 04 Dec 2024

### What's Changed

- fix: segment limit validation versioning by [@matthewelwell](https://github.com/matthewelwell) in https://github.com/Flagsmith/flagsmith-common/pull/9

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.1...v1.4.2

[Changes][v1.4.2]

<a name="v1.4.1"></a>

## [v1.4.1](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.4.1) - 04 Dec 2024

### What's Changed

- fix: segment limit validation versioning by [@matthewelwell](https://github.com/matthewelwell) in https://github.com/Flagsmith/flagsmith-common/pull/8

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.0...v1.4.1

[Changes][v1.4.1]

<a name="v1.4.0"></a>

## [v1.4.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.4.0) - 04 Dec 2024

### What's Changed

- feat(org/permissions): Add org permission constants by [@gagantrivedi](https://github.com/gagantrivedi) in https://github.com/Flagsmith/flagsmith-common/pull/7

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.3.0...v1.4.0

[Changes][v1.4.0]

<a name="v1.3.0"></a>

## [v1.3.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.3.0) - 03 Dec 2024

### What's Changed

- fix: Ensure owning segment matches to parent segment from rule or condition by [@zachaysan](https://github.com/zachaysan) in https://github.com/Flagsmith/flagsmith-common/pull/5

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.2.0...v1.3.0

[Changes][v1.3.0]

<a name="v1.2.0"></a>

## [v1.2.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.2.0) - 05 Nov 2024

### What's Changed

- feat(env/perms): add cr related perms to tag_supported_permissions by [@gagantrivedi](https://github.com/gagantrivedi) in https://github.com/Flagsmith/flagsmith-common/pull/6

### New Contributors

- [@gagantrivedi](https://github.com/gagantrivedi) made their first contribution in https://github.com/Flagsmith/flagsmith-common/pull/6

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.1.0...v1.2.0

[Changes][v1.2.0]

<a name="v1.1.0"></a>

## [v1.1.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.1.0) - 23 Oct 2024

### What's Changed

- chore: add configuration files by [@matthewelwell](https://github.com/matthewelwell) in https://github.com/Flagsmith/flagsmith-common/pull/2
- deps: lock to django 4 by [@matthewelwell](https://github.com/matthewelwell) in https://github.com/Flagsmith/flagsmith-common/pull/3
- feat: Add workflows change request concerns by [@zachaysan](https://github.com/zachaysan) in https://github.com/Flagsmith/flagsmith-common/pull/4

### New Contributors

- [@zachaysan](https://github.com/zachaysan) made their first contribution in https://github.com/Flagsmith/flagsmith-common/pull/4

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/compare/v1.0.0...v1.1.0

[Changes][v1.1.0]

<a name="v1.0.0"></a>

## [v1.0.0](https://github.com/Flagsmith/flagsmith-common/releases/tag/v1.0.0) - 18 Jul 2024

### What's Changed

- feat: add serializers for versioning change requests by [@matthewelwell](https://github.com/matthewelwell) in https://github.com/Flagsmith/flagsmith-common/pull/1

### New Contributors

- [@matthewelwell](https://github.com/matthewelwell) made their first contribution in https://github.com/Flagsmith/flagsmith-common/pull/1

**Full Changelog**: https://github.com/Flagsmith/flagsmith-common/commits/v1.0.0

[Changes][v1.0.0]

[v1.5.2]: https://github.com/Flagsmith/flagsmith-common/compare/v1.5.1...v1.5.2
[v1.5.1]: https://github.com/Flagsmith/flagsmith-common/compare/v1.5.0...v1.5.1
[v1.5.0]: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.2...v1.5.0
[v1.4.2]: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.1...v1.4.2
[v1.4.1]: https://github.com/Flagsmith/flagsmith-common/compare/v1.4.0...v1.4.1
[v1.4.0]: https://github.com/Flagsmith/flagsmith-common/compare/v1.3.0...v1.4.0
[v1.3.0]: https://github.com/Flagsmith/flagsmith-common/compare/v1.2.0...v1.3.0
[v1.2.0]: https://github.com/Flagsmith/flagsmith-common/compare/v1.1.0...v1.2.0
[v1.1.0]: https://github.com/Flagsmith/flagsmith-common/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/Flagsmith/flagsmith-common/tree/v1.0.0

<!-- Generated by https://github.com/rhysd/changelog-from-release v3.7.2 -->
