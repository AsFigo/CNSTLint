from pathlib import Path

RULES_DIR = Path("../src/rules")
OUTPUT_FILE = Path("source/rules.rst")

# Gather all constraint rule files (all filenames containing 'cnst')
rule_files = sorted(
    [
        f.stem
        for f in RULES_DIR.glob("*.py")
        if "cnst" in f.stem
    ]
)

lines = ["Lint Rules", "==========", ""]

for rule in rule_files:
    lines.append(rule)
    lines.append("-" * len(rule))
    lines.append(f".. automodule:: rules.{rule}")
    lines.append("")

OUTPUT_FILE.write_text("\n".join(lines))
print(f"Generated {OUTPUT_FILE} with {len(rule_files)} rules.")
