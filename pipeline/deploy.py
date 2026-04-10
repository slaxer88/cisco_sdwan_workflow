from __future__ import annotations

import time
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from sdwan_client.auth import VManageAuth
from sdwan_client.templates import TemplateManager
from sdwan_client.policies import PolicyManager
from sdwan_client.devices import DeviceManager

console = Console()


def _wait_for_task(device_mgr: DeviceManager, task_id: str, timeout: int = 300) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        status = device_mgr.check_task_status(task_id)
        summary = status.get("summary", [])
        if summary:
            activity_status = summary[0].get("status", "")
            if activity_status == "done":
                return True
            if activity_status in ("failure", "failed"):
                console.print(f"[red]Task {task_id} failed: {summary}[/red]")
                return False
        time.sleep(5)
    console.print(f"[red]Task {task_id} timed out[/red]")
    return False


def deploy_feature_templates(client: VManageAuth, templates: list[dict]) -> list[str]:
    tm = TemplateManager(client)
    created_ids = []

    for tpl in templates:
        payload = {
            "templateName": tpl["name"],
            "templateDescription": tpl.get("description", ""),
            "templateType": tpl["template_type"],
            "deviceType": tpl["device_type"],
            "templateDefinition": tpl.get("definition", {}),
            "templateMinVersion": "15.0.0",
        }
        console.print(f"  Creating feature template: [cyan]{tpl['name']}[/cyan]")
        try:
            resp = tm.create_feature_template(payload)
            template_id = resp.get("templateId", "")
            created_ids.append(template_id)
            console.print(f"    [green]Created[/green] -> {template_id}")
        except Exception as e:
            console.print(f"    [red]Failed[/red]: {e}")

    return created_ids


def deploy_policies(client: VManageAuth, policies: list[dict]) -> list[str]:
    pm = PolicyManager(client)
    created_ids = []

    for pol in policies:
        payload = {
            "policyName": pol["name"],
            "policyDescription": pol.get("description", ""),
            "policyType": pol.get("policy_type", "feature"),
            "policyDefinition": pol.get("definition", {}),
        }
        console.print(f"  Creating policy: [cyan]{pol['name']}[/cyan]")
        try:
            resp = pm.create_centralized_policy(payload)
            policy_id = resp.get("policyId", "")
            created_ids.append(policy_id)
            console.print(f"    [green]Created[/green] -> {policy_id}")
        except Exception as e:
            console.print(f"    [red]Failed[/red]: {e}")

    return created_ids


def attach_devices(client: VManageAuth, devices: list[dict], template_map: dict[str, str]) -> bool:
    tm = TemplateManager(client)
    dm = DeviceManager(client)
    success = True

    for device in devices:
        template_name = device.get("device_template", "")
        template_id = template_map.get(template_name)
        if not template_id:
            console.print(f"  [yellow]Skipping {device['hostname']}: template '{template_name}' not found[/yellow]")
            continue

        device_vars = []
        variables = device.get("variables", {})
        for var_name, var_value in variables.items():
            device_vars.append(
                {
                    "csv-deviceId": device["device_id"],
                    "csv-deviceIP": device.get("system_ip", ""),
                    "csv-host-name": device["hostname"],
                    f"/0/{var_name}": str(var_value),
                }
            )

        console.print(f"  Attaching template to: [cyan]{device['hostname']}[/cyan]")
        try:
            resp = tm.attach_template(template_id, device_vars)
            task_id = resp.get("id", "")
            if task_id:
                ok = _wait_for_task(dm, task_id)
                if ok:
                    console.print(f"    [green]Attached successfully[/green]")
                else:
                    console.print(f"    [red]Attachment failed[/red]")
                    success = False
        except Exception as e:
            console.print(f"    [red]Failed[/red]: {e}")
            success = False

    return success


def run_deploy(plan: dict, client: VManageAuth) -> bool:
    console.print("\n[bold]Deploying changes to vManage...[/bold]\n")
    all_ok = True

    with Progress() as progress:
        total = len(plan.get("create", []))
        task = progress.add_task("Deploying...", total=total)

        for item in plan.get("create", []):
            config = item.get("config", {})
            item_type = item.get("type", "")

            if item_type == "feature_templates":
                deploy_feature_templates(client, [config])
            elif item_type == "centralized_policies":
                deploy_policies(client, [config])

            progress.update(task, advance=1)

    return all_ok


def run_deploy_dry(plan: dict) -> None:
    console.print("\n[bold yellow]DRY RUN - No changes will be made[/bold yellow]\n")

    for action_type in ("create", "update", "delete"):
        items = plan.get(action_type, [])
        if not items:
            continue

        symbols = {"create": "+", "update": "~", "delete": "-"}
        colors = {"create": "green", "update": "yellow", "delete": "red"}

        for item in items:
            console.print(
                f"  [{colors[action_type]}]{symbols[action_type]}[/{colors[action_type]}] "
                f"Would {action_type}: {item['name']}"
            )

    console.print("\n[bold]Dry run complete. No changes made.[/bold]")
