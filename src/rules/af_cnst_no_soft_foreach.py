# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule
import logging
import anytree

class FcnstNoSoftForeach(AsFigoLintRule):
    """
    AF_CNST_NO_SOFT_FOREACH:

    Detects a soft constraint declared inside a foreach
    constraint block.

    A soft constraint inside foreach is applied on a
    per-iteration basis and can interact unexpectedly
    with hard constraints.
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "AF_CNST_NO_SOFT_FOREACH"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):

        # Search all constraint declarations.
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):

            # Search constraint expressions inside the constraint.
            for exprNode in constraintNode.iter_find_all(
                {"tag": "kConstraintExpression"}
            ):

                # We are interested only in foreach expressions.
                has_foreach = False

                for child in exprNode.children:
                    if getattr(child, "text", "").strip() == "foreach":
                        has_foreach = True
                        break

                if not has_foreach:
                    continue

                # The foreach body is normally represented by
                # a kBraceGroup under the foreach expression.
                for braceNode in exprNode.iter_find_all(
                    {"tag": "kBraceGroup"}
                ):

                    # Check constraint expressions inside foreach body.
                    for bodyExprNode in braceNode.iter_find_all(
                        {"tag": "kConstraintExpression"}
                    ):

                        # A soft constraint is represented by a
                        # "soft" leaf, not a kSoftConstraint node.
                        for child in bodyExprNode.children:
                            if getattr(child, "text", "").strip() == "soft":

                                message = self.formatViolationMessage(
                                    description=(
                                        "Soft constraint declared inside "
                                        "a foreach constraint block. "
                                        "Soft constraints inside foreach "
                                        "are applied per iteration and "
                                        "can interact unexpectedly with "
                                        "hard constraints."
                                    ),
                                    code_snippet=bodyExprNode.text,
                                    fix_suggestion=(
                                        "Move the soft constraint outside "
                                        "the foreach block."
                                    ),
                                )

                                self.linter.logViolation(
                                    self.ruleID,
                                    message,
                                )
