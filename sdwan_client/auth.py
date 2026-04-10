from __future__ import annotations

import requests
import urllib3
from typing import Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VManageAuth:
    def __init__(self, base_url: str, username: str, password: str, port: int = 443):
        self.base_url = f"{base_url.rstrip('/')}:{port}"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False

    def login(self) -> None:
        login_url = f"{self.base_url}/j_security_check"
        payload = {"j_username": self.username, "j_password": self.password}

        resp = self.session.post(login_url, data=payload, timeout=30)
        if resp.status_code != 200 or "html" in resp.text.lower():
            raise ConnectionError(f"vManage login failed: {resp.status_code}")

        token_url = f"{self.base_url}/dataservice/client/token"
        token_resp = self.session.get(token_url, timeout=15)
        if token_resp.status_code == 200:
            self.session.headers["X-XSRF-TOKEN"] = token_resp.text.strip()

    def logout(self) -> None:
        try:
            self.session.get(f"{self.base_url}/logout", timeout=10)
        except Exception:
            pass

    def get(self, endpoint: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/dataservice/{endpoint.lstrip('/')}"
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data: dict | None = None, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/dataservice/{endpoint.lstrip('/')}"
        resp = self.session.post(url, json=data, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def put(self, endpoint: str, data: dict | None = None, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/dataservice/{endpoint.lstrip('/')}"
        resp = self.session.put(url, json=data, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def delete(self, endpoint: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/dataservice/{endpoint.lstrip('/')}"
        resp = self.session.delete(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()
