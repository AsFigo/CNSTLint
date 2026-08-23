# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstAdditiveOverflowInBound(AsFigoLintRule):
    """
    **CNST_ADDITIVE_OVERFLOW_IN_BOUND_VLT** — Inside a constraint,
    ``A + B <= MAX`` where ``MAX`` is near the operand type maximum can
    silently pass when the true sum overflows and wraps to a small value.

    **Rationale**: SV constraint addition is performed in the operand's
    native width without automatic promotion. When ``p_start_addr + page_size``
    approaches or exceeds ``2^32``, the result wraps (e.g., ``0xFFFF0000 +
    0x20000 == 0x10000`` in 32 bits). The wrapped value satisfies
    ``<= 32'hFFFF_FFFF`` while the physical address is actually out of bounds.
    Rearrange to subtract on the RHS to avoid the addition entirely.

    **Violation**::

        constraint c_bound {
            p_start_addr + page_size <= 32'hFFFF_FFFF;  // can wrap silently
        }

    **Correct usage**::

        constraint c_bound {
            p_start_addr <= 32'hFFFF_FFFF - page_size;  // no addition, no overflow
        }

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_ADDITIVE_OVERFLOW_IN_BOUND_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for outerBin in constraintNode.iter_find_all(
                {"tag": "kBinaryExpression"}
            ):
                children = getattr(outerBin, "children", [])
                if len(children) < 3:
                    continue
                op = getattr(children[1], "text", "").strip()
                if op not in ("<=", "<"):
                    continue
                lhs = children[0]
                if getattr(lhs, "tag", "") != "kBinaryExpression":
                    continue
                lhs_ch = getattr(lhs, "children", [])
                if len(lhs_ch) < 3:
                    continue
                inner_op = getattr(lhs_ch[1], "text", "").strip()
                if inner_op != "+":
                    continue
                message = self.formatViolationMessage(
                    description=(
                        "Constraint uses 'A + B <= MAX' where the addition "
                        "can silently overflow and wrap to a small value, "
                        "satisfying the bound while the true sum is out of range."
                    ),
                    code_snippet=outerBin.text,
                    fix_suggestion=(
                        "Rearrange to 'A <= MAX - B' to eliminate the "
                        "addition and avoid overflow. Ensure MAX - B cannot "
                        "itself underflow (use a conditional or known-safe bounds)."
                    ),
                )
                self.linter.logViolation(self.ruleID, message)
