from __future__ import unicode_literals
from __future__ import print_function

import sys
from unittest.suite import _isnotsuite, TestSuite
try:
    from io import StringIO
except: # pragma: no cover
    from cStringIO import StringIO

from green.output import GreenStream


class GreenTestSuite(TestSuite):
    """
    This version of a test suite has two important functions:

    1) It brings Python 3.4-like features to Python 2.7
    2) It adds Green-specific features  (see customize())
    """
    args = None

    def __init__(self, tests=(), args=None):
        # You should either set GreenTestSuite.args before instantiation, or
        # pass args into __init__
        super(GreenTestSuite, self).__init__(tests)
        self._removed_tests = 0
        self.customize(args)

    def customize(self, args):
        """
        Green-specific behavior customization via an args dictionary from
        the green.config module.  If you don't pass in an args dictionary,
        then this class acts like TestSuite from Python 3.4.
        """
        # Set a new args on the CLASS
        if args:
            self.args = args

        # Use the class args
        self.allow_stdout = self.args.allow_stdout

    def _removeTestAtIndex(self, index):
        """
        Python 3.4-like version of this function for Python 2.7's sake.
        """
        test = self._tests[index]
        if hasattr(test, 'countTestCases'):
            self._removed_tests += test.countTestCases()
        self._tests[index] = None

    def countTestCases(self):
        """
        Python 3.4-like version of this function for Python 2.7's sake.
        """
        cases = self._removed_tests
        for test in self:
            if test:
                cases += test.countTestCases()
        return cases

    def run(self, result):
        """
        Emulate unittest's behavior, with Green-specific changes.
        """
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(self):
            if result.shouldStop:
                break

            if _isnotsuite(test):
                self._tearDownPreviousClass(test, result)
                self._handleModuleFixture(test, result)
                self._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                if (getattr(test.__class__, '_classSetupFailed', False) or
                    getattr(result, '_moduleSetUpFailed', False)):
                    continue

                if not self.allow_stdout:
                    captured_stdout = StringIO()
                    saved_stdout = sys.stdout
                    sys.stdout = GreenStream(captured_stdout)

            test(result)

            if _isnotsuite(test):
                if not self.allow_stdout:
                    sys.stdout = saved_stdout
                    result.recordStdout(test, captured_stdout.getvalue())

            self._removeTestAtIndex(index)

        if topLevel:
            self._tearDownPreviousClass(None, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = False
        return result