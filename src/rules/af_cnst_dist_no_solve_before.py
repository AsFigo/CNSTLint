# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstDistNoSolveBefore(AsFigoLintRule):
    """
    **CNST_DIST_NO_SOLVE_BEFORE_VLT** — A ``rand`` variable that has a ``dist{}``
    constraint and also controls an implication (``->``) constraint on other
    ``rand`` variables requires a ``solve <var> before <others>`` directive.

    **Rationale**: Without ``solve ... before``, the solver may evaluate all
    constraints simultaneously, failing to honour the ``dist{}`` weights and
    allowing the implication antecedent to see an unsettled value. The
    ``solve ... before`` directive explicitly sequences the two-phase resolution:
    pick the ``dist``-weighted variable first, then solve the conditional
    constraints conditioned on that value.

    **Violation**::

        constraint c_dist   { qos_mode dist { BURST_MODE := 70, SPARSE_MODE := 30 }; }
        constraint c_burst  { qos_mode == BURST_MODE -> dma_grid[0][0] > 100; }
        // Missing: constraint c_order { solve qos_mode before dma_grid; }

    **Correct usage**::

        constraint c_order  { solve qos_mode before dma_grid; }
        constraint c_dist   { qos_mode dist { BURST_MODE := 70, SPARSE_MODE := 30 }; }
        constraint c_burst  { qos_mode == BURST_MODE -> dma_grid[0][0] > 100; }

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_DIST_NO_SOLVE_BEFORE_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for classNode in data.tree.iter_find_all({"tag": "kClassDeclaration"}):
            # Collect variables that appear in dist{} constraints
            dist_vars = set()
            for distNode in classNode.iter_find_all({"tag": "kDistribution"}):
                dist_ch = getattr(distNode, "children", [])
                if dist_ch:
                    var_text = getattr(dist_ch[0], "text", "").strip()
                    if var_text and var_text.isidentifier():
                        dist_vars.add(var_text)

            if not dist_vars:
                continue

            # Check whether any constraint in the class has 'solve ... before'
            all_constraint_text = " ".join(
                getattr(cn, "text", "")
                for cn in classNode.iter_find_all({"tag": "kConstraintDeclaration"})
            )
            if "solve" in all_constraint_text:
                continue

            # Look for implication (->) constraints where antecedent references
            # a dist variable
            for constraintNode in classNode.iter_find_all(
                {"tag": "kConstraintDeclaration"}
            ):
                for exprNode in constraintNode.iter_find_all(
                    {"tag": "kConstraintExpression"}
                ):
                    children = getattr(exprNode, "children", [])
                    # Find the '->' (constraint-implies) leaf
                    impl_idx = None
                    for idx, child in enumerate(children):
                        if getattr(child, "text", "").strip() == "->":
                            impl_idx = idx
                            break

                    if impl_idx is None or impl_idx == 0:
                        continue

                    antecedent = children[impl_idx - 1]
                    ant_text = getattr(antecedent, "text", "").strip()

                    for var in dist_vars:
                        if var in ant_text:
                            message = self.formatViolationMessage(
                                description=(
                                    f"Variable '{var}' has a 'dist{{}}' constraint "
                                    "and also appears in an implication antecedent, "
                                    "but no 'solve ... before' directive is present. "
                                    "Verilator may not honour the distribution weights "
                                    "and the implication may see an unsettled value."
                                ),
                                code_snippet=constraintNode.text,
                                fix_suggestion=(
                                    f"Add: constraint c_order "
                                    f"{{ solve {var} before <other_vars>; }}"
                                ),
                            )
                            self.linter.logViolation(self.ruleID, message)
                            break
