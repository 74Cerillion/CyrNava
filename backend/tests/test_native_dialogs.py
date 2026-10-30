"""Qt's public chooser contract, without requiring Qt in the backend environment."""

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from desktop.native.dialogs import choose_draft_destination, choose_images  # noqa: E402


def test_image_dialog_starts_at_home_and_preserves_portal_selection(
    tmp_path, monkeypatch
):
    home = tmp_path / "home with spaces"
    monkeypatch.setattr(Path, "home", lambda: home)
    # A portal may return a document grant path, not the original host path.
    selected = "/run/user/1000/doc/grant-id/evidence.png"
    dialog = Mock()
    dialog.getOpenFileName.return_value = (selected, "Images")
    assert choose_images(dialog, "parent") == [selected]
    assert dialog.getOpenFileName.call_args.args[2] == str(home)
    assert "/app/" not in dialog.getOpenFileName.call_args.args[2]
    dialog.getOpenFileNames.assert_not_called()


def test_multiple_selection_and_cancel_do_not_invent_file_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    dialog = Mock()
    dialog.getOpenFileNames.return_value = (
        ["/run/user/1000/doc/a/a.png", "/run/user/1000/doc/b/b.jpg"],
        "Images",
    )
    assert choose_images(dialog, None, multiple=True) == [
        "/run/user/1000/doc/a/a.png",
        "/run/user/1000/doc/b/b.jpg",
    ]
    assert dialog.getOpenFileNames.call_args.args[2] == str(tmp_path)
    dialog.getOpenFileName.return_value = ("", "")
    assert choose_images(dialog, None) == []
    dialog.getOpenFileNames.return_value = ([], "")
    assert choose_images(dialog, None, multiple=True) == []


def test_export_uses_absolute_home_destination_and_honors_cancel(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    dialog = Mock()
    dialog.getSaveFileName.return_value = (
        "/run/user/1000/doc/export/draft.json",
        "JSON",
    )
    assert (
        choose_draft_destination(dialog, "parent")
        == "/run/user/1000/doc/export/draft.json"
    )
    assert dialog.getSaveFileName.call_args.args[2] == str(
        tmp_path / "cyrnava-draft.json"
    )
    dialog.getSaveFileName.return_value = ("", "")
    assert choose_draft_destination(dialog, "parent") == ""


def test_backup_save_suggests_extension_without_changing_portal_grant(
    tmp_path, monkeypatch
):
    from desktop.native.dialogs import choose_backup_destination

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    dialog = Mock()
    # User can replace the suggested name with one lacking an extension.
    selected = "/run/user/1000/doc/backup-grant/test"
    dialog.getSaveFileName.return_value = (selected, "CyrNava backup")
    assert choose_backup_destination(dialog, None) == selected
    assert dialog.getSaveFileName.call_args.args[2] == str(
        tmp_path / "cyrnava-backup.cyrnava"
    )
    dialog.getSaveFileName.return_value = ("", "")
    assert choose_backup_destination(dialog, None) == ""


def test_backup_open_includes_extensionless_files_and_preserves_grant(
    tmp_path, monkeypatch
):
    from desktop.native.dialogs import choose_backup_source

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    dialog = Mock()
    selected = "/run/user/1000/doc/backup-grant/test"
    dialog.getOpenFileName.return_value = (selected, "All files (*)")
    assert choose_backup_source(dialog, None) == selected
    args = dialog.getOpenFileName.call_args.args
    assert args[2] == str(tmp_path)
    assert "*.cyrnava" in args[3] and "*.zip" in args[3] and "All files (*)" in args[3]
    dialog.getOpenFileName.return_value = ("", "")
    assert choose_backup_source(dialog, None) == ""
