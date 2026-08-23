# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstUniqueRowSlice(AsFigoLintRule):
    """
    **CNST_UNIQUE_MDA_ROW_SLICE_VLT** — The ``unique`` constraint must not operate on
    a single row slice of a multi-dimensional array selected by an index variable.

    **Rationale**: Using ``unique { array[i] }`` inside a ``foreach`` loop
    constrains only the elements of a single row at a time. Each row is solved
    independently, meaning uniqueness is enforced per-row but NOT across rows.
    This leads to a weaker constraint than the author likely intended and
    can cause subtle solver portability issues. If cross-row uniqueness is
    required, iterate the full flattened array or apply ``unique`` to the
    entire 2-D array.

    **Violation**::

        constraint c_row_unique {
            foreach (core_power[i]) {
                unique { core_power[i] };  // only row i is unique -- violation
            }
        }

    **Correct usage**::

        constraint c_all_unique {
            unique { core_power };   // unique across all elements
        }

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_UNIQUE_MDA_ROW_SLICE_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for uniqueNode in constraintNode.iter_find_all(
                {"tag": "kUniquenessConstraint"}
            ):
                # A kDimensionScalar inside the unique brace group means
                # the expression is subscripted (e.g., array[i]), which
                # limits uniqueness to a single row/slice.
                for braceNode in uniqueNode.iter_find_all({"tag": "kBraceGroup"}):
                    if list(braceNode.iter_find_all({"tag": "kDimensionScalar"})):
                        message = self.formatViolationMessage(
                            description=(
                                "The 'unique' constraint operates on a "
                                "subscripted row slice (e.g., array[i]). "
                                "This enforces uniqueness only within the "
                                "selected row, not across the entire multi-dimensional array."
                            ),
                            code_snippet=uniqueNode.text,
                            fix_suggestion=(
                                "Apply 'unique { array }' to the whole array "
                                "if cross-row uniqueness is required, or "
                                "restructure the constraint logic."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
                        break  # one report per unique node
