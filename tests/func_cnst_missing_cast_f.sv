// FUNC_CNST_MISSING_CAST
// Array reduction method sum() inside a constraint must use an explicit cast.

class bug_c;

  rand bit num_list[32];

  constraint c_sum {
    // VIOLATION: sum() result is used without an explicit cast
    num_list.sum() == 1;
  }

endclass
