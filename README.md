# CNSTLint

**CNSTLint** is an open-source, minimalist linter designed to enforce correctness and style rules for SystemVerilog constraint blocks (`rand`, `constraint`).

Built on the philosophy of **BYOL** (**Build Your Own Linter**), CNSTLint demonstrates how verification engineers can roll out custom static analysis rules using Python and Google's [Verible](https://github.com/chipsalliance/verible) parser.

---

## Table of Contents

1. [BYOL - Build Your Own Linter](#byol---build-your-own-linter)
2. [Documentation](#documentation)
3. [Directory Structure](#directory-structure)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Adding New Lint Rules](#adding-new-lint-rules)
7. [Dependencies](#dependencies)
8. [License](#license)

---

## BYOL - Build Your Own Linter

The core concept of **CNSTLint** is **BYOL**, a framework that lets you easily define custom linting rules tailored to your team's SystemVerilog constraint standards. Whether detecting missing casts in `sum()`, flagging unsafe soft constraint placement, or enforcing distribution operator correctness, CNSTLint is lightweight and easily extensible.

---

## Documentation

Full rule reference and API documentation are hosted on GitHub Pages:
**[CNSTLint Documentation](https://asfigo.github.io/cnstlint/)**

---

## Directory Structure

```text
CNSTLint/
├── bin/
│   ├── cnstlint.py                        # Main executable CLI
│   └── verible_verilog_syntax.py          # Verible Python bindings
├── docs/                                  # Sphinx documentation source
├── examples/                              # Example pass/fail SV files
│   ├── Makefile
│   ├── cnst_operator_precedence_f.sv      # Violation example
│   └── cnst_operator_precedence_p.sv      # Compliant example
└── src/
    ├── af_lint_rule.py                    # Base rule class (AsFigoLintRule)
    ├── asfigo_linter.py                   # Core linter engine
    └── rules/                             # Constraint lint rules
        └── af_cnst_*.py / af_func_cnst_*.py
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AsFigo/cnstlint.git
   cd cnstlint
   ```

2. **Install Verible Parser:**
   CNSTLint requires Google's Verible parser binary (`verible-verilog-syntax`) in your executable path. Download it from the [Verible Releases](https://github.com/chipsalliance/verible/releases).

3. **Install Python dependencies:**
   ```bash
   pip install anytree tomli
   pip install -r docs/requirements.txt
   ```

---

## Usage

Run the linter against a SystemVerilog target file from your project root:

```bash
python3 bin/cnstlint.py -t examples/cnst_operator_precedence_f.sv
```

---

## Adding New Lint Rules

1. Create a new Python file inside `src/rules/` (e.g., `af_cnst_my_rule.py`).
2. Class structure should inherit from `AsFigoLintRule`:

```python
from af_lint_rule import AsFigoLintRule

class MyCustomRule(AsFigoLintRule):
    """AF_CNST_CUSTOM_001: Description of your custom rule."""

    def apply(self, filePath: str, data):
        # Rule check logic using Verible AST data
        pass
```

3. Add a corresponding entry in `docs/source/rules.rst` documenting the rule rationale, violation example, correct usage, and severity.

---

## Dependencies

* **Python**: 3.8+
* **Verible Parser**: [`verible-verilog-syntax`](https://github.com/chipsalliance/verible) executable
* **Python Packages**: `anytree`, `tomli`, `sphinx`, `furo` (for docs)

---

## License

This project is open-source and licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

This **CNSTLint** linter is part of the **BYOL** (Build Your Own Linter) framework from **AsFigo Technologies**.
