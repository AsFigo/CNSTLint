# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule

_UNIQUE_SIZE_THRESHOLD = 4


class CnstUniqueLargeArray(AsFigoLintRule):
    """
    **CNST_UNIQUE_LARGE_ARRAY_VLT** — ``unique{}`` applied to an unpacked array
    with more than 4 elements is silently unreliable in Verilator.

    **Rationale**: Verilator's ``unique{}`` implementation does not scale
    correctly for arrays larger than approximately 4 elements. ``randomize()``
    returns 1 (success) while the result may contain duplicate values. Use
    pairwise ``!=`` constraints instead.

    **Violation**::

        rand bit [7:0] vals[8];
        constraint c_u { unique {vals}; }  // silently wrong for 8 elements

    **Correct usage**::

        constraint c_u {
            foreach (vals[i])
                foreach (vals[j])
                    if (i != j) vals[i] != vals[j];
        }

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_UNIQUE_LARGE_ARRAY_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        # Build field name → fixed unpacked size map
        field_sizes = {}
        for declNode in data.tree.iter_find_all({"tag": "kDataDeclaration"}):
            for varAssign in declNode.iter_find_all(
                {"tag": "kVariableDeclarationAssignment"}
            ):
                va_children = getattr(varAssign, "children", [])
                if not va_children:
                    continue
                field_name = getattr(va_children[0], "text", "").strip()
                if not field_name or not field_name.isidentifier():
                    continue
                for unpackNode in varAssign.iter_find_all(
                    {"tag": "kUnpackedDimensions"}
                ):
                    for dimScalar in unpackNode.iter_find_all(
                        {"tag": "kDimensionScalar"}
                    ):
                        for exprList in dimScalar.iter_find_all(
                            {"tag": "kExpressionList"}
                        ):
                            for numNode in exprList.iter_find_all(
                                {"tag": "kNumber"}
                            ):
                                try:
                                    size = int(
                                        getattr(numNode, "text", "0").strip()
                                    )
                                    field_sizes[field_name] = size
                                except ValueError:
                                    pass
                                break
                        break
                    break

        # Check unique{} constraints
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for uniqueNode in constraintNode.iter_find_all(
                {"tag": "kUniquenessConstraint"}
            ):
                for braceNode in uniqueNode.iter_find_all({"tag": "kBraceGroup"}):
                    for exprNode in braceNode.iter_find_all({"tag": "kExpression"}):
                        var_name = getattr(exprNode, "text", "").strip()
                        if not var_name:
                            break
                        size = field_sizes.get(var_name)
                        if size is None:
                            # Dynamic array — warn unconditionally
                            message = self.formatViolationMessage(
                                description=(
                                    f"'unique{{{var_name}}}' on a dynamic array. "
                                    "Verilator's unique{} is unreliable for "
                                    "arrays larger than 4 elements."
                                ),
                                code_snippet=uniqueNode.text,
                                fix_suggestion=(
                                    "Use pairwise '!=' constraints inside nested "
                                    "foreach loops instead of unique{}."
                                ),
                            )
                            self.linter.logViolation(self.ruleID, message)
                        elif size > _UNIQUE_SIZE_THRESHOLD:
                            message = self.formatViolationMessage(
                                description=(
                                    f"'unique{{{var_name}}}' on an array of "
                                    f"{size} elements (threshold: "
                                    f"{_UNIQUE_SIZE_THRESHOLD}). "
                                    "Verilator silently produces duplicates for "
                                    "arrays larger than 4 elements."
                                ),
                                code_snippet=uniqueNode.text,
                                fix_suggestion=(
                                    "Use pairwise '!=' constraints inside nested "
                                    "foreach loops instead of unique{}."
                                ),
                            )
                            self.linter.logViolation(self.ruleID, message)
                        break
                    break
