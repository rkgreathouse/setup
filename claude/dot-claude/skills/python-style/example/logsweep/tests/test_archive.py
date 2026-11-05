from pathlib import Path

from logsweep.archive import archive_files


def test_moves_files_keeping_their_relative_path(tmp_path: Path) -> None:
    source = tmp_path / "service" / "old.log"
    source.parent.mkdir()
    source.write_text("entry\n")

    archived = archive_files([source], tmp_path, tmp_path / "archive")

    assert archived == [tmp_path / "archive" / "service" / "old.log"]
    assert archived[0].read_text() == "entry\n"
    assert not source.exists()
