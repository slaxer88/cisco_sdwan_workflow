from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

from sdwan_client.auth import VManageAuth
from sdwan_client.templates import TemplateManager
from sdwan_client.policies import PolicyManager
from sdwan_client.devices import DeviceManager

console = Console()

FACTORY_PREFIXES = ("Factory_Default", "Default_")


def _is_factory_default(name: str) -> bool:
    return any(name.startswith(p) for p in FACTORY_PREFIXES)


def _yaml_dump(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
    console.print(f"  [green]Wrote[/green] {path}")


def export_feature_templates(tm: TemplateManager, output_dir: Path, include_factory: bool = False) -> list[dict]:
    raw = tm.list_feature_templates()
    templates = []

    for t in raw:
        name = t.get("templateName", "")
        if not include_factory and _is_factory_default(name):
            continue

        detail = {}
        try:
            detail = tm.get_feature_template(t["templateId"])
        except Exception:
            pass

        templates.append(
            {
                "name": name,
                "description": t.get("templateDescription", ""),
                "template_type": t.get("templateType", ""),
                "device_type": t.get("deviceType", []),
                "template_id": t.get("templateId", ""),
                "definition": detail.get("templateDefinition", {}),
            }
        )

    result = {"feature_templates": templates}
    _yaml_dump(result, output_dir / "templates" / "feature_templates.yaml")
    return templates


def export_device_templates(
    tm: TemplateManager,
    output_dir: Path,
    include_factory: bool = False,
    id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    raw = tm.list_device_templates()
    templates = []
    name_map = id_to_name or {}

    for t in raw:
        name = t.get("templateName", "")
        if not include_factory and _is_factory_default(name):
            continue

        sub_templates = []
        try:
            detail = tm.get_device_template(t["templateId"])
            for gt in detail.get("generalTemplates", []):
                tid = gt.get("templateId", "")
                resolved = name_map.get(tid, gt.get("templateName", tid))
                entry = {"name": resolved, "type": gt.get("templateType", "")}
                subs = gt.get("subTemplates", [])
                if subs:
                    entry["sub_templates"] = [
                        {
                            "name": name_map.get(
                                s.get("templateId", ""), s.get("templateName", s.get("templateId", ""))
                            ),
                            "type": s.get("templateType", ""),
                        }
                        for s in subs
                    ]
                sub_templates.append(entry)
        except Exception:
            pass

        templates.append(
            {
                "name": name,
                "description": t.get("templateDescription", ""),
                "device_type": t.get("deviceType", ""),
                "template_id": t.get("templateId", ""),
                "devices_attached": t.get("devicesAttached", 0),
                "feature_templates": sub_templates,
            }
        )

    result = {"device_templates": templates}
    _yaml_dump(result, output_dir / "templates" / "device_templates.yaml")
    return templates


def export_policies(pm: PolicyManager, output_dir: Path) -> dict:
    centralized = []
    for p in pm.list_centralized_policies():
        detail = {}
        try:
            detail = pm.get_centralized_policy(p["policyId"])
        except Exception:
            pass

        centralized.append(
            {
                "name": p.get("policyName", ""),
                "description": p.get("policyDescription", ""),
                "policy_id": p.get("policyId", ""),
                "policy_type": p.get("policyType", ""),
                "is_activated": p.get("isPolicyActivated", False),
                "definition": detail.get("policyDefinition", {}),
            }
        )

    policy_lists = {}
    for list_type in ("site", "vpn", "prefix", "tloc", "sla", "app", "color", "dataprefixall"):
        try:
            items = pm.list_policy_lists(list_type)
            if items:
                policy_lists[list_type] = [
                    {
                        "name": item.get("name", ""),
                        "list_id": item.get("listId", ""),
                        "entries": item.get("entries", []),
                    }
                    for item in items
                ]
        except Exception:
            pass

    result = {"centralized_policies": centralized, "policy_lists": policy_lists}
    _yaml_dump(result, output_dir / "policies" / "centralized_policies.yaml")
    return result


def export_devices(dm: DeviceManager, output_dir: Path) -> list[dict]:
    raw = dm.list_devices()
    devices = []

    for d in raw:
        devices.append(
            {
                "hostname": d.get("host-name", ""),
                "device_id": d.get("deviceId", ""),
                "device_type": d.get("device-type", ""),
                "system_ip": d.get("system-ip", ""),
                "site_id": str(d.get("site-id", "")),
                "reachability": d.get("reachability", ""),
                "version": d.get("version", ""),
                "template": d.get("template", ""),
            }
        )

    result = {"devices": devices}
    _yaml_dump(result, output_dir / "devices" / "inventory.yaml")
    return devices


def run_export(client: VManageAuth, output_dir: Path, include_factory: bool = False) -> None:
    console.print("[bold]Exporting vManage configuration...[/bold]\n")

    tm = TemplateManager(client)
    pm = PolicyManager(client)
    dm = DeviceManager(client)

    console.print("[bold]1. Feature Templates[/bold]")
    ft = export_feature_templates(tm, output_dir, include_factory)
    console.print(f"   Exported {len(ft)} feature templates\n")

    all_ft_raw = tm.list_feature_templates()
    id_to_name = {t["templateId"]: t["templateName"] for t in all_ft_raw}

    console.print("[bold]2. Device Templates[/bold]")
    dt = export_device_templates(tm, output_dir, include_factory, id_to_name=id_to_name)
    console.print(f"   Exported {len(dt)} device templates\n")

    console.print("[bold]3. Policies[/bold]")
    pol = export_policies(pm, output_dir)
    console.print(f"   Exported {len(pol.get('centralized_policies', []))} centralized policies")
    console.print(f"   Exported {sum(len(v) for v in pol.get('policy_lists', {}).values())} policy lists\n")

    console.print("[bold]4. Device Inventory[/bold]")
    devs = export_devices(dm, output_dir)
    console.print(f"   Exported {len(devs)} devices\n")

    table = Table(title="Export Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Output File")
    table.add_row("Feature Templates", str(len(ft)), "templates/feature_templates.yaml")
    table.add_row("Device Templates", str(len(dt)), "templates/device_templates.yaml")
    table.add_row(
        "Centralized Policies", str(len(pol.get("centralized_policies", []))), "policies/centralized_policies.yaml"
    )
    table.add_row("Devices", str(len(devs)), "devices/inventory.yaml")
    console.print(table)

    console.print(f"\n[green]Export complete -> {output_dir}/[/green]")
