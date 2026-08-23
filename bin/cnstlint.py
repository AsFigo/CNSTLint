# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

import sys
import os
import argparse
import logging
import verible_verilog_syntax

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from af_lint_rule import AsFigoLintRule
from asfigo_linter import AsFigoLinter
from rules.af_cnst_no_soft_foreach import FcnstNoSoftForeach
from rules.af_func_cnst_wrong_oper_pre import FuncCnstWrongOperPre
from rules.af_func_cnst_missing_cast import FuncCnstMissingCast
from rules.af_func_cnst_dist_col_eq import FuncCnstDistColEq
from rules.af_func_cnst_dist_col_sl import FuncCnstDistColSl
from rules.af_cnst_additive_overflow import CnstAdditiveOverflowInBound
from rules.af_cnst_dist_no_solve_before import CnstDistNoSolveBefore
from rules.af_cnst_dist_on_enum import CnstDistOnEnumType
from rules.af_cnst_foreach_unguarded_prev import CnstForeachUnguardedPrevIdx
from rules.af_cnst_name_convention import CnstNameConvention
from rules.af_cnst_no_enum_in_with import CnstNoEnumInWithClause
from rules.af_cnst_no_locator import CnstNoLocatorInConstraint
from rules.af_cnst_no_struct_sum import CnstNoStructSumWith
from rules.af_cnst_rand_class_handle import CnstRandClassHandleArray
from rules.af_cnst_rand_mode_leftover import CnstRandModeLeftover
from rules.af_cnst_rand_no_logic import CnstRandNoLogic
from rules.af_cnst_randc_dyn_excl import CnstRandcDynamicExclusion
from rules.af_cnst_sum_narrow_no_cast import CnstSumNarrowNoCast
from rules.af_cnst_unique_large_arr import CnstUniqueLargeArray
from rules.af_cnst_unique_row_slice import CnstUniqueRowSlice


class CNSTLinter(AsFigoLinter):
    """Linter that applies constraint lint rules on SystemVerilog code."""

    def __init__(self, configFile="config.toml", logLevel=logging.INFO):
        super().__init__(configFile=configFile, logLevel=logLevel)
        self.rules = [rule_cls(self) for rule_cls in AsFigoLintRule.__subclasses__()]

    def loadSyntaxTree(self, file_path: str):
        """Loads SystemVerilog syntax tree using VeribleVerilogSyntax."""
        parser = verible_verilog_syntax.VeribleVerilogSyntax()
        return parser.parse_files([file_path], options={"gen_tree": True})

    def runOnSingleFile(self, file_path: str):
        """Runs all registered lint rules on a single file."""
        self.resetFileState(file_path)

        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return

        treeData = self.loadSyntaxTree(file_path)

        for path, fileData in treeData.items():
            self.logInfo("CNSTLint", f"Loaded test file: {file_path}")
            for rule in self.rules:
                rule.run(path, fileData)

    def runOnFlist(self, flist_path: str):
        """Runs registered rules sequentially on files listed in a filelist."""
        files = self._parseFlist(flist_path)
        for file_path in files:
            self.runOnSingleFile(file_path)

    def runCli(self) -> int:
        """Parses command-line arguments and triggers linter execution."""
        parser = argparse.ArgumentParser(description="AsFigo CNSTLint Engine")
        parser.add_argument("-t", "--test", help="Path to single SystemVerilog target file")
        parser.add_argument("-f", "--filelist", help="Path to filelist containing SystemVerilog target files")
        parser.add_argument("-c", "--config", default="config.toml", help="Path to rules configuration file")

        args = parser.parse_args()

        if args.config != "config.toml":
            self.rulesConfig = self.loadConfig(args.config)

        if args.test:
            self.runOnSingleFile(args.test)
        elif args.filelist:
            self.runOnFlist(args.filelist)
        else:
            parser.print_help()
            return 1

        self.logSummary()
        return 1 if self.totalErrorCount > 0 else 0


if __name__ == "__main__":
    linter = CNSTLinter(configFile="config.toml", logLevel=logging.INFO)
    sys.exit(linter.runCli())
