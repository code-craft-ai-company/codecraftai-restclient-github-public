# Design

## Overview

`GithubPublicRestClient` is a `GithubRestClientBase` subclass — itself a
`RestClientBase` subclass — that talks to the public GitHub REST API. Its
distinguishing property is that almost none of it is written by hand: the
client module, all 41 API-group modules, and the 500+ schema modules are
emitted by `GithubRestClientGenerator` from GitHub's OpenAPI description.

Two modules are hand-maintained:

- `githubrestclientbase.py` — GitHub authentication (token and basic).
- `generation/githubrestclientgenerator.py` — generator configuration and the
  `rest_client_generator_main()` entry point.

Everything else is disposable output. Fixing a generated module means fixing
the generator in `codecraftai-restclient-base` or adding a hint under
`generation/specs/`, then regenerating.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  generation/specs/api-public.json  (GitHub OpenAPI, ~16MB)│
│  generation/specs/api-hints.json   (method-name overrides)│
└─────────────────────────┬────────────────────────────────┘
                          │  GithubRestClientGenerator
                          ▼
┌──────────────────────────────────────────────────────────┐
│  githubpublicrestclient.py   groups/*.py   schemas/*.py   │
│  (generated — DO NOT EDIT)                                │
└─────────────────────────┬────────────────────────────────┘
                          │ extends
                          ▼
┌────────────────────────────┐      ┌─────────────────────┐
│  GithubRestClientBase      │─────▶│ codecraftai-        │
│  (hand-written auth)       │      │   credentials       │
└──────────┬─────────────────┘      └─────────────────────┘
           │ extends
           ▼
┌────────────────────────────┐
│  RestClientBase            │  perform_call / aspects /
│  (codecraftai-restclient-  │  session reuse / error raise
│   base)                    │
└──────────┬─────────────────┘
           │ HTTPS, header auth
           ▼
      api.github.com
```

---

## Generation Scheme

The generator is driven entirely by the OpenAPI document; the subclass in this
repo only supplies module roots and the base class.

**Grouping.** Each operation's first `tags` entry becomes its group. The group
module file is the tag snake-cased with underscores stripped
(`code_scanning` → `codescanning.py`); the class is the tag pascal-cased with
an `ApiGroup` suffix (`CodeScanningApiGroup`); the client property is the
snake-cased tag (`client.code_scanning`).

**Method naming.** GitHub `operationId` values are `tag/method` pairs, so the
generator splits on `/` and keeps the right-hand side. Where the resulting name
is unhelpful, `generation/specs/api-hints.json` supplies a `method-name`
override keyed by path and HTTP method — currently 34 overrides, every one of
them renaming a `get` operation into a `list_*` name (`/emojis` →
`list_emojis`).

**Schema placement.** Schemas are distributed across `schemas/` by usage rather
than alphabetically: a schema referenced by exactly one tag lands in that tag's
module; a schema shared across tags lands in the module of the tag that owns
its first creating (POST/PUT/PATCH) operation; anything still ambiguous gets
its own module named after the lower-cased class name. This is why
`schemas/gists.py` holds `BaseGist`, `GistComment`, `GistCommit`, and
`GistSimple` together, while widely-shared types such as `Actor` and `Commit`
sit in modules of their own.

**Return typing.** `_determine_return_type` inspects the 200 response schema.
A list response with `page`/`per_page` query parameters becomes
`PagedList[Item]`; a list without them becomes `List[Item]`; a single object
becomes its `SchemaObject` type; anything unresolvable becomes `Any`.

**Scale.** The current generation produces 41 group modules holding 1,063
methods — 187 returning `PagedList`, 63 returning `List` — plus 524 schema
modules holding 754 `SchemaObject` classes. Group sizes are extremely uneven:
`repos.py` (201 methods) and `actions.py` (166) together are roughly a third of
the surface, while `emojis.py`, `ratelimit.py`, and `credentials.py` hold a
single method each.

---

## Generated Method Shape

Every generated method has the same skeleton, which is the contract worth
knowing rather than the individual signatures:

1. Resolve `aspects`, falling back to `client.aspects` when `None`.
2. Resolve headers — a supplied `headers` argument *replaces* `client.headers`.
3. Compose `call_leaf`, either as a literal or by `str.format` over a
   `leaf_template` and a `path_params` dict.
4. Build `query_params`, skipping any parameter left at `None`.
5. Default `exp_status` to the operation's 2xx codes from the spec.
6. Call `client.perform_call(...)`.
7. Parse: `None` for 204/205 and empty-bodied 202; `SchemaObject.from_dict` for
   a single object; a list comprehension over `_parse_item` wrapped in
   `PagedList` for a paged collection.

Authentication, retry strategy, session reuse, and HTTP error classification
are not in the generated code at all — they belong to `RestClientBase`.
`_parse_item` degrades to the raw dictionary when a payload does not fit its
declared schema, so a spec drift shows up as a dict rather than an exception.

---

## Module Layout

```
source/packages/ccai/restclient/github/public/
├── __init__.py
├── githubrestclientbase.py          # hand-written: auth
├── githubpublicrestclient.py        # generated: 41 group properties
├── py.typed
├── generation/
│   ├── githubrestclientgenerator.py # hand-written: generator config
│   └── specs/
│       ├── api-public.json          # GitHub OpenAPI description
│       ├── api-hints.json           # method-name overrides
│       └── pagination-hints.json    # (see tasks.md — not currently loaded)
├── groups/                          # generated: 41 modules
└── schemas/                         # generated: 524 modules
```

---

## See Also

- `codecraftai-restclient-base/specs/restapigroup-enhancements/` — the
  `RestApiGroup` shape and paging helpers this client builds on.
- `codecraftai-restclient-pychestrate/specs/pychestrate-client/` — the sibling
  generated client, same generator, different spec and module layout.
- `codecraftai-credentials` — `GithubTokenCredential` and `BasicCredential`.

---

## Testing Strategy

`source/testroots/testbase/` exists but is unpopulated — there are no tests in
this repo today. That is recorded as an open item in `tasks.md` rather than
described here as if it were built.

The testing shape this package needs is structural rather than behavioural,
because the code under test is generated: assert that the client exposes the
expected group properties and types, that a representative schema's `required`
fields match the OpenAPI document, and that method signatures round-trip
path/query parameters correctly against a mock transport. The sibling
`codecraftai-restclient-pychestrate` smoke test
(`source/testroots/testbase/tests/test_p20a_client_smoke.py`) is a working
model of exactly this approach and can be adapted directly.
