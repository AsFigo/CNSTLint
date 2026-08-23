// ----------------------------------------------------
// SPDX-FileCopyrightText: AsFigo Technologies, UK
// SPDX-FileCopyrightText: VerifWorks, India
// SPDX-License-Identifier: MIT
// ----------------------------------------------------

class foo_class;

    bit foo_select;
    rand int foo;

    constraint foo_cnst {
        foo == (foo_select ? 5 : 6);
    }

endclass
