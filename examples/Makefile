# ----------------------------------------------------
# SPDX-FileCopyrightText: AsFigo Technologies, UK
# SPDX-FileCopyrightText: VerifWorks, India
# SPDX-License-Identifier: MIT
# ----------------------------------------------------

CNSTLINT = python3 ../bin/cnstlint.py

all: run_f run_p

run_f:
	$(CNSTLINT) -t cnst_operator_precedence_f.sv

run_p:
	$(CNSTLINT) -t cnst_operator_precedence_p.sv
