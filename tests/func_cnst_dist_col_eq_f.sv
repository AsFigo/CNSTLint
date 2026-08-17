class test_const_dist_col_eq;

  rand bit [15:0] field1;

  constraint c_dist {
    field1 dist {
      [0:31]     := 1,
      [32:65535] := 1
    };
  }

endclass
