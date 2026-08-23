# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule

_ALLOWED_PREFIXES = ("cnst_", "cst_")
_ALLOWED_SUFFIXES = ("_cnst", "_cst")


class CnstNameConvention(AsFigoLintRule):
    """
    **CNST_NAME_CONVENTION** — Every constraint block name must carry an
    approved prefix (``cnst_``, ``cst_``) or suffix (``_cnst``, ``_cst``).

    **Rationale**: A consistent naming convention makes constraint blocks
    instantly discoverable by engineers and tooling alike. Bare names such
    as ``c_range`` or ``check_valid`` are ambiguous — they blend into other
    identifiers and are easy to miss during code review or coverage analysis.

    **Violation**::

        constraint c_length  { length  inside {[1:128]}; }  // violation
        constraint c_payload { payload inside {[0:255]}; }  // violation

    **Correct usage**::

        constraint cnst_length  { length  inside {[1:128]}; }  // cnst_ prefix
        constraint cst_payload  { payload inside {[0:255]}; }  // cst_ prefix
        constraint flags_cnst   { flags   inside {[0:15]};  }  // _cnst suffix
        constraint version_cst  { version inside {[1:3]};   }  // _cst suffix

    **Severity**: WARNING
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_NAME_CONVENTION"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for constraintNode in data.tree.iter_find_all(
            {"tag": "kConstraintDeclaration"}
        ):
            # The constraint name is the SymbolIdentifier leaf in the
            # direct children of kConstraintDeclaration (slot @2).
            for child in constraintNode.children:
                if getattr(child, "tag", None) != "SymbolIdentifier":
                    continue

                name = getattr(child, "text", "").strip()
                if not name:
                    continue

                compliant = (
                    name.startswith(_ALLOWED_PREFIXES)
                    or name.endswith(_ALLOWED_SUFFIXES)
                )

                if not compliant:
                    message = self.formatViolationMessage(
                        description=(
                            f"Constraint name '{name}' does not follow the "
                            "naming convention. Names must start with "
                            "'cnst_' or 'cst_', or end with '_cnst' or '_cst'."
                        ),
                        code_snippet=f"constraint {name} {{ ... }}",
                        fix_suggestion=(
                            f"Rename to 'cnst_{name}', 'cst_{name}', "
                            f"'{name}_cnst', or '{name}_cst'."
                        ),
                    )
                    self.linter.logViolation(self.ruleID, message)
                break  # only the first SymbolIdentifier child is the name
