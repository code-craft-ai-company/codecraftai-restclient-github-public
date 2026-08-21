# Implementation Plan — GitHub Public Client

## Package Skeleton

- [x] 1. Create `source/packages/ccai/restclient/github/public/` with `generation/`, `groups/`, and `schemas/` subpackages.
- [x] 2. Add `py.typed` so downstream consumers get the generated annotations.
- [x] 3. Declare `codecraftai-errors`, `codecraftai-credentials`, and `codecraftai-restclient-base` as git dependencies in `pyproject.toml`.

## Authentication (hand-written)

- [x] 4. Implement `GithubRestClientBase(RestClientBase)` defaulting the `Accept` header to `application/vnd.github.v3+json`.
- [x] 5. Implement `authenticate()` building a `requests.Session` from credential-derived headers, with no login round trip.
- [x] 6. Implement `_build_auth_headers` dispatch: `BasicCredential` → Basic, `GithubTokenCredential` → Bearer.
- [x] 7. Implement `_get_token_value` fallback across `token` and `access_token` attributes, then `username`/`password`, then `RuntimeError`.

## Generation (hand-written)

- [x] 8. Implement `GithubRestClientGenerator(RestClientGenerator)` binding `REST_CLIENT_BASE_CLASS` and the three module roots.
- [x] 9. Implement `rest_client_generator_main()` resolving `generation/specs/api-public.json` and writing into the package root.
- [x] 10. Vendor GitHub's OpenAPI description as `generation/specs/api-public.json`.
- [x] 11. Author `generation/specs/api-hints.json` with 34 `method-name` overrides turning bare `get` operations into `list_*` names.

## Generated Output

- [x] 12. Generate `githubpublicrestclient.py` exposing 41 API groups as read-only properties.
- [x] 13. Generate 41 group modules under `groups/`, one per OpenAPI tag.
- [x] 14. Generate 524 schema modules under `schemas/` holding 754 `SchemaObject` classes.
- [x] 15. Generate `PagedList[T]` returns for the 187 operations carrying `page`/`per_page` parameters.
- [x] 16. Generate `List[T]` returns for the 63 unpaged list operations.
- [x] 17. Generate empty-body handling (204/205, and 202 with a zero-length body) on status-only operations.

## Open Items

- [ ] 18. **No tests exist.** `source/testroots/testbase/` contains only `__testroot__.py`; there is no `tests/` directory and no runnable suite. Add structural smoke tests modelled on `codecraftai-restclient-pychestrate/source/testroots/testbase/tests/test_p20a_client_smoke.py`: client-exposes-expected-groups, schema `required` fields match the OpenAPI document, and path/query composition against a mock transport.
- [ ] 19. **No `make generate` target.** The `Makefile` carries only `dist-clean`, `dist-build`, and `dist-publish`; regeneration requires invoking the generator module directly. The sibling pychestrate repo has a `generate` target — mirror it here.
- [ ] 20. **`generation/specs/pagination-hints.json` is never read.** `RestClientGenerator.__init__` assigns `self._pagination_hints = self.DEFAULT_PAGINATION_DETECTION_HINTS` with no file load, so the vendored hints file — including its `link_header` detection rule and `non_paginated` / `custom_pagination` exception lists — has no effect on generation. Either wire it up in the base generator or delete the file.
- [ ] 21. **`GithubAppCredential` is not supported.** `README.rst` advertises "token and app authentication", but `GithubAppCredential` exposes `keyfiles`/`keys`/`keypasswd` and no `token`, `access_token`, `username`, or `password`, so `_build_auth_headers` raises `RuntimeError` for it. Either implement the JWT-assertion → installation-token exchange or correct the README claim.
- [ ] 22. **README names the wrong top-level class.** `README.rst` calls `GithubRestClientBase` "the top-level client for GitHub's public API"; the top-level client is `GithubPublicRestClient`.
