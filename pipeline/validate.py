from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
import jsonschema
from rich.console import Console
from rich.table import Table

console = Console()

SCHEMA_DIR = Path(__file__).parent.parent / "configs" / "schemas"

SCHEMA_MAP = {
    "templates": "template_schema.json",
    "policies": "policy_schema.json",
    "devices": "device_schema.json",
}


def _detect_config_type(file_path: Path) -> str | None:
    name = file_path.stem.lower()
    if "template" in name:
        return "templates"
    if "polic" in name:
        return "policies"
    if "device" in name:
        return "devices"
    return None


def validate_yaml_syntax(file_path: Path) -> list[str]:
    errors = []
    try:
        with open(file_path) as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error in {file_path.name}: {e}")
    return errors


def validate_schema(file_path: Path) -> list[str]:
    errors = []
    config_type = _detect_config_type(file_path)
    if not config_type:
        return [f"Cannot detect config type for {file_path.name} - skipping schema validation"]

    schema_file = SCHEMA_DIR / SCHEMA_MAP[config_type]
    if not schema_file.exists():
        return [f"Schema not found: {schema_file}"]

    with open(file_path) as f:
        data = yaml.safe_load(f)
    with open(schema_file) as f:
        schema = json.load(f)

    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(data):
        path = " -> ".join(str(p) for p in error.absolute_path) or "root"
        errors.append(f"[{file_path.name}] {path}: {error.message}")

    return errors


def validate_cross_references(config_dir: Path) -> list[str]:
    errors = []

    feature_template_names: set[str] = set()
    device_template_names: set[str] = set()

    for yaml_file in config_dir.rglob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f) or {}

        for ft in data.get("feature_templates", []):
            feature_template_names.add(ft["name"])

        for dt in data.get("device_templates", []):
            device_template_names.add(dt["name"])
            for ref in dt.get("feature_templates", []):
                if ref not in feature_template_names:
                    errors.append(f"Device template '{dt['name']}' references undefined feature template '{ref}'")

        for device in data.get("devices", []):
            ref = device.get("device_template", "")
            if ref and ref not in device_template_names:
                errors.append(f"Device '{device['hostname']}' references undefined device template '{ref}'")

    return errors


def run_validation(config_dir: Path) -> bool:
    config_dir = Path(config_dir)
    yaml_files = list(config_dir.rglob("*.yaml"))

    if not yaml_files:
        console.print("[yellow]No YAML files found[/yellow]")
        return True

    all_errors: list[str] = []

    table = Table(title="Validation Results")
    table.add_column("File", style="cyan")
    table.add_column("Check", style="magenta")
    table.add_column("Status")

    for f in yaml_files:
        syntax_errors = validate_yaml_syntax(f)
        status = "[red]FAIL[/red]" if syntax_errors else "[green]PASS[/green]"
        table.add_row(f.name, "YAML Syntax", status)
        all_errors.extend(syntax_errors)

        if not syntax_errors:
            schema_errors = validate_schema(f)
            status = "[red]FAIL[/red]" if schema_errors else "[green]PASS[/green]"
            table.add_row(f.name, "Schema", status)
            all_errors.extend(schema_errors)

    xref_errors = validate_cross_references(config_dir)
    status = "[red]FAIL[/red]" if xref_errors else "[green]PASS[/green]"
    table.add_row("(all)", "Cross-References", status)
    all_errors.extend(xref_errors)

    console.print(table)

    if all_errors:
        console.print(f"\n[red]Found {len(all_errors)} error(s):[/red]")
        for e in all_errors:
            console.print(f"  [red]x[/red] {e}")
        return False

    console.print("\n[green]All validations passed[/green]")
    return True


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs"
    success = run_validation(Path(config_path))
    sys.exit(0 if success else 1)
