# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstNoEnumInWithClause(AsFigoLintRule):
    """
    **CNST_NO_ENUM_IN_WITH_CLAUSE_VLT** — Enum comparisons must not appear inside
    any ``with (...)`` clause used with array methods in a constraint block.

    **Rationale**: Comparing an enum-typed field or enum literal
    (e.g., ``item == WRITE``) inside any ``with (...)`` clause crashes the
    Verilator compiler with an internal compiler error (ICE). This is
    independent of whether the array holds a struct — it reproduces on a bare
    enum array too. There is no graceful diagnostic; the build simply fails.

    **Violation**::

        typedef enum bit { READ, WRITE } cmd_e;
        rand cmd_e cmd_list[];
        constraint c_bw {
            cmd_list.sum() with (item == WRITE ? 1 : 0) <= 10;  // ICE crash
        }

    **Correct usage**::

        rand int write_count;
        constraint c_bw {
            write_count == 0;
            foreach (cmd_list[i])
                if (cmd_list[i] == WRITE) write_count <= 10;
        }

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_NO_ENUM_IN_WITH_CLAUSE_VLT"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        # Collect all enum literal names from typedef enum declarations
        enum_literals = self._collect_enum_literal_names(data.tree)
        if not enum_literals:
            return

        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            for methodNode in constraintNode.iter_find_all(
                {"tag": "kBuiltinArrayMethodCallExtension"}
            ):
                for withNode in methodNode.iter_find_all(
                    {"tag": "kArrayWithPredicate"}
                ):
                    # Collect all identifiers inside the with() body
                    with_text = getattr(withNode, "text", "")
                    for literal in enum_literals:
                        if literal in with_text:
                            message = self.formatViolationMessage(
                                description=(
                                    f"Enum literal '{literal}' used inside "
                                    "a 'with (...)' clause in a constraint block. "
                                    "Verilator crashes with an internal compiler "
                                    "error when enum comparisons appear in "
                                    "array method 'with()' clauses."
                                ),
                                code_snippet=constraintNode.text,
                                fix_suggestion=(
                                    "Replace the 'with(item == ENUM_VAL ...)' "
                                    "pattern with a foreach constraint that "
                                    "conditionally accumulates via a helper "
                                    "rand int variable."
                                ),
                            )
                            self.linter.logViolation(self.ruleID, message)
                            break

    def _collect_enum_literal_names(self, tree):
        """Return set of all enum literal (enumerator) names in this file."""
        literals = set()
        for typeDecl in tree.iter_find_all({"tag": "kTypeDeclaration"}):
            for enumType in typeDecl.iter_find_all({"tag": "kEnumType"}):
                for enumName in enumType.iter_find_all({"tag": "kEnumName"}):
                    text = getattr(enumName, "text", "").strip()
                    if text and text.isidentifier():
                        literals.add(text)
        return literals
