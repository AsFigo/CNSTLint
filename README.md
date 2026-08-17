# CNSTLint

Linter for SystemVerilog Constraints. Following the philosophy of BYOL - Build Your Own Linter, CNSTLint is an example of how users can roll out their own linters!

**CNSTLint** is an open-source **minimalist** linter tool designed to enforce style and correctness rules for SystemVerilog constraint blocks. It provides a framework for **Build Your Own Linter** (**BYOL**), allowing users to create their own custom lint rules while benefiting from built-in checks such as operator precedence, soft constraint placement, distribution operator choice, missing casts, and other constraint best practices.

## BYOL - Build Your Own Linter

The core concept of **CNSTLint** is **BYOL** (Build Your Own Linter), a framework that lets you easily define custom linting rules tailored to your specific needs. **CNSTLint** is flexible and extensible.

## Open Source

This project is **open source** and licensed under the MIT License. Contributions are welcome, and you are free to fork, modify, and distribute it according to your needs.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AsFigo/cnstlint.git
cd cnstlint
```

2. Install required dependencies — Verible mainly

   See: https://github.com/chipsalliance/verible

3. `pip install anytree`
4. `pip install tomli`

## Usage

### Running the Linter from Command Line

```bash
# Single file
python bin/cnstlint.py -t <path_to_file.sv>

# Filelist
python bin/cnstlint.py -f <filelist.txt>

# Custom config
python bin/cnstlint.py -t <path_to_file.sv> -c <config.toml>
```

### Running the Regression Suite

```bash
python src/af_cnst_regr_runner.py
```

Results are saved to `regression_summary.log`.

## Test Cases

Test files follow the naming convention:

- `*_p.sv` — **pass** case: must produce **0 errors**
- `*_f.sv` — **fail** case: must produce **≥ 1 error**

## Adding New Lint Rules

1. Create a new Python file inside `src/rules/`. The class must inherit from `AsFigoLintRule`.
2. Set `self.ruleID` in `__init__`.
3. Implement `apply(self, filePath, data)` using CST traversal via `data.tree.iter_find_all({"tag": "..."})`.
4. Import the new class in `bin/cnstlint.py`.
5. Add `*_p.sv` and `*_f.sv` test cases in `tests/`.

## Built-in Rules

| Rule ID | File | Description |
|---------|------|-------------|
| `AF_CNST_NO_SOFT_FOREACH` | `af_cnst_no_soft_foreach.py` | Detects `soft` constraint inside `foreach` block |
| `FUNC_CNST_WRONG_OPER_PRE` | `af_func_cnst_wrong_oper_pre.py` | Mixed operator precedence (`==` with `?:`) in constraint expressions |
| `FUNC_CNST_MISSING_CAST` | `af_func_cnst_missing_cast.py` | `sum()` array reduction in a constraint missing explicit cast |
| `FUNC_CNST_DIST_COL_EQ` | `af_func_cnst_dist_col_eq.py` | Constant `dist` range using `:=` with a large span |
| `FUNC_CNST_DIST_COL_SL` | `af_func_cnst_dist_col_sl.py` | Interval `[a:b]` in `dist` should use `:/` instead of `:=` |

## Dependencies

- Python 3.x
- [Verible](https://github.com/chipsalliance/verible) — SystemVerilog parser from Google/ChipsAlliance
- `anytree`
- `tomli`

## License

This project is **open source** and licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

This **CNSTLint** linter is part of the **BYOL** (Build Your Own Linter) framework from **AsFigo Technologies**.
