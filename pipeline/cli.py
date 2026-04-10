from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from pipeline.validate import run_validation
from pipeline.plan import run_plan_local, run_plan_remote
from pipeline.deploy import run_deploy, run_deploy_dry

console = Console()


def get_vmanage_client():
    from sdwan_client.auth import VManageAuth

    url = os.environ.get("VMANAGE_URL", "")
    username = os.environ.get("VMANAGE_USERNAME", "")
    password = os.environ.get("VMANAGE_PASSWORD", "")
    port = int(os.environ.get("VMANAGE_PORT", "443"))

    if not all([url, username, password]):
        console.print("[red]Missing vManage credentials. Set VMANAGE_URL, VMANAGE_USERNAME, VMANAGE_PASSWORD[/red]")
        sys.exit(1)

    return VManageAuth(url, username, password, port)


def cmd_validate(args):
    console.print("[bold]Stage: VALIDATE[/bold]\n")
    success = run_validation(Path(args.config_dir))
    sys.exit(0 if success else 1)


def cmd_plan(args):
    console.print("[bold]Stage: PLAN[/bold]\n")

    console.print("[bold]Step 1: Validate configs[/bold]")
    if not run_validation(Path(args.config_dir)):
        console.print("[red]Validation failed. Aborting plan.[/red]")
        sys.exit(1)

    console.print("\n[bold]Step 2: Generate plan[/bold]")
    if args.local:
        run_plan_local(Path(args.config_dir))
    else:
        client = get_vmanage_client()
        with client:
            run_plan_remote(Path(args.config_dir), client)


def cmd_deploy(args):
    console.print("[bold]Stage: DEPLOY[/bold]\n")

    console.print("[bold]Step 1: Validate[/bold]")
    if not run_validation(Path(args.config_dir)):
        console.print("[red]Validation failed. Aborting deploy.[/red]")
        sys.exit(1)

    console.print("\n[bold]Step 2: Plan[/bold]")
    if args.dry_run:
        plan = run_plan_local(Path(args.config_dir))
        run_deploy_dry(plan)
        return

    client = get_vmanage_client()
    with client:
        plan = run_plan_remote(Path(args.config_dir), client)

        if not plan.get("create") and not plan.get("update") and not plan.get("delete"):
            console.print("\n[green]No changes to deploy.[/green]")
            return

        if not args.auto_approve:
            confirm = input("\nProceed with deployment? (yes/no): ")
            if confirm.lower() != "yes":
                console.print("[yellow]Deployment cancelled.[/yellow]")
                return

        console.print("\n[bold]Step 3: Deploy[/bold]")
        success = run_deploy(plan, client)
        sys.exit(0 if success else 1)


def cmd_status(args):
    console.print("[bold]Stage: STATUS[/bold]\n")
    client = get_vmanage_client()
    with client:
        from sdwan_client.devices import DeviceManager

        dm = DeviceManager(client)
        devices = dm.list_devices()

        from rich.table import Table

        table = Table(title="SD-WAN Devices")
        table.add_column("Hostname", style="cyan")
        table.add_column("Device Type")
        table.add_column("System IP")
        table.add_column("Site ID")
        table.add_column("Reachability", style="green")

        for d in devices:
            table.add_row(
                d.get("host-name", ""),
                d.get("device-type", ""),
                d.get("system-ip", ""),
                str(d.get("site-id", "")),
                d.get("reachability", ""),
            )
        console.print(table)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="sdwan-pipeline",
        description="Cisco SD-WAN CI/CD Pipeline CLI",
    )
    parser.add_argument("--config-dir", default="configs", help="Path to config directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Validate YAML configs against schemas")

    plan_parser = subparsers.add_parser("plan", help="Generate change plan")
    plan_parser.add_argument("--local", action="store_true", help="Local-only plan (no vManage connection)")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy changes to vManage")
    deploy_parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed")
    deploy_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompt")

    subparsers.add_parser("status", help="Show current vManage device status")

    args = parser.parse_args()
    commands = {
        "validate": cmd_validate,
        "plan": cmd_plan,
        "deploy": cmd_deploy,
        "status": cmd_status,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
