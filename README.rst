==================================================
Automation Mojo RestClient GitHub (Public)
==================================================

The ``automojo-restclient-github-public`` package is the GitHub public-API REST client for the automojo suite. It is built on top of ``automojo-restclient-base`` and provides a typed, schema-driven client with coverage for the public surface of the GitHub REST API — including actions, apps, billing, code scanning, codespaces, copilot, dependabot, issues, and the rest of the well-known endpoint families.

Highlights
==========

- ``GithubRestClientBase`` as the top-level client for GitHub's public API.
- Generated schema catalogue under ``public/schemas/`` modelling each GitHub resource with ``SchemaObject``/``SchemaField`` bindings.
- Endpoint groupings under ``public/groups/`` covering actions, apps, billing, code scanning, codespaces, copilot, dependabot, issues, and more.
- ``GithubRestClientGenerator`` under ``public/generation/`` to regenerate schema and group modules from the GitHub OpenAPI spec.
- Token and app authentication via ``automojo-credentials``.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/testroots/testbase/`` - TestBase test roots.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run TestBase tests (when test roots are populated):

.. code-block:: bash

   testbase testing run --root source/testroots/testbase --includes=automojo --output=./.output

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
