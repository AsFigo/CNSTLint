class soft_foreach_fail;

    rand bit [7:0] bar;

    constraint c_bar_default {
        soft bar == 8'hFF;
    }

    constraint c_bar_foreach {
        foreach (bar[i]) {
            soft bar[i] == 1'b1;
        }
    }

    constraint c_bar_hard {
        bar[0] == 1'b0;
    }

endclass
