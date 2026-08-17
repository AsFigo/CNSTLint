class foo_class;

    bit foo_select;
    rand int foo;

    constraint foo_c {
        foo == (foo_select ? 5 : 6);
    }

endclass
