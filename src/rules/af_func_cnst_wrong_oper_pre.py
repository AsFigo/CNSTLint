# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule
import logging
import anytree

class FuncCnstWrongOperPre(AsFigoLintRule):
    """
    FUNC_CNST_WRONG_OPER_PRE:
    Detects mixed operator precedence in constraint expressions where
    equality/relational operators are combined with the conditional
    (?:) operator without explicitly grouping the conditional expression.

    Such expressions can be interpreted differently due to SystemVerilog
    operator precedence and may not represent the intended constraint.

    The conditional expression should be explicitly enclosed in parentheses
    to make the intended evaluation order unambiguous.
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "FUNC_CNST_WRONG_OPER_PRE"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):

        #
        # Search all constraint declarations
        #
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):

            #
            # Search condition expressions inside
            # the constraint.
            #
            for conditionNode in constraintNode.iter_find_all(
                {"tag": "kConditionExpression"}
            ):

                binaryNode = next(
                    conditionNode.iter_find_all(
                        {"tag": "kBinaryExpression"}
                    ),
                    None,
                )

                if binaryNode is None:
                    continue

                #
                # Confirm the binary operator is ==.
                #
                hasEquality = any(
                    getattr(child, "text", None) == "=="
                    for child in binaryNode.children
                )

                if not hasEquality:
                    continue

                #
                # Violation
                #
                message = self.formatViolationMessage(
                    description=(
                        "Mixed operator precedence in constraint "
                        "expression. Use parentheses around the "
                        "conditional expression."
                    ),
                    code_snippet=conditionNode.text,
                    fix_suggestion=(
                        "Use parentheses around the conditional "
                        "expression."
                    ),
                )

                self.linter.logViolation(
                    self.ruleID,
                    message,
                )
