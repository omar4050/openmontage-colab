"""Model registry loader for OpenMontage."""
from pathlib import Path
from typing import Any, Dict
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "models.yaml"


class ModelRegistry:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self._data: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"models registry not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}
        return self._data

    @property
    def data(self) -> Dict[str, Any]:
        if not self._data:
            self.load()
        return self._data


def load_registry() -> ModelRegistry:
    reg = ModelRegistry()
    reg.load()
    return reg
