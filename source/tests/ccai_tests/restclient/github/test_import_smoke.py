"""
    Import smoke test for the generated GitHub public REST client.

    The package is several hundred generated modules. Nothing exercises most
    of them, so the cheapest useful guarantee is that every module imports:
    a regeneration that breaks a module's imports, references a missing
    base-class symbol, or ships a syntax error fails here by name.
"""

import importlib
import pkgutil
import unittest
import warnings

ROOT_PACKAGE = "ccai.restclient.github"


def _walk_module_names():
    root = importlib.import_module(ROOT_PACKAGE)
    rtnval = [info.name for info in pkgutil.walk_packages(root.__path__, root.__name__ + ".")]
    return rtnval


class ImportSmokeTests(unittest.TestCase):

    def test_package_is_not_empty(self) -> None:
        names = _walk_module_names()
        self.assertGreater(len(names), 100, "expected the generated client to contain hundreds of modules")
        return

    def test_every_module_imports(self) -> None:
        failures = []
        with warnings.catch_warnings():
            # Generated docstrings are checked separately; an import failure is the signal here.
            warnings.simplefilter("ignore")
            for name in _walk_module_names():
                try:
                    importlib.import_module(name)
                except Exception as exc:  # noqa: BLE001 - every failure is reported by module name
                    failures.append("{}: {!r}".format(name, exc))
        self.assertEqual(failures, [], "modules that failed to import:\n" + "\n".join(failures))
        return

    def test_client_class_is_exposed(self) -> None:
        module = importlib.import_module(ROOT_PACKAGE + ".public.githubpublicrestclient")
        classes = [name for name in dir(module) if name.endswith("RestClient")]
        self.assertTrue(classes, "expected a *RestClient class in the public client module")
        return


if __name__ == "__main__":
    unittest.main()
