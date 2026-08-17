// ----------------------------------------------------
// FAIL: Interval uses := instead of :/
// ----------------------------------------------------

class test_dist_range;

  rand byte bar;

  constraint c_bar_dist {
    bar dist {
      [0:99] := 5,
      100     := 95
    };
  }

endclass
