# ----------------------------------------------------
#
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
#
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class FuncCnstDistColEq(AsFigoLintRule):
    """Check constant distribution ranges."""

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "FUNC_CNST_DIST_COL_EQ"

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

                # We are interested only in := distribution items.
                if ":=" not in item.text:
                    continue

                for value_range in item.iter_find_all(
                    {"tag": "kValueRange"}
                ):

                    # Get the two range expressions.
                    expressions = [
                        child
                        for child in value_range.children
                        if child.tag == "kExpression"
                    ]

                    if len(expressions) != 2:
                        continue

                    try:
                        start = int(expressions[0].text.strip())
                        end = int(expressions[1].text.strip())
                    except ValueError:
                        continue

                    # Report only large ranges.
                    if (end - start) > 255:
                        message = (
                            "FUNC: Constant distribution has a large "
                            "range.\n\n"
                            f"{item.text}\n"
                        )

                        self.linter.logViolation(
                            self.ruleID,
                            message,
                        )
