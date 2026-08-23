# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstNoStructSumWith(AsFigoLintRule):
    """
    **CNST_NO_STRUCT_SUM_WITH_VLT** — ``sum() with (...)`` on a struct-typed
    array must not appear inside a constraint block.

    **Rationale**: For any struct-typed array, ``array.sum() with (expr)``
    generates a malformed SMT query (``Sorts (...) are incompatible``) that
    the solver rejects. ``randomize()`` returns 0 (failure) even though the
    constraint is syntactically valid. Use a prefix-sum helper array of plain
    integers instead.

    **Violation**::

        typedef struct { rand bit [7:0] dma_size; } cmd_s;
        rand cmd_s cmd_list[];
        constraint c_bw {
            cmd_list.sum() with (item.dma_size) <= 4096;  // solver rejects
        }

    **Correct usage**::

        rand int dma_running[];
        constraint c_bw {
            dma_running.size() == cmd_list.size();
            foreach (cmd_list[i])
                dma_running[i] == (i == 0 ? cmd_list[i].dma_size
                                           : dma_running[i-1] + cmd_list[i].dma_size);
            dma_running[dma_running.size()-1] <= 4096;
        }

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_NO_STRUCT_SUM_WITH_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        struct_typedefs = self._collect_struct_typedef_names(data.tree)
        field_types = self._collect_field_type_map(data.tree)

        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for refNode in constraintNode.iter_find_all({"tag": "kReference"}):
                # The receiver is in the first kLocalRoot child of kReference
                ref_children = getattr(refNode, "children", [])
                if not ref_children:
                    continue
                first_child = ref_children[0]
                if getattr(first_child, "tag", "") != "kLocalRoot":
                    continue
                array_var = ""
                for unqId in first_child.iter_find_all({"tag": "kUnqualifiedId"}):
                    array_var = getattr(unqId, "text", "").strip()
                    break

                if not array_var:
                    continue

                field_type = field_types.get(array_var, "")
                if field_type not in struct_typedefs:
                    continue

                # Check if this reference uses sum()/product() with()
                for methodNode in refNode.iter_find_all(
                    {"tag": "kBuiltinArrayMethodCallExtension"}
                ):
                    method_name = ""
                    has_with = False
                    for child in getattr(methodNode, "children", []):
                        text = getattr(child, "text", "").strip()
                        tag = getattr(child, "tag", "")
                        if not method_name and text in ("sum", "product"):
                            method_name = text
                        if tag == "kArrayWithPredicate":
                            has_with = True
                    if method_name and has_with:
                        message = self.formatViolationMessage(
                            description=(
                                f"'{array_var}.{method_name}() with (...)' on "
                                f"struct-typed array (type '{field_type}') inside "
                                "a constraint block. Verilator generates a malformed "
                                "SMT query for struct arrays, causing randomize() "
                                "to return 0 silently."
                            ),
                            code_snippet=constraintNode.text,
                            fix_suggestion=(
                                "Use a prefix-sum helper array of plain integers "
                                "and accumulate the field values via foreach constraints."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
                        break

    def _collect_struct_typedef_names(self, tree):
        """Return set of typedef names that resolve to struct types in this file."""
        names = set()
        for typeDecl in tree.iter_find_all({"tag": "kTypeDeclaration"}):
            if not list(typeDecl.iter_find_all({"tag": "kStructType"})):
                continue
            for child in reversed(getattr(typeDecl, "children", [])):
                text = getattr(child, "text", "").strip()
                if text and text.isidentifier() and text not in (
                    "typedef", "struct", "union", "packed", ";"
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
