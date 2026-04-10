from __future__ import annotations

from typing import Any
from .auth import VManageAuth


class DeviceManager:
    def __init__(self, client: VManageAuth):
        self.client = client

    def list_devices(self) -> list[dict[str, Any]]:
        resp = self.client.get("device")
        return resp.get("data", [])

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        return self.client.get(f"device/state/{device_id}")

    def get_running_config(self, device_id: str) -> str:
        resp = self.client.get(f"template/config/running/{device_id}")
        return resp.get("config", "")

    def get_device_counters(self) -> list[dict[str, Any]]:
        resp = self.client.get("device/counters")
        return resp.get("data", [])

    def get_control_status(self, device_id: str) -> list[dict[str, Any]]:
        resp = self.client.get(f"device/control/synced/connections?deviceId={device_id}")
        return resp.get("data", [])

    def check_task_status(self, task_id: str) -> dict[str, Any]:
        return self.client.get(f"device/action/status/{task_id}")
