# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule

# 4-state types that must not be used with rand/randc (IEEE 1800 §18.4)
_FOURSTATE_TYPES = frozenset({"logic", "reg"})


class CnstRandNoLogic(AsFigoLintRule):
    """
    **CNST_RAND_TWO_STATE_ONLY** — ``rand`` and ``randc`` qualifiers must only
    be applied to 2-state variable types. Using them on 4-state types
    (``logic``, ``reg``) is prohibited by IEEE 1800-2017 §18.4.

    **Rationale**: The SV LRM explicitly states that ``rand``/``randc`` can
    only be used on integer variables with 2-state data types (``bit``,
    ``byte``, ``shortint``, ``int``, ``longint``). Applying them to ``logic``
    or ``reg`` (4-state types) is illegal. Tools that silently accept this
    may produce X or Z values in the randomised result, leading to downstream
    simulation failures that are difficult to trace back to the declaration.

    **Violation**::

        rand  logic [7:0] addr;    // violation: rand on 4-state logic
        randc logic [3:0] burst;   // violation: randc on 4-state logic
        rand  reg         strobe;  // violation: rand on 4-state reg

    **Correct usage**::

        rand  bit  [7:0] addr;    // OK: 2-state bit
        randc bit  [3:0] burst;   // OK: 2-state bit
        rand  byte       strobe;  // OK: 2-state byte

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_RAND_TWO_STATE_ONLY"

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for declNode in data.tree.iter_find_all({"tag": "kDataDeclaration"}):
            # Check for rand or randc qualifier
            rand_qual = None
            for qualNode in declNode.iter_find_all({"tag": "kQualifierList"}):
                for child in qualNode.children:
                    text = getattr(child, "text", "").strip()
                    if text in ("rand", "randc"):
                        rand_qual = text
                        break

            if rand_qual is None:
                continue

            # Check for a 4-state type primitive
            for typeNode in declNode.iter_find_all(
                {"tag": "kDataTypePrimitive"}
            ):
                for child in typeNode.children:
                    type_text = getattr(child, "text", "").strip()
                    if type_text in _FOURSTATE_TYPES:
                        message = self.formatViolationMessage(
                            description=(
                                f"'{rand_qual}' applied to 4-state type "
                                f"'{type_text}'. IEEE 1800 §18.4 restricts "
                                f"'{rand_qual}' to 2-state integer types "
                                "(bit, byte, shortint, int, longint). "
                                "Using 4-state types with rand/randc may "
                                "produce X/Z values in simulation."
                            ),
                            code_snippet=declNode.text,
                            fix_suggestion=(
                                f"Replace '{type_text}' with 'bit' or another "
                                "2-state type (byte, shortint, int, longint)."
                            ),
                        )
                        self.linter.logViolation(self.ruleID, message)
                        break  # one report per declaration
