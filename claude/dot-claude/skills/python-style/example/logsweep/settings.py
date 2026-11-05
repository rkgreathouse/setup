from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import ConfigError


@dataclass(frozen=True, slots=True)
class Settings:
    max_age_days: int
    archive_dir: str
    patterns: tuple[str, ...]


def load_settings(path: Path) -> Settings:
    raw = read_yaml(path)
    return parse_settings(raw, path)


def read_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ConfigError(f"config not found: {path}")

    with path.open() as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ConfigError(f"config must be a mapping: {path}")

    return data


def parse_settings(raw: dict[str, object], path: Path) -> Settings:
    max_age_days = raw.get("max_age_days")
    archive_dir = raw.get("archive_dir")
    patterns = raw.get("patterns")

    if not isinstance(max_age_days, int):
        raise ConfigError(f"{path}: max_age_days must be an integer")

    if not isinstance(archive_dir, str):
        raise ConfigError(f"{path}: archive_dir must be a string")

    if not isinstance(patterns, list):
        raise ConfigError(f"{path}: patterns must be a list")

    return Settings(
        max_age_days=max_age_days,
        archive_dir=archive_dir,
        patterns=tuple(str(pattern) for pattern in patterns),
    )
