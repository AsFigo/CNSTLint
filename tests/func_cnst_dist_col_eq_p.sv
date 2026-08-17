// Pass case: ranges are small (span <= 255) and use :/
// FUNC_CONST_DIST_COL_EQ  : no violation (range span < 255)
// FUNC_DIST_RANGE_SHOULD_USE_COLON_SLASH : no violation (:/ used)
class test_const_dist_col_eq;

  rand bit [7:0] field1;

  constraint c_dist {
    field1 dist {
      [0:31]  :/ 1,
      [32:63] :/ 1
    };
  }

endclass
