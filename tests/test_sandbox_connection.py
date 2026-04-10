#!/usr/bin/env python3
"""
Cisco DevNet Sandbox 연결 테스트 스크립트
Sandbox URL: https://developer.cisco.com/sdwan/sandbox/
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdwan_client.auth import VManageAuth
from sdwan_client.devices import DeviceManager
from sdwan_client.templates import TemplateManager
from sdwan_client.policies import PolicyManager
from rich.console import Console
from rich.table import Table

console = Console()

SANDBOX_URL = os.environ.get("VMANAGE_URL", "https://sandbox-sdwan-2.cisco.com")
SANDBOX_USER = os.environ.get("VMANAGE_USERNAME", "devnetuser")
SANDBOX_PASS = os.environ.get("VMANAGE_PASSWORD", "RG!_Yw919_83")
SANDBOX_PORT = int(os.environ.get("VMANAGE_PORT", "443"))


def main():
    console.print("[bold]Connecting to Cisco SD-WAN Sandbox...[/bold]\n")

    try:
        client = VManageAuth(SANDBOX_URL, SANDBOX_USER, SANDBOX_PASS, SANDBOX_PORT)
        client.login()
        console.print("[green]Login successful[/green]\n")
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        console.print("\nTry the Always-On sandbox: https://developer.cisco.com/sdwan/sandbox/")
        sys.exit(1)

    try:
        dm = DeviceManager(client)
        devices = dm.list_devices()

        table = Table(title=f"SD-WAN Devices ({len(devices)} total)")
        table.add_column("Hostname", style="cyan")
        table.add_column("Type")
        table.add_column("System IP")
        table.add_column("Site ID")
        table.add_column("Status", style="green")
        table.add_column("Version")

        for d in devices:
            table.add_row(
                d.get("host-name", "N/A"),
                d.get("device-type", "N/A"),
                d.get("system-ip", "N/A"),
                str(d.get("site-id", "N/A")),
                d.get("reachability", "N/A"),
                d.get("version", "N/A"),
            )
        console.print(table)

        console.print("\n[bold]Feature Templates:[/bold]")
        tm = TemplateManager(client)
        templates = tm.list_feature_templates()
        for t in templates[:10]:
            console.print(f"  - {t.get('templateName', 'N/A')} ({t.get('templateType', 'N/A')})")
        if len(templates) > 10:
            console.print(f"  ... and {len(templates) - 10} more")

        console.print(f"\n[bold]Centralized Policies:[/bold]")
        pm = PolicyManager(client)
        policies = pm.list_centralized_policies()
        for p in policies[:5]:
            console.print(f"  - {p.get('policyName', 'N/A')}")
        if not policies:
            console.print("  (none)")

    finally:
        client.logout()
        console.print("\n[dim]Logged out[/dim]")


if __name__ == "__main__":
    main()
