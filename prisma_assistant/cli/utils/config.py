from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Config:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {}
        if path.exists():
            self.data = json.loads(path.read_text())

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))
