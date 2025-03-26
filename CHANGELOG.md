# Changelog

<a name="v1.5.2"></a>

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
