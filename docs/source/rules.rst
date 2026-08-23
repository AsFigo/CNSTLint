Lint Rules
==========

.. _AF_CNST_NO_SOFT_FOREACH:

AF_CNST_NO_SOFT_FOREACH
-----------------------

Soft constraint must not appear inside a foreach block.

**Rationale**: A ``soft`` constraint inside a ``foreach`` loop is evaluated
on a per-iteration basis. When the solver later applies a conflicting hard
constraint on any element, only that iteration's soft constraint is silently
discarded, which can produce unexpected distributions that are difficult to
trace. Placing soft constraints outside the foreach block makes the priority
relationship between hard and soft constraints explicit and predictable.

**Violation**::

    constraint c_bar_foreach {
        foreach (bar[i]) {
            soft bar[i] == 1'b1;  // soft inside foreach -- violation
        }
    }

**Correct usage**::

    constraint c_bar_default {
        soft bar == 8'hFF;        // soft outside foreach -- compliant
    }

    constraint c_bar_foreach {
        foreach (bar[i]) {
            bar[i] == 1'b1;       // hard constraint inside foreach -- compliant
        }
    }

**Severity**: ERROR

----

.. _FUNC_CNST_DIST_COL_EQ:

FUNC_CNST_DIST_COL_EQ
---------------------

Large constant distribution range must not use the ``:=`` operator.

**Rationale**: The ``:=`` operator assigns the same fixed weight to every
individual value in the range. For a large range (span > 255), this
effectively assigns equal probability to every value, which is rarely the
intent and can degrade solver performance. Use ``:/ `` (weight divided across
the range) for large ranges, reserving ``:=`` only for scalar values or small
ranges where per-value weighting is deliberate.

**Violation**::

    constraint c_dist {
        field1 dist {
          [32:65535] := 1  // span > 255 with := -- violation
        };
    }

**Correct usage**::

    constraint c_dist {
        field1 dist {
          [0:31]  :/ 1,   // small ranges with :/ -- compliant
          [32:63] :/ 1
        };
    }

**Severity**: ERROR

----

.. _FUNC_CNST_DIST_COL_SL:

FUNC_CNST_DIST_COL_SL
---------------------

Distribution range ``[a:b]`` must use ``:/`` rather than ``:=``.

**Rationale**: When a distribution item covers a range of values ``[a:b]``,
the ``:=`` operator assigns the stated weight to **every** value in the range
individually, so the total weight contributed by the range is
``weight × (b − a + 1)``. This is almost never the intent for a range entry.
The ``:/`` operator divides the stated weight across all values in the range,
which is the natural, expected behaviour and keeps the distribution
proportions correct. Use ``:=`` only on scalar values.

**Violation**::

    constraint c_bar_dist {
        bar dist {
          [0:99] := 5  // := on a range -- violation
        };
    }

**Correct usage**::

    constraint c_bar_dist {
        bar dist {
          [0:99] :/ 5  // :/ distributes weight across the range -- compliant
        };
    }

**Severity**: ERROR

----

.. _FUNC_CNST_MISSING_CAST:

FUNC_CNST_MISSING_CAST
----------------------

Array reduction ``sum()`` inside a constraint must use an explicit cast.

**Rationale**: The built-in array reduction method ``sum()`` returns a value
whose width equals the element width, not the accumulated result width. When
used in a constraint expression without a cast, the solver operates on a
narrower type than intended, which can silently truncate the sum and produce
incorrect randomisation results. An explicit cast (e.g. ``int'(...)``) makes
the intended bit-width visible to both the solver and the reader.

**Violation**::

    constraint c_sum {
        num_list.sum() == 1;      // no cast -- violation
    }

**Correct usage**::

    constraint c_sum {
        int'(num_list.sum()) == 1;  // explicit cast -- compliant
    }

**Severity**: ERROR

----

.. _FUNC_CNST_WRONG_OPER_PRE:

FUNC_CNST_WRONG_OPER_PRE
------------------------

Conditional ``?:`` mixed with ``==`` in a constraint must be parenthesised.

**Rationale**: SystemVerilog operator precedence places ``==`` above ``?:``
(conditional). Without explicit parentheses, the expression
``lhs == expr ? a : b`` is parsed as ``(lhs == expr) ? a : b`` — a
conditional whose condition is the equality check — rather than the likely
intent of ``lhs == (expr ? a : b)``. The misparse produces a constraint that
the solver satisfies in an unexpected way, and the bug is invisible at the
source level. Enclosing the conditional in parentheses makes the evaluation
order unambiguous and prevents the mismatch.

**Violation**::

    constraint foo_c {
        foo == (foo_select) ? 5 : 6;  // parsed as (foo == foo_select) ? 5 : 6
    }

**Correct usage**::

    constraint foo_c {
        foo == (foo_select ? 5 : 6);  // conditional explicitly parenthesised
    }

**Severity**: ERROR
