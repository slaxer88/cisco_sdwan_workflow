from __future__ import annotations

from typing import Any
from .auth import VManageAuth


class PolicyManager:
    def __init__(self, client: VManageAuth):
        self.client = client

    def list_centralized_policies(self) -> list[dict[str, Any]]:
        resp = self.client.get("template/policy/vsmart")
        return resp.get("data", [])

    def get_centralized_policy(self, policy_id: str) -> dict[str, Any]:
        return self.client.get(f"template/policy/vsmart/definition/{policy_id}")

    def create_centralized_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("template/policy/vsmart", data=payload)

    def update_centralized_policy(self, policy_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.put(f"template/policy/vsmart/{policy_id}", data=payload)

    def activate_centralized_policy(self, policy_id: str) -> dict[str, Any]:
        return self.client.post(f"template/policy/vsmart/activate/{policy_id}", data={})

    def deactivate_centralized_policy(self, policy_id: str) -> dict[str, Any]:
        return self.client.post(f"template/policy/vsmart/deactivate/{policy_id}", data={})

    def list_localized_policies(self) -> list[dict[str, Any]]:
        resp = self.client.get("template/policy/vedge")
        return resp.get("data", [])

    def list_policy_lists(self, list_type: str) -> list[dict[str, Any]]:
        resp = self.client.get(f"template/policy/list/{list_type}")
        return resp.get("data", [])

    def create_policy_list(self, list_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.post(f"template/policy/list/{list_type}", data=payload)

    def list_security_policies(self) -> list[dict[str, Any]]:
        resp = self.client.get("template/policy/security")
        return resp.get("data", [])
