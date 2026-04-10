from pathlib import Path

import pytest
import yaml

CONFIG_DIR = Path(__file__).parent.parent / "configs"


def test_all_yaml_files_parse():
    for f in CONFIG_DIR.rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh)
        assert data is not None, f"{f.name} parsed to None"


def test_template_names_are_uppercase():
    for f in (CONFIG_DIR / "templates").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for tpl in data.get("feature_templates", []):
            name = tpl["name"]
            assert name == name.upper().replace(" ", "-"), f"Template name '{name}' must be UPPER-KEBAB-CASE"


def test_device_site_ids_unique():
    site_ids = []
    for f in (CONFIG_DIR / "devices").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for device in data.get("devices", []):
            site_ids.append(device["site_id"])

    assert len(site_ids) == len(set(site_ids)), f"Duplicate site_ids found: {site_ids}"


def test_device_system_ips_unique():
    ips = []
    for f in (CONFIG_DIR / "devices").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for device in data.get("devices", []):
            ips.append(device["system_ip"])

    assert len(ips) == len(set(ips)), f"Duplicate system_ips found: {ips}"


def test_device_templates_reference_exists():
    template_names = set()
    for f in (CONFIG_DIR / "templates").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for dt in data.get("device_templates", []):
            template_names.add(dt["name"])

    for f in (CONFIG_DIR / "devices").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for device in data.get("devices", []):
            ref = device.get("device_template", "")
            assert ref in template_names, (
                f"Device '{device['hostname']}' references template '{ref}' which doesn't exist"
            )


def test_policy_sla_classes_have_required_fields():
    for f in (CONFIG_DIR / "policies").rglob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
        for sla in data.get("policy_lists", {}).get("sla_classes", []):
            assert "name" in sla, f"SLA class missing 'name'"
            assert "latency" in sla, f"SLA class '{sla.get('name')}' missing 'latency'"
            assert "loss" in sla, f"SLA class '{sla.get('name')}' missing 'loss'"
