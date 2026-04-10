from __future__ import annotations

import sys
from pathlib import Path

import yaml
from deepdiff import DeepDiff
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def load_all_configs(config_dir: Path) -> dict:
    merged = {}
    for yaml_file in sorted(config_dir.rglob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f) or {}
        for key, value in data.items():
            if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key].extend(value)
            else:
                merged[key] = value
    return merged


def fetch_remote_state(client) -> dict:
    from sdwan_client.templates import TemplateManager
    from sdwan_client.policies import PolicyManager

    remote = {
        "feature_templates": [],
        "device_templates": [],
        "centralized_policies": [],
    }

    tm = TemplateManager(client)
    for t in tm.list_feature_templates():
        remote["feature_templates"].append(
            {
                "name": t.get("templateName", ""),
                "template_type": t.get("templateType", ""),
                "description": t.get("templateDescription", ""),
            }
        )

    for t in tm.list_device_templates():
        remote["device_templates"].append(
            {
                "name": t.get("templateName", ""),
                "device_type": t.get("deviceType", ""),
                "description": t.get("templateDescription", ""),
            }
        )

    pm = PolicyManager(client)
    for p in pm.list_centralized_policies():
        remote["centralized_policies"].append(
            {
                "name": p.get("policyName", ""),
                "description": p.get("policyDescription", ""),
            }
        )

    return remote


def compute_diff(local: dict, remote: dict) -> dict:
    plan = {"create": [], "update": [], "delete": [], "unchanged": []}

    local_names = {
        item["name"]
        for items in local.values()
        if isinstance(items, list)
        for item in items
        if isinstance(item, dict) and "name" in item
    }
    remote_names = {
        item["name"]
        for items in remote.values()
        if isinstance(items, list)
        for item in items
        if isinstance(item, dict) and "name" in item
    }

    local_by_name = {}
    for items in local.values():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    local_by_name[item["name"]] = item

    remote_by_name = {}
    for items in remote.values():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    remote_by_name[item["name"]] = item

    for name in local_names - remote_names:
        plan["create"].append({"name": name, "config": local_by_name[name]})

    for name in remote_names - local_names:
        plan["delete"].append({"name": name, "config": remote_by_name[name]})

    for name in local_names & remote_names:
        diff = DeepDiff(remote_by_name[name], local_by_name[name], ignore_order=True)
        if diff:
            plan["update"].append({"name": name, "diff": str(diff), "config": local_by_name[name]})
        else:
            plan["unchanged"].append(name)

    return plan


def display_plan(plan: dict) -> None:
    if plan["create"]:
        console.print(Panel(f"[green]+[/green] {len(plan['create'])} resource(s) to CREATE", style="green"))
        for item in plan["create"]:
            console.print(f"  [green]+[/green] {item['name']}")

    if plan["update"]:
        console.print(Panel(f"[yellow]~[/yellow] {len(plan['update'])} resource(s) to UPDATE", style="yellow"))
        for item in plan["update"]:
            console.print(f"  [yellow]~[/yellow] {item['name']}")
            if "diff" in item:
                console.print(Syntax(item["diff"], "python", theme="monokai", line_numbers=False))

    if plan["delete"]:
        console.print(Panel(f"[red]-[/red] {len(plan['delete'])} resource(s) to DELETE", style="red"))
        for item in plan["delete"]:
            console.print(f"  [red]-[/red] {item['name']}")

    if plan["unchanged"]:
        console.print(f"\n[dim]{len(plan['unchanged'])} resource(s) unchanged[/dim]")

    total_changes = len(plan["create"]) + len(plan["update"]) + len(plan["delete"])
    console.print(f"\n[bold]Plan: {total_changes} change(s)[/bold]")


def run_plan_local(config_dir: Path) -> dict:
    local = load_all_configs(config_dir)

    plan = {"create": [], "update": [], "delete": [], "unchanged": []}
    for key, items in local.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    plan["create"].append({"name": item["name"], "type": key, "config": item})

    display_plan(plan)
    return plan


def run_plan_remote(config_dir: Path, client) -> dict:
    local = load_all_configs(config_dir)
    remote = fetch_remote_state(client)
    plan = compute_diff(local, remote)
    display_plan(plan)
    return plan


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs"
    run_plan_local(Path(config_path))
