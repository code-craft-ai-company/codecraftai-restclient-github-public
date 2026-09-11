"""
    A floor on the number of tests the merge gate discovers, so a discovery
    regression fails loudly instead of quietly running fewer tests.
"""

import os
import unittest


# The discovery pattern the merge gate passes to `python -m unittest discover`.
GATE_PATTERN = "test_*.py"

# The number of tests the gate discovered when this floor was set.  Raise it
# when tests are added; never lower it without explaining why in the commit.
TEST_COUNT_FLOOR = 41


def _gate_start_dir() -> str:
    """
        Resolves the ``-s`` directory the gate passes (``source/tests``)
        from this module's location under it.
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    rtnval = os.path.dirname(this_dir)
    return rtnval


class SuiteFloorTests(unittest.TestCase):

    def test_gate_discovers_at_least_the_floor(self) -> None:
        """
            Mechanism: the gate runs ``python3 -m unittest discover -s
            ./source/tests -p "test_*.py"``, which is
            ``TestLoader().discover(start_dir, pattern)`` and runs the suite it
            returns.  This test calls the same discovery with the same start
            directory and pattern and counts the suite's test cases, so a
            test package that loses its ``__init__.py``, a module that stops
            importing, or a file renamed out of the pattern lowers the count
            and fails here.  A module that fails to import is reported by
            the loader as a synthetic failing test, so ``loader.errors`` is
            asserted empty separately rather than letting it pad the count.
        """
        start_dir = _gate_start_dir()

        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=start_dir, pattern=GATE_PATTERN)

        self.assertEqual(loader.errors, [], "discovery reported import errors:" + os.linesep + os.linesep.join(loader.errors))

        found = suite.countTestCases()
        errmsg_lines = [
            "The merge gate discovers fewer tests than the recorded floor.",
            "START DIR: {}".format(start_dir),
            "PATTERN: {}".format(GATE_PATTERN),
            "FLOOR: {}".format(TEST_COUNT_FLOOR),
            "FOUND: {}".format(found),
        ]
        self.assertGreaterEqual(found, TEST_COUNT_FLOOR, os.linesep.join(errmsg_lines))
        return


if __name__ == "__main__":
    unittest.main()
