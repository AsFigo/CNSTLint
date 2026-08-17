# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class FuncCnstMissingCast(AsFigoLintRule):
    """FUNC_CNST_MISSING_CAST:
    Array reduction method sum() inside a constraint
    should use an explicit cast.
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "FUNC_CNST_MISSING_CAST"

    def apply(self, filePath, data):

        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):

            for functionNode in constraintNode.iter_find_all(
                {"tag": "kFunctionCall"}
            ):

                methodNodes = list(
                    functionNode.iter_find_all(
                        {"tag": "kBuiltinArrayMethodCallExtension"}
                    )
                )

                for methodNode in methodNodes:

                    if "sum" not in methodNode.text:
                        continue

                    # Check ancestors for kCast
                    hasCast = False

                    currentNode = functionNode.parent

                    while currentNode is not None:

                        if getattr(currentNode, "tag", None) == "kCast":
                            hasCast = True
                            break

                        currentNode = currentNode.parent

                    if hasCast:
                        continue

                    message = (
                        "Array reduction method sum() in a constraint "
                        "should use an explicit cast.\n"
                        f"{functionNode.text}"
                    )

                    self.linter.logViolation(
                        self.ruleID,
                        message
                    )
