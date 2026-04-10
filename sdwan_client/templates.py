from __future__ import annotations

from typing import Any
from .auth import VManageAuth


class TemplateManager:
    def __init__(self, client: VManageAuth):
        self.client = client

    def list_feature_templates(self) -> list[dict[str, Any]]:
        resp = self.client.get("template/feature")
        return resp.get("data", [])

    def get_feature_template(self, template_id: str) -> dict[str, Any]:
        return self.client.get(f"template/feature/object/{template_id}")

    def create_feature_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("template/feature", data=payload)

    def update_feature_template(self, template_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload["templateId"] = template_id
        return self.client.put(f"template/feature/{template_id}", data=payload)

    def delete_feature_template(self, template_id: str) -> dict[str, Any]:
        return self.client.delete(f"template/feature/{template_id}")

    def list_device_templates(self) -> list[dict[str, Any]]:
        resp = self.client.get("template/device")
        return resp.get("data", [])

    def get_device_template(self, template_id: str) -> dict[str, Any]:
        return self.client.get(f"template/device/object/{template_id}")

    def create_device_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("template/device/feature", data=payload)

    def attach_template(self, template_id: str, devices: list[dict]) -> dict[str, Any]:
        payload = {
            "deviceTemplateList": [
                {
                    "templateId": template_id,
                    "device": devices,
                    "isEdited": False,
                    "isMasterEdited": False,
                }
            ]
        }
        return self.client.post("template/device/config/attachfeature", data=payload)

    def detach_template(self, device_type: str, device_id: str) -> dict[str, Any]:
        payload = {
            "deviceType": device_type,
            "devices": [{"deviceId": device_id}],
        }
        return self.client.post("template/config/device/mode/cli", data=payload)

    def get_template_input(self, template_id: str, device_ids: list[str] | None = None) -> dict[str, Any]:
        payload = {"templateId": template_id, "deviceIds": device_ids or [], "isEdited": False, "isMasterEdited": False}
        return self.client.post("template/device/config/input", data=payload)
