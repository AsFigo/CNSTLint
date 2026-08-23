# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstSumNarrowNoCast(AsFigoLintRule):
    """
    **CNST_SUM_WITH_NARROW_NO_CAST_VLT** — A ``sum()`` with predicate must cast
    each element to avoid silent narrow-integer truncation.

    **Rationale**: When ``sum()`` is applied to an array of narrow types (e.g.,
    ``bit``, ``byte``), the accumulator has the same width as the element type.
    Summing many narrow elements without an explicit cast causes the intermediate
    and final result to silently overflow / truncate. The fix is to cast the
    iterator variable inside the ``with`` clause to a wider type (e.g.,
    ``int``), so the accumulator has sufficient range.

    **Violation**::

        constraint c_hamming {
            changed_bits.sum() with (item) == toggle_target;  // no cast -- violation
        }

    **Correct usage**::

        constraint c_hamming {
            changed_bits.sum() with (int'(item)) == toggle_target;  // cast present
        }

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_SUM_WITH_NARROW_NO_CAST_VLT"

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
                # Check if this is a sum() call
                is_sum = False
                for child in methodNode.children:
                    if getattr(child, "text", "").strip() == "sum":
                        is_sum = True
                        break

                if not is_sum:
                    continue

                # Check for with() predicate
                for predNode in methodNode.iter_find_all(
                    {"tag": "kArrayWithPredicate"}
                ):
                    # If no kCast inside the predicate, flag it
                    if not list(predNode.iter_find_all({"tag": "kCast"})):
                        message = self.formatViolationMessage(
                            description=(
                                "sum() with a predicate (with clause) does not "
                                "cast the iterator element. Without a cast, the "
                                "accumulator width equals the element type width, "
                                "causing silent truncation when summing narrow types."
                            ),
                            code_snippet=methodNode.text,
                            fix_suggestion=(
                                "Add an explicit type cast inside the with() "
                                "clause, e.g., '.sum() with (int'(item))' to "
                                "widen the accumulator before summation."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
