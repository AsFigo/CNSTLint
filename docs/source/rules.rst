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

----

.. _CNST_ADDITIVE_OVERFLOW_IN_BOUND_VLT:

CNST_ADDITIVE_OVERFLOW_IN_BOUND_VLT
------------------------------------

Inside a constraint, ``A + B <= MAX`` where ``MAX`` is near the operand type maximum can silently pass when the true sum overflows and wraps to a small value.

**Rationale**: SV constraint addition is performed in the operand's native width without automatic promotion. When ``p_start_addr + page_size`` approaches or exceeds ``2^32``, the result wraps (e.g., ``0xFFFF0000 + 0x20000 == 0x10000`` in 32 bits). The wrapped value satisfies ``<= 32'hFFFF_FFFF`` while the physical address is actually out of bounds. Rearrange to subtract on the RHS to avoid the addition entirely.

**Violation**::

    constraint c_bound {
        p_start_addr + page_size <= 32'hFFFF_FFFF;  // can wrap silently
    }

**Correct usage**::

    constraint c_bound {
        p_start_addr <= 32'hFFFF_FFFF - page_size;  // no addition, no overflow
    }

**Severity**: WARNING

----

.. _CNST_DIST_NO_SOLVE_BEFORE_VLT:

CNST_DIST_NO_SOLVE_BEFORE_VLT
------------------------------

A ``rand`` variable that has a ``dist{}`` constraint and also controls an implication (``->``) constraint on other ``rand`` variables requires a ``solve <var> before <others>`` directive.

**Rationale**: Without ``solve ... before``, the solver may evaluate all constraints simultaneously, failing to honour the ``dist{}`` weights and allowing the implication antecedent to see an unsettled value. The ``solve ... before`` directive explicitly sequences two-phase resolution: pick the ``dist``-weighted variable first, then solve the conditional constraints.

**Violation**::

    constraint c_dist   { qos_mode dist { BURST_MODE := 70, SPARSE_MODE := 30 }; }
    constraint c_burst  { qos_mode == BURST_MODE -> dma_grid[0][0] > 100; }
    // Missing: constraint c_order { solve qos_mode before dma_grid; }

**Correct usage**::

    constraint c_order  { solve qos_mode before dma_grid; }
    constraint c_dist   { qos_mode dist { BURST_MODE := 70, SPARSE_MODE := 30 }; }
    constraint c_burst  { qos_mode == BURST_MODE -> dma_grid[0][0] > 100; }

**Severity**: WARNING

----

.. _CNST_DIST_ON_ENUM_TYPE_VLT:

CNST_DIST_ON_ENUM_TYPE_VLT
---------------------------

A ``dist{}`` expression applied to a ``rand`` field of enum type does not reproduce the declared weights reliably in Verilator.

**Rationale**: Confirmed over 2000 trials: a ``rand enum`` field with ``dist {A:=20, B:=50, C:=30}`` lands nowhere near those weights (observed 25/28/47 instead of 20/50/30). The fix is to drive the weighted pick through a plain ``rand bit [N:0]`` field and map it onto the enum afterward with implication constraints.

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

----

.. _CNST_FOREACH_UNGUARDED_PREV_IDX_VLT:

CNST_FOREACH_UNGUARDED_PREV_IDX_VLT
-------------------------------------

Inside a ``foreach`` constraint, accessing ``arr[i-1]`` without an enclosing ``if (i > 0)`` guard causes silent unsigned wraparound to the maximum index value when ``i == 0``.

**Rationale**: The ``foreach`` loop variable is unsigned in Verilator and most simulators. When ``i == 0``, the expression ``i-1`` wraps to the largest representable unsigned value, silently accessing the wrong array element rather than being skipped.

**Violation**::

    constraint c_no_overlap {
        foreach (regions[i])
            regions[i].base_addr > regions[i-1].limit_addr;  // wraps at i==0
    }

**Correct usage**::

    constraint c_no_overlap {
        foreach (regions[i])
            if (i > 0)
                regions[i].base_addr > regions[i-1].limit_addr;
    }

**Severity**: ERROR

----

.. _CNST_NAME_CONVENTION:

CNST_NAME_CONVENTION
--------------------

Every constraint block name must carry an approved prefix (``cnst_``, ``cst_``) or suffix (``_cnst``, ``_cst``).

**Rationale**: A consistent naming convention makes constraint blocks instantly discoverable by engineers and tooling alike. Bare names such as ``c_range`` or ``check_valid`` are ambiguous and easy to miss during code review or coverage analysis.

**Violation**::

    constraint c_length  { length  inside {[1:128]}; }  // violation
    constraint c_payload { payload inside {[0:255]}; }  // violation

**Correct usage**::

    constraint cnst_length  { length  inside {[1:128]}; }  // cnst_ prefix
    constraint cst_payload  { payload inside {[0:255]}; }  // cst_ prefix
    constraint flags_cnst   { flags   inside {[0:15]};  }  // _cnst suffix
    constraint version_cst  { version inside {[1:3]};   }  // _cst suffix

**Severity**: WARNING

----

.. _CNST_NO_ENUM_IN_WITH_CLAUSE_VLT:

CNST_NO_ENUM_IN_WITH_CLAUSE_VLT
--------------------------------

Enum comparisons must not appear inside any ``with (...)`` clause used with array methods in a constraint block.

**Rationale**: Comparing an enum-typed field or enum literal (e.g., ``item == WRITE``) inside any ``with (...)`` clause crashes the Verilator compiler with an internal compiler error (ICE). There is no graceful diagnostic; the build simply fails.

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

----

.. _CNST_NO_LOCATOR_IN_CONSTRAINT_VLT:

CNST_NO_LOCATOR_IN_CONSTRAINT_VLT
----------------------------------

Array locator methods must not appear inside constraint blocks.

**Rationale**: Array locator methods (``find``, ``find_first``, ``find_last``, ``find_index``, ``find_first_index``, ``find_last_index``, ``min``, ``max``) are iterative query functions. Using them inside constraint blocks couples the solver to imperative iteration semantics, which most constraint solvers and formal tools do not support.

**Violation**::

    constraint c_no_flush {
        cmd_list.find() with (item != 8'hFF);  // locator in constraint -- violation
    }

**Correct usage**::

    function void post_randomize();
        // Perform locator-style filtering in procedural code
        filtered = cmd_list.find() with (item != 8'hFF);
    endfunction

**Severity**: ERROR

----

.. _CNST_NO_STRUCT_SUM_WITH_VLT:

CNST_NO_STRUCT_SUM_WITH_VLT
----------------------------

``sum() with (...)`` on a struct-typed array must not appear inside a constraint block.

**Rationale**: For any struct-typed array, ``array.sum() with (expr)`` generates a malformed SMT query that the solver rejects. ``randomize()`` returns 0 (failure) even though the constraint is syntactically valid. Use a prefix-sum helper array of plain integers instead.

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

----

.. _CNST_RAND_CLASS_HANDLE_ARRAY_VLT:

CNST_RAND_CLASS_HANDLE_ARRAY_VLT
---------------------------------

A ``rand`` queue of class handles must be accompanied by a ``post_randomize()`` function that individually randomizes each element.

**Rationale**: Declaring a queue of class handles as ``rand`` does NOT automatically randomize the handle objects themselves; it randomizes only the queue membership. To randomize the fields of each pointed-to object, ``post_randomize()`` must explicitly call ``randomize()`` on every element. Omitting it results in handles that reference un-randomized (default-initialized) objects.

**Violation**::

    class PacketGenerator;
        rand Packet queue_of_pkts[$];
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

----

.. _CNST_RAND_MODE_LEFTOVER_VLT:

CNST_RAND_MODE_LEFTOVER_VLT
----------------------------

``this.rand_mode(0)`` in the constructor disables all ``rand`` fields; any field not subsequently re-enabled with ``field.rand_mode(1)`` is silently pinned to its default value forever.

**Rationale**: ``this.rand_mode(0)`` is a bulk disable. Developers often add it to isolate one field, re-enable that field, then forget to remove the bulk disable. The remaining ``rand`` fields never vary across ``randomize()`` calls with no error emitted.

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

----

.. _CNST_RAND_TWO_STATE_ONLY:

CNST_RAND_TWO_STATE_ONLY
------------------------

``rand`` and ``randc`` qualifiers must only be applied to 2-state variable types. Using them on 4-state types (``logic``, ``reg``) is prohibited by IEEE 1800-2017 §18.4.

**Rationale**: The SV LRM explicitly states that ``rand``/``randc`` can only be used on integer variables with 2-state data types. Applying them to ``logic`` or ``reg`` is illegal. Tools that silently accept this may produce X or Z values in the randomised result.

**Violation**::

    rand  logic [7:0] addr;    // violation: rand on 4-state logic
    randc logic [3:0] burst;   // violation: randc on 4-state logic
    rand  reg         strobe;  // violation: rand on 4-state reg

**Correct usage**::

    rand  bit  [7:0] addr;    // OK: 2-state bit
    randc bit  [3:0] burst;   // OK: 2-state bit
    rand  byte       strobe;  // OK: 2-state byte

**Severity**: ERROR

----

.. _CNST_RANDC_DYNAMIC_EXCLUSION_VLT:

CNST_RANDC_DYNAMIC_EXCLUSION_VLT
---------------------------------

A ``randc`` variable must not be constrained with ``inside { dynamic_variable }`` to exclude already-used values.

**Rationale**: ``randc`` variables cycle through all legal values before repeating. Pairing ``randc`` with an ``inside { queue }`` exclusion constraint creates conflicting semantics: the solver must simultaneously guarantee cycling AND enforce a runtime exclusion set, leading to solver failures or undefined behaviour.

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
            used_ids_q.push_back(id);
        endfunction
    endclass

**Severity**: ERROR

----

.. _CNST_SUM_WITH_NARROW_NO_CAST_VLT:

CNST_SUM_WITH_NARROW_NO_CAST_VLT
---------------------------------

A ``sum()`` with predicate must cast each element to avoid silent narrow-integer truncation.

**Rationale**: When ``sum()`` is applied to an array of narrow types (e.g., ``bit``, ``byte``), the accumulator has the same width as the element type. Summing many narrow elements without an explicit cast causes silent overflow. Cast the iterator variable inside the ``with`` clause to a wider type (e.g., ``int``).

**Violation**::

    constraint c_hamming {
        changed_bits.sum() with (item) == toggle_target;  // no cast -- violation
    }

**Correct usage**::

    constraint c_hamming {
        changed_bits.sum() with (int'(item)) == toggle_target;  // cast present
    }

**Severity**: ERROR

----

.. _CNST_UNIQUE_LARGE_ARRAY_VLT:

CNST_UNIQUE_LARGE_ARRAY_VLT
----------------------------

``unique{}`` applied to an unpacked array with more than 4 elements is silently unreliable in Verilator.

**Rationale**: Verilator's ``unique{}`` implementation does not scale correctly for arrays larger than approximately 4 elements. ``randomize()`` returns 1 (success) while the result may contain duplicate values. Use pairwise ``!=`` constraints instead.

**Violation**::

    rand bit [7:0] vals[8];
    constraint c_u { unique {vals}; }  // silently wrong for 8 elements

**Correct usage**::

    constraint c_u {
        foreach (vals[i])
            foreach (vals[j])
                if (i != j) vals[i] != vals[j];
    }

**Severity**: WARNING

----

.. _CNST_UNIQUE_MDA_ROW_SLICE_VLT:

CNST_UNIQUE_MDA_ROW_SLICE_VLT
------------------------------

The ``unique`` constraint must not operate on a single row slice of a multi-dimensional array selected by an index variable.

**Rationale**: Using ``unique { array[i] }`` inside a ``foreach`` loop constrains only the elements of a single row at a time. Uniqueness is enforced per-row but NOT across rows, leading to a weaker constraint than intended.

**Violation**::

    constraint c_row_unique {
        foreach (core_power[i]) {
            unique { core_power[i] };  // only row i is unique -- violation
        }
    }

**Correct usage**::

    constraint c_all_unique {
        unique { core_power };   // unique across all elements
    }

**Severity**: ERROR
