# ----------------------------------------------------
#
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
#
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class FuncCnstDistColSl(AsFigoLintRule):
    """Intervals [a:b] should use :/ by default."""

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "FUNC_CNST_DIST_COL_SL"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):

        if data.tree is None:
            return

        for distribution in data.tree.iter_find_all(
            {"tag": "kDistribution"}
        ):

            for item in distribution.iter_find_all(
                {"tag": "kDistributionItem"}
            ):

                # Check whether this item is a range [a:b].
                has_value_range = any(
                    child.tag == "kValueRange"
                    for child in item.children
                )

                if not has_value_range:
                    continue

                # Check the direct children for the distribution operator.
                operator = None

                for child in item.children:
                    if child.text == ":=":
                        operator = ":="
                        break

                    if child.text == ":/":
                        operator = ":/"
                        break

                # Range using := should use :/ by default.
                if operator == ":=":

                    message = (
                        "FUNC: Intervals [a:b] should use :/ by default. "
                        "Use := only when intentionally assigning the "
                        "weight to every value in the range.\n\n"
                        f"{item.text}\n"
                    )

                    self.linter.logViolation(
                        self.ruleID,
                        message,
                    )
