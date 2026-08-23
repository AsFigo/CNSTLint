# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstRandModeLeftover(AsFigoLintRule):
    """
    **CNST_RAND_MODE_LEFTOVER_VLT** — ``this.rand_mode(0)`` in the constructor
    disables all ``rand`` fields; any field not subsequently re-enabled with
    ``field.rand_mode(1)`` is silently pinned to its default value forever.

    **Rationale**: ``this.rand_mode(0)`` is a bulk disable. Developers often
    add it to isolate one field, re-enable that field, then forget to remove
    the bulk disable. The remaining ``rand`` fields still appear in declarations
    and dumps but never vary across ``randomize()`` calls — no error is emitted.

    **Violation**::

        function new();
            this.rand_mode(0);         // disables BOTH seq_num and channel
            this.channel.rand_mode(1); // re-enables channel only
            // seq_num silently pinned to 0
        endfunction

    **Correct usage**::

        function new();
            // No leftover rand_mode(0) -- both fields randomize freely
        endfunction

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_RAND_MODE_LEFTOVER_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for classNode in data.tree.iter_find_all({"tag": "kClassDeclaration"}):
            # Collect rand/randc field names from direct class items
            rand_fields = set()
            for classItems in classNode.iter_find_all({"tag": "kClassItems"}):
                for child in getattr(classItems, "children", []):
                    if getattr(child, "tag", "") != "kDataDeclaration":
                        continue
                    for qualNode in child.iter_find_all({"tag": "kQualifierList"}):
                        if getattr(qualNode, "text", "").strip() not in (
                            "rand", "randc"
                        ):
                            break
                        for varAssign in child.iter_find_all(
                            {"tag": "kVariableDeclarationAssignment"}
                        ):
                            va_ch = getattr(varAssign, "children", [])
                            if va_ch:
                                fname = getattr(va_ch[0], "text", "").strip()
                                if fname and fname.isidentifier():
                                    rand_fields.add(fname)
                break  # only first kClassItems

            if not rand_fields:
                continue

            # Inspect constructor
            for ctorNode in classNode.iter_find_all({"tag": "kClassConstructor"}):
                has_global_disable = False
                re_enabled = set()

                for stmtNode in ctorNode.iter_find_all({"tag": "kStatement"}):
                    for refCallNode in stmtNode.iter_find_all(
                        {"tag": "kReferenceCallBase"}
                    ):
                        ref_node = None
                        paren_node = None
                        for child in getattr(refCallNode, "children", []):
                            tag = getattr(child, "tag", "")
                            if tag == "kReference":
                                ref_node = child
                            elif tag == "kParenGroup":
                                paren_node = child

                        if ref_node is None:
                            continue

                        ref_ch = getattr(ref_node, "children", [])
                        if not ref_ch:
                            continue

                        # Root must be 'this'
                        root_text = getattr(ref_ch[0], "text", "").strip()
                        if root_text != "this":
                            continue

                        hier_exts = [
                            c for c in ref_ch
                            if getattr(c, "tag", "") == "kHierarchyExtension"
                        ]
                        if not hier_exts:
                            continue

                        # Method name is in the last hierarchy extension
                        last_method = (
                            getattr(hier_exts[-1], "text", "")
                            .strip()
                            .lstrip(".")
                        )
                        if last_method != "rand_mode":
                            continue

                        # Get the argument (0 or 1)
                        arg_text = ""
                        if paren_node is not None:
                            for argList in paren_node.iter_find_all(
                                {"tag": "kArgumentList"}
                            ):
                                arg_text = getattr(argList, "text", "").strip()
                                break

                        if len(hier_exts) == 1:
                            # this.rand_mode(x)
                            if arg_text == "0":
                                has_global_disable = True
                        elif len(hier_exts) == 2:
                            # this.<field>.rand_mode(x)
                            field = (
                                getattr(hier_exts[0], "text", "")
                                .strip()
                                .lstrip(".")
                            )
                            if arg_text == "1" and field in rand_fields:
                                re_enabled.add(field)

                if has_global_disable:
                    not_re_enabled = rand_fields - re_enabled
                    if not_re_enabled:
                        missing = ", ".join(sorted(not_re_enabled))
                        message = self.formatViolationMessage(
                            description=(
                                f"'this.rand_mode(0)' disables all rand fields, "
                                f"but [{missing}] are never re-enabled. "
                                "Those fields are silently pinned to their "
                                "default (usually 0) across all randomize() calls."
                            ),
                            code_snippet=ctorNode.text,
                            fix_suggestion=(
                                "Remove 'this.rand_mode(0)' entirely, or "
                                f"add '{missing}.rand_mode(1)' for each "
                                "field that must remain randomizable."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
