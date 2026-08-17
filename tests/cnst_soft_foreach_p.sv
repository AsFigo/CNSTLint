class soft_foreach_pass;

    rand bit [7:0] bar;

    // Soft constraint is outside foreach - compliant
    constraint c_bar_default {
        soft bar == 8'hFF;
    }

    // Hard constraint inside foreach - compliant
    constraint c_bar_foreach {
        foreach (bar[i]) {
            bar[i] == 1'b1;
        }
    }

    constraint c_bar_hard {
        bar[0] == 1'b0;
    }

endclass
