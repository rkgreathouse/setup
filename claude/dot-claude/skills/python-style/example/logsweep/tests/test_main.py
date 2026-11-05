import os
import time
from pathlib import Path

import pytest

from ..__main__ import main


def write_config(path: Path) -> Path:
    path.write_text('max_age_days: 30\narchive_dir: archive\npatterns: ["*.log"]\n')
    return path


def write_old_log(path: Path) -> Path:
    path.write_text("entry\n")

    modified = time.time() - 40 * 86_400
    os.utime(path, (modified, modified))

    return path


def test_dry_run_lists_files_without_moving(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = write_config(tmp_path / "config.yaml")
    old_log = write_old_log(tmp_path / "old.log")

    exit_code = main([str(tmp_path), "--config", str(config), "--dry-run"])

    assert exit_code == 0
    assert old_log.exists()
    assert f"would archive {old_log}" in capsys.readouterr().out


def test_sweep_archives_old_logs(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.yaml")
    write_old_log(tmp_path / "old.log")

    exit_code = main([str(tmp_path), "--config", str(config)])

    assert exit_code == 0
    assert (tmp_path / "archive" / "old.log").exists()


def test_missing_config_exits_with_failure(tmp_path: Path) -> None:
    exit_code = main([str(tmp_path), "--config", str(tmp_path / "missing.yaml")])

    assert exit_code == 1
