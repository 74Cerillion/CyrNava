"""User-mediated Qt dialogs with host-visible initial locations for portals.

The application's /app source path exists only inside Flatpak. Passing it to the
host portal produces a folder-not-found error. Never use an editor-supplied path
or the process working directory as the initial chooser location.
"""

from pathlib import Path

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.PNG *.JPG *.JPEG *.WEBP)"


def choose_images(dialog, parent, multiple=False):
    choose = dialog.getOpenFileNames if multiple else dialog.getOpenFileName
    selection, _ = choose(parent, "Select local image", str(Path.home()), IMAGE_FILTER)
    if multiple:
        return selection
    return [selection] if selection else []


def choose_draft_destination(dialog, parent):
    selected, _ = dialog.getSaveFileName(
        parent,
        "Export recovery draft",
        str(Path.home() / "cyrnava-draft.json"),
        "JSON (*.json)",
    )
    return selected
