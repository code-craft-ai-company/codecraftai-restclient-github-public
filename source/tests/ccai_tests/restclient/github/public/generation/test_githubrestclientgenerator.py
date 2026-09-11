"""
    Generator drift tests: the checked-in client tree must be exactly what
    :class:`GithubRestClientGenerator` produces from the committed OpenAPI
    description, so a hand edit to a generated file, or a change in the
    generator's output, fails here by file name.
"""

import os
import tempfile
import unittest

from typing import Dict, List

from ccai.errors.exceptions import SkipError

from ccai.restclient.github.public.generation import githubrestclientgenerator as generation_module
from ccai.restclient.github.public.generation.githubrestclientgenerator import GithubRestClientGenerator


GENERATION_DIR = os.path.dirname(os.path.abspath(generation_module.__file__))
PACKAGE_DIR = os.path.dirname(GENERATION_DIR)
SPEC_FILE = os.path.join(GENERATION_DIR, "specs", "api-public.json")

CLIENT_CLASS_NAME = "GithubPublicRestClient"
CLIENT_MODULE_FILE = "githubpublicrestclient.py"
GENERATED_SUBDIRS = ("groups", "schemas")


def _require_spec_file() -> str:
    """
        Returns the committed OpenAPI description path, raising
        :class:`SkipError` when it is absent so the run records a skip
        rather than an error.
    """
    if not os.path.isfile(SPEC_FILE):
        raise SkipError("The OpenAPI description {} is not present; the drift test cannot regenerate.".format(SPEC_FILE))
    return SPEC_FILE


def _generate_into(target_dir: str) -> None:
    """
        Runs the generator with the same arguments as its
        ``rest_client_generator_main`` entry point, into ``target_dir``.
    """
    generator = GithubRestClientGenerator(
        openapi_spec_file=_require_spec_file(),
        clients_root=target_dir,
        client_class_name=CLIENT_CLASS_NAME,
    )
    generator.generate()
    return


def _generated_files(root: str) -> Dict[str, bytes]:
    """
        Maps every generated file under ``root`` (relative path) to its bytes:
        the client module, the two package ``__init__`` files and every
        ``.py`` in the ``groups`` and ``schemas`` directories.
    """
    found: Dict[str, bytes] = {}

    top_level = [CLIENT_MODULE_FILE, "__init__.py"]
    for name in top_level:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, "rb") as stream:
                found[name] = stream.read()

    for subdir in GENERATED_SUBDIRS:
        directory = os.path.join(root, subdir)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            with open(path, "rb") as stream:
                found[subdir + "/" + name] = stream.read()

    return found


class GeneratorDriftTests(unittest.TestCase):

    def test_regenerated_tree_matches_checked_in_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ghgen-") as scratch:
            _generate_into(scratch)
            regenerated = _generated_files(scratch)

        checked_in = _generated_files(PACKAGE_DIR)

        self.assertGreater(len(regenerated), 100, "expected the generator to produce hundreds of modules")

        missing = sorted(name for name in regenerated if name not in checked_in)
        extra = sorted(name for name in checked_in if name not in regenerated)
        self.assertEqual(missing, [], "generated files absent from the package: " + ", ".join(missing))
        self.assertEqual(extra, [], "package files the generator no longer produces: " + ", ".join(extra))

        drifted: List[str] = []
        for name in sorted(regenerated):
            if regenerated[name] != checked_in[name]:
                drifted.append(name)

        drift_message_lines = [
            "Checked-in generated files differ from a fresh regeneration. Regenerate with",
            "    python -m ccai.restclient.github.public.generation.githubrestclientgenerator",
            "or fix the generator. Drifted files ({}):".format(len(drifted)),
        ]
        for name in drifted[:25]:
            drift_message_lines.append("    " + name)
        self.assertEqual(drifted, [], os.linesep.join(drift_message_lines))
        return

    def test_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ghgen-a-") as first_dir, \
             tempfile.TemporaryDirectory(prefix="ghgen-b-") as second_dir:
            _generate_into(first_dir)
            _generate_into(second_dir)
            first = _generated_files(first_dir)
            second = _generated_files(second_dir)

        self.assertEqual(sorted(first), sorted(second))
        unstable = [name for name in sorted(first) if first[name] != second[name]]
        self.assertEqual(unstable, [], "files whose content changed between two runs: " + ", ".join(unstable))
        return


if __name__ == "__main__":
    unittest.main()
