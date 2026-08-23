# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstDistOnEnumType(AsFigoLintRule):
    """
    **CNST_DIST_ON_ENUM_TYPE_VLT** — A ``dist{}`` expression applied to a ``rand``
    field of enum type does not reproduce the declared weights reliably in
    Verilator.

    **Rationale**: Confirmed over 2000 trials: a ``rand enum`` field with
    ``dist {A:=20, B:=50, C:=30}`` lands nowhere near those weights
    (observed 25/28/47 instead of 20/50/30). The identical weights on a
    plain-bit field of the same width match target within ≈1 point. The fix
    is to drive the weighted pick through a plain ``rand bit [N:0]`` field
    and map it onto the enum afterward with implication constraints.

    **Violation**::

        typedef enum bit [1:0] { HIT_EX, HIT_MEM, HIT_WB, HIT_NONE } stage_e;
        rand stage_e target;
        constraint c_dist { target dist { HIT_EX := 40, HIT_MEM := 40, HIT_WB := 20 }; }

    **Correct usage**::

        rand bit [1:0] target_pick;
        rand stage_e   target;
        constraint c_pick_dist { target_pick dist { 0 := 40, 1 := 40, 2 := 20, 3 := 0 }; }
        constraint c_map {
            target_pick == 0 -> target == HIT_EX;
            target_pick == 1 -> target == HIT_MEM;
            target_pick == 2 -> target == HIT_WB;
            target_pick == 3 -> target == HIT_NONE;
        }

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_DIST_ON_ENUM_TYPE_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        enum_typedefs = self._collect_enum_typedef_names(data.tree)
        if not enum_typedefs:
            return

        field_types = self._collect_field_type_map(data.tree)

        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for distNode in constraintNode.iter_find_all({"tag": "kDistribution"}):
                dist_ch = getattr(distNode, "children", [])
                if not dist_ch:
                    continue
                var_text = getattr(dist_ch[0], "text", "").strip()
                if not var_text or not var_text.isidentifier():
                    continue
                field_type = field_types.get(var_text, "")
                if field_type not in enum_typedefs:
                    continue
                message = self.formatViolationMessage(
                    description=(
                        f"'dist{{}}' constraint on '{var_text}' which is of "
                        f"enum type '{field_type}'. Verilator does not "
                        "reliably honour distribution weights on enum-typed "
                        "rand fields; observed weights deviate significantly "
                        "from declared values."
                    ),
                    code_snippet=constraintNode.text,
                    fix_suggestion=(
                        f"Replace with a plain 'rand bit [N:0] {var_text}_pick' "
                        "field, apply dist{} to that, then map to the enum "
                        "with implication constraints."
                    ),
                )
                self.linter.logViolation(self.ruleID, message)

    def _collect_enum_typedef_names(self, tree):
        """Return set of typedef names that resolve to enum types in this file."""
        names = set()
        for typeDecl in tree.iter_find_all({"tag": "kTypeDeclaration"}):
            if not list(typeDecl.iter_find_all({"tag": "kEnumType"})):
                continue
            for child in reversed(getattr(typeDecl, "children", [])):
                text = getattr(child, "text", "").strip()
                if text and text.isidentifier() and text not in (
                    "typedef", "enum", ";"
                ):
                    names.add(text)
                    break
        return names

    def _collect_field_type_map(self, tree):
        """Return dict mapping field_name → type_name for all declarations."""
        field_types = {}
        for declNode in tree.iter_find_all({"tag": "kDataDeclaration"}):
            type_name = ""
            for instType in declNode.iter_find_all({"tag": "kInstantiationType"}):
                for localRoot in instType.iter_find_all({"tag": "kLocalRoot"}):
                    for unqId in localRoot.iter_find_all({"tag": "kUnqualifiedId"}):
                        type_name = getattr(unqId, "text", "").strip()
                        break
                    break
                break
            if not type_name:
                continue
            for varAssign in declNode.iter_find_all(
                {"tag": "kVariableDeclarationAssignment"}
            ):
                va_ch = getattr(varAssign, "children", [])
                if va_ch:
                    fname = getattr(va_ch[0], "text", "").strip()
                    if fname and fname.isidentifier():
                        field_types[fname] = type_name
        return field_types
