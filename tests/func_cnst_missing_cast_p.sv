// FUNC_CNST_MISSING_CAST
// Valid use of an explicit cast around the array reduction result.

class good_c;

  rand bit num_list[32];

  constraint c_sum {
    // PASS: explicit cast is used
    int'(num_list.sum()) == 1;
  }

endclass
