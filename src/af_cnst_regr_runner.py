# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

import glob
import os
import sys
import unittest

# Resolve absolute paths to repository directories
srcDir = os.path.dirname(os.path.abspath(__file__))
repoRootDir = os.path.abspath(os.path.join(srcDir, ".."))
binDir = os.path.join(repoRootDir, "bin")
testsDir = os.path.join(repoRootDir, "tests")

# Add 'bin' and 'src' to Python import path dynamically
if binDir not in sys.path:
    sys.path.append(binDir)
if srcDir not in sys.path:
    sys.path.append(srcDir)

from cnstlint import CNSTLinter


def makePassTest(filePath):
    """Returns a test method that asserts 0 errors for a pass case."""
    def test(self):
        self.linter.resetFileState(filePath)
        self.linter.runOnSingleFile(filePath)
        self.assertEqual(
            self.linter.errorCount,
            0,
            f"Expected 0 errors for {os.path.basename(filePath)}, "
            f"but found {self.linter.errorCount}: {self.linter.errorList}",
        )
    return test


def makeFailTest(filePath):
    """Returns a test method that asserts >= 1 error for a fail case."""
    def test(self):
        self.linter.resetFileState(filePath)
        self.linter.runOnSingleFile(filePath)
        self.assertGreater(
            self.linter.errorCount,
            0,
            f"Expected lint violations for {os.path.basename(filePath)}, "
            f"but 0 were reported.",
        )
    return test


class TestCNSTLintRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Instantiate linter once for all test runs."""
        configPath = os.path.join(testsDir, "config.toml")
        if not os.path.exists(configPath):
            configPath = os.path.join(repoRootDir, "config.toml")
        cls.linter = CNSTLinter(configFile=configPath)


# Dynamically register one test method per pass file
for _filePath in sorted(glob.glob(os.path.join(testsDir, "*_p.sv"))):
    _testName = "test_pass_" + os.path.basename(_filePath).replace(".sv", "")
    setattr(TestCNSTLintRules, _testName, makePassTest(_filePath))

# Dynamically register one test method per fail file
for _filePath in sorted(glob.glob(os.path.join(testsDir, "*_f.sv"))):
    _testName = "test_fail_" + os.path.basename(_filePath).replace(".sv", "")
    setattr(TestCNSTLintRules, _testName, makeFailTest(_filePath))


if __name__ == "__main__":
    logPath = os.path.join(os.getcwd(), "regression_summary.log")

    with open(logPath, "w") as logFile:
        runner = unittest.TextTestRunner(stream=logFile, verbosity=2)
        unittest.main(testRunner=runner, exit=False)

    print(f"Regression complete. Log saved to: {logPath}")
