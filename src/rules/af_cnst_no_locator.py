# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule

# Array locator methods (IEEE 1800-2017 §7.12.2) are not supported
# inside constraint blocks by most synthesis and formal tools.
_LOCATOR_METHODS = frozenset({
    "find", "find_first", "find_last",
    "find_index", "find_first_index", "find_last_index",
    "min", "max",
})


class CnstNoLocatorInConstraint(AsFigoLintRule):
    """
    **CNST_NO_LOCATOR_IN_CONSTRAINT_VLT** — Array locator methods must not appear
    inside constraint blocks.

    **Rationale**: Array locator methods (``find``, ``find_first``, ``find_last``,
    ``find_index``, ``find_first_index``, ``find_last_index``, ``min``, ``max``)
    are iterative query functions. Using them inside constraint blocks couples the
    solver to imperative iteration semantics, which most constraint solvers and
    formal tools do not support. The result is either a tool error or silently
    vacuous constraints.

    **Violation**::

        constraint c_no_flush {
            cmd_list.find() with (item != 8'hFF);  // locator in constraint -- violation
        }

    **Correct usage**::

        function void post_randomize();
            // Perform locator-style filtering in procedural code
            filtered = cmd_list.find() with (item != 8'hFF);
        endfunction

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_NO_LOCATOR_IN_CONSTRAINT_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for methodNode in constraintNode.iter_find_all(
                {"tag": "kBuiltinArrayMethodCallExtension"}
            ):
                for child in methodNode.children:
                    method_name = getattr(child, "text", "").strip()
                    if method_name in _LOCATOR_METHODS:
                        message = self.formatViolationMessage(
                            description=(
                                f"Array locator method '{method_name}()' used "
                                "inside a constraint block. Locator methods are "
                                "imperative iteration constructs not supported "
                                "by constraint solvers."
                            ),
                            code_snippet=constraintNode.text,
                            fix_suggestion=(
                                "Move the locator method call to "
                                "post_randomize() or a procedural function. "
                                "Rewrite the constraint using 'inside', "
                                "'unique', or relational operators instead."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
                        break  # one report per method node
