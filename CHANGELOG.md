# Changelog

<a name="v1.5.2"></a>

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
