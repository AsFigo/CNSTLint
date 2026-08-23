# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstRandcDynamicExclusion(AsFigoLintRule):
    """
    **CNST_RANDC_DYNAMIC_EXCLUSION_VLT** — A ``randc`` variable must not be
    constrained with ``inside { dynamic_variable }`` to exclude already-used
    values.

    **Rationale**: ``randc`` variables cycle through all legal values before
    repeating, providing built-in uniqueness within a single randomize epoch.
    Pairing ``randc`` with an ``inside { queue }`` exclusion constraint
    creates conflicting semantics: the solver must simultaneously guarantee
    cycling AND enforce a runtime exclusion set. This leads to solver failures
    or tool-specific undefined behaviour once the exclusion set grows.

    The correct pattern is to use a plain ``rand`` variable, manage a dynamic
    exclusion queue in ``post_randomize()``, and constrain with
    ``!(id inside { used_ids_q })``.

    **Violation**::

        class TaggedFrame;
            randc bit [7:0] id;
            static bit [7:0] used_ids_q[$];
            constraint c_unique {
                !(id inside { used_ids_q });  // randc + dynamic inside -- violation
            }
        endclass

    **Correct usage**::

        class TaggedFrame;
            rand bit [7:0] id;             // use rand, not randc
            static bit [7:0] used_ids_q[$];
            constraint c_unique {
                !(id inside { used_ids_q });
            }
            function void post_randomize();
                used_ids_q.push_back(id);  // track used values here
            endfunction
        endclass

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_RANDC_DYNAMIC_EXCLUSION_VLT"

    def _collect_randc_vars(self, classNode):
        """
        Returns a set of variable names declared with 'randc' in this class.
        """
        randc_vars = set()
        for declNode in classNode.iter_find_all({"tag": "kDataDeclaration"}):
            is_randc = False
            for qualNode in declNode.iter_find_all({"tag": "kQualifierList"}):
                for child in qualNode.children:
                    if getattr(child, "text", "").strip() == "randc":
                        is_randc = True
            if not is_randc:
                continue
            # Collect declared variable names
            for assignNode in declNode.iter_find_all(
                {"tag": "kVariableDeclarationAssignment"}
            ):
                for child in assignNode.children:
                    text = getattr(child, "text", "").strip()
                    tag = getattr(child, "tag", None)
                    # SymbolIdentifier leaf = variable name
                    if tag == "SymbolIdentifier" and text:
                        randc_vars.add(text)
        return randc_vars

    def _constraint_has_inside_with_variable(self, constraintNode):
        """
        Returns True if any constraint expression uses 'inside { variable }'
        where the inside set contains a variable reference (kLocalRoot),
        not just numeric/range literals.
        """
        for binaryNode in constraintNode.iter_find_all(
            {"tag": "kBinaryExpression"}
        ):
            has_inside_op = False
            for child in binaryNode.children:
                if getattr(child, "text", "").strip() == "inside":
                    has_inside_op = True
                    break
            if not has_inside_op:
                continue

            # Check the inside set for variable references
            for rangeListNode in binaryNode.iter_find_all(
                {"tag": "kOpenRangeList"}
            ):
                if list(rangeListNode.iter_find_all({"tag": "kLocalRoot"})):
                    return True
        return False

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for classNode in data.tree.iter_find_all({"tag": "kClassDeclaration"}):
            randc_vars = self._collect_randc_vars(classNode)
            if not randc_vars:
                continue

            for constraintNode in classNode.iter_find_all(
                {"tag": "kConstraintDeclaration"}
            ):
                if self._constraint_has_inside_with_variable(constraintNode):
                    message = self.formatViolationMessage(
                        description=(
                            f"Class has 'randc' variable(s) {sorted(randc_vars)} "
                            "and a constraint that uses 'inside { dynamic_variable }' "
                            "for exclusion. Combining randc cycling semantics with "
                            "a runtime dynamic exclusion set leads to solver conflicts."
                        ),
                        code_snippet=constraintNode.text,
                        fix_suggestion=(
                            "Replace 'randc' with 'rand'. Add a 'post_randomize()' "
                            "function to push newly generated values into the "
                            "exclusion queue, keeping the 'inside' constraint."
                        ),
                    )
                    self.linter.logViolation(self.ruleID, message)
