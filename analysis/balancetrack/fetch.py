from __future__ import annotations

from pathlib import Path
from typing import List

import requests

TIMEOUT = 10


def base_url(host: str) -> str:
    if not host.startswith("http"):
        host = "http://" + host
    return host.rstrip("/")


def status(host: str) -> dict:
    r = requests.get(base_url(host) + "/status", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def list_sessions(host: str) -> List[dict]:
    r = requests.get(base_url(host) + "/sessions", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def download(host: str, name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / name
    with requests.get(f"{base_url(host)}/sessions/{name}", stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(target, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return target


def delete(host: str, name: str):
    r = requests.delete(f"{base_url(host)}/sessions/{name}", timeout=TIMEOUT)
    r.raise_for_status()
