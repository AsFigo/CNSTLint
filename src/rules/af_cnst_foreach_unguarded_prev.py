# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstForeachUnguardedPrevIdx(AsFigoLintRule):
    """
    **CNST_FOREACH_UNGUARDED_PREV_IDX_VLT** — Inside a ``foreach`` constraint,
    accessing ``arr[i-1]`` without an enclosing ``if (i > 0)`` guard causes
    silent unsigned wraparound to the maximum index value when ``i == 0``.

    **Rationale**: The ``foreach`` loop variable is unsigned in Verilator and
    most simulators. When ``i == 0``, the expression ``i-1`` wraps to the
    largest representable unsigned value (e.g., ``2^32-1``), silently
    accessing the wrong array element rather than being skipped.

    **Violation**::

        constraint c_no_overlap {
            foreach (regions[i])
                regions[i].base_addr > regions[i-1].limit_addr;  // wraps at i==0
        }

    **Correct usage**::

        constraint c_no_overlap {
            foreach (regions[i])
                if (i > 0)
                    regions[i].base_addr > regions[i-1].limit_addr;
        }

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_FOREACH_UNGUARDED_PREV_IDX_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for foreachExpr in constraintNode.iter_find_all(
                {"tag": "kConstraintExpression"}
            ):
                children = getattr(foreachExpr, "children", [])
                if not children:
                    continue
                if getattr(children[0], "text", "").strip() != "foreach":
                    continue

                # Extract loop variable from the foreach paren group: foreach(arr[i])
                loop_var = None
                for parenNode in foreachExpr.iter_find_all({"tag": "kParenGroup"}):
                    for dimNode in parenNode.iter_find_all(
                        {"tag": "kDimensionScalar"}
                    ):
                        for unqId in dimNode.iter_find_all(
                            {"tag": "kUnqualifiedId"}
                        ):
                            candidate = getattr(unqId, "text", "").strip()
                            if candidate and candidate.isidentifier():
                                loop_var = candidate
                            break
                        break
                    break

                if not loop_var:
                    continue

                # Get the body kConstraintExpression (child after paren group)
                body_nodes = [
                    c for c in children
                    if getattr(c, "tag", "") == "kConstraintExpression"
                ]
                if not body_nodes:
                    continue
                body = body_nodes[0]

                # If the body is directly guarded with 'if', it is safe
                body_children = getattr(body, "children", [])
                if any(
                    getattr(c, "text", "").strip() == "if"
                    for c in body_children
                ):
                    continue

                # Look for arr[loop_var - N] subscripts in the body
                for dimNode in body.iter_find_all({"tag": "kDimensionScalar"}):
                    for binExpr in dimNode.iter_find_all(
                        {"tag": "kBinaryExpression"}
                    ):
                        bin_ch = getattr(binExpr, "children", [])
                        if len(bin_ch) < 3:
                            continue
                        op = getattr(bin_ch[1], "text", "").strip()
                        lhs = getattr(bin_ch[0], "text", "").strip()
                        if op == "-" and lhs == loop_var:
                            message = self.formatViolationMessage(
                                description=(
                                    f"foreach loop uses '{loop_var}-N' subscript "
                                    f"without 'if ({loop_var} > 0)' guard. "
                                    f"When {loop_var}==0, unsigned subtraction "
                                    "wraps to maximum index, silently accessing "
                                    "the wrong array element."
                                ),
                                code_snippet=foreachExpr.text,
                                fix_suggestion=(
                                    f"Wrap the constraint body in "
                                    f"'if ({loop_var} > 0) {{ ... }}'. "
                                    "The first element has no predecessor "
                                    "and should be skipped."
                                ),
                            )
                            self.linter.logViolation(self.ruleID, message)
                            break
