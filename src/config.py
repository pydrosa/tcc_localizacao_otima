from pathlib import Path
import yaml


def load_config(path: str | Path = "config/config.yaml") -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuração não encontrada: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
