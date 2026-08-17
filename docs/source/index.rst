CNSTLint — SystemVerilog Constraint Linter
==========================================

**CNSTLint** is an open-source linter for SystemVerilog constraint blocks,
developed by `AsFigo Technologies <https://asfigo.com>`_ as part of the
**BYOL** (Build Your Own Linter) framework.

It enforces best practices for ``rand``/``constraint`` constructs — covering
operator precedence, soft constraint placement, distribution operators, and
array reduction safety — helping verification teams catch constraint bugs
before simulation.

.. code-block:: bash

   python bin/cnstlint.py -t <your_file.sv>

----

.. toctree::
   :maxdepth: 2
   :caption: Rule Reference

   rules
