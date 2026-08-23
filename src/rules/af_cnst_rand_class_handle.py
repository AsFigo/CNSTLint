# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

from af_lint_rule import AsFigoLintRule


class CnstRandClassHandleArray(AsFigoLintRule):
    """
    **CNST_RAND_CLASS_HANDLE_ARRAY_VLT** — A ``rand`` queue of class handles must
    be accompanied by a ``post_randomize()`` function that individually
    randomizes each element.

    **Rationale**: Declaring a queue of class handles as ``rand`` does NOT
    automatically randomize the handle objects themselves; it randomizes only
    the queue membership (which handles are in the queue). To randomize the
    fields of each pointed-to object, ``post_randomize()`` must explicitly
    call ``randomize()`` on every element. Omitting ``post_randomize()`` results
    in handles that reference un-randomized (default-initialized) objects,
    a common and silent correctness bug.

    **Violation**::

        class PacketGenerator;
            rand Packet queue_of_pkts[$];   // rand queue of handles
            constraint c_size { queue_of_pkts.size() == 5; }
            // No post_randomize -- violation
        endclass

    **Correct usage**::

        class PacketGenerator;
            rand Packet queue_of_pkts[$];
            constraint c_size { queue_of_pkts.size() == 5; }
            function void post_randomize();
                foreach (queue_of_pkts[i]) begin
                    queue_of_pkts[i] = new();
                    void'(queue_of_pkts[i].randomize());
                end
            endfunction
        endclass

    **Severity**: ERROR
    """

    def __init__(self, linter):
        self.linter = linter
        self.ruleID = "CNST_RAND_CLASS_HANDLE_ARRAY_VLT"

    def _has_rand_handle_queue(self, classNode):
        """
        Returns True if the class has a 'rand' declaration of a user-defined
        type that is a queue (unpacked dimension containing '$').
        """
        for declNode in classNode.iter_find_all({"tag": "kDataDeclaration"}):
            # Must have 'rand' qualifier
            is_rand = False
            for qualNode in declNode.iter_find_all({"tag": "kQualifierList"}):
                for child in qualNode.children:
                    if getattr(child, "text", "").strip() == "rand":
                        is_rand = True
            if not is_rand:
                continue

            # Type must be user-defined (kLocalRoot, not kDataTypePrimitive)
            has_user_type = bool(
                list(declNode.iter_find_all({"tag": "kLocalRoot"}))
            )
            if not has_user_type:
                continue

            # Must have an unpacked queue dimension: [$]
            for unpackNode in declNode.iter_find_all(
                {"tag": "kUnpackedDimensions"}
            ):
                for dimNode in unpackNode.iter_find_all(
                    {"tag": "kDimensionScalar"}
                ):
                    dim_text = getattr(dimNode, "text", "")
                    if "$" in dim_text:
                        return True
        return False

    def _has_post_randomize(self, classNode):
        """
        Returns True if the class contains a function named 'post_randomize'.
        """
        for funcNode in classNode.iter_find_all({"tag": "kFunctionDeclaration"}):
            for idNode in funcNode.iter_find_all({"tag": "kUnqualifiedId"}):
                for child in idNode.children:
                    if getattr(child, "text", "").strip() == "post_randomize":
                        return True
        return False

    def apply(
        self,
        filePath: str,
        data: AsFigoLintRule.VeribleSyntax.SyntaxData,
    ):
        for classNode in data.tree.iter_find_all({"tag": "kClassDeclaration"}):
            if not self._has_rand_handle_queue(classNode):
                continue

            if self._has_post_randomize(classNode):
                continue

            # Get class name for the message
            class_name = "unknown"
            for headerNode in classNode.iter_find_all({"tag": "kClassHeader"}):
                for child in headerNode.children:
                    tag = getattr(child, "tag", None)
                    if tag == "SymbolIdentifier" or (
                        tag is None and getattr(child, "text", "").strip()
                        not in ("class", ";", "")
                    ):
                        text = getattr(child, "text", "").strip()
                        if text and text not in ("class", ";"):
                            class_name = text
                            break

            message = self.formatViolationMessage(
                description=(
                    f"Class '{class_name}' declares a 'rand' queue of class "
                    "handles but does not define 'post_randomize()'. The "
                    "pointed-to objects will not be randomized automatically; "
                    "only the queue structure is randomized by the solver."
                ),
                code_snippet=classNode.text,
                fix_suggestion=(
                    "Add a 'function void post_randomize()' that iterates "
                    "the queue, calls 'new()' on each element, and then "
                    "calls '.randomize()' on each handle."
                ),
            )
            self.linter.logViolation(self.ruleID, message)
