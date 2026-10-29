# Desktop icon

The canonical logo is `frontend/public/assets/branding/DesktopLogo.png`: an unchanged copy of the owner's supplied 1254 × 1254 RGB image. The original black background is retained. SHA-256: `0d5be626f349f83cde2dc0738242e7cccf13ed7b08c08ab85b6d6853fa69db24`.

The adjacent `cyrnava-{16,32,48,64,128,256,512}.png` files are complete Lanczos downsampling, without cropping, recoloring, redrawing or background removal. The favicon uses 16/32 pixels, the sidebar uses 256 pixels displayed at 128 CSS pixels, and the installer uses 512 pixels. The remaining sizes are available for other desktop scaling needs. No remote asset is required.

To regenerate after reviewing the same source, run from the repository root:

```bash
backend/.venv/bin/python desktop/generate_icons.py frontend/public/assets/branding/DesktopLogo.png
```

Pillow is already a pinned backend dependency; no new package was added. `cyrnava.svg` remains only as a legacy placeholder reference for safe installer detection. The installer compares bytes rather than guessing from filenames, preserves custom icons, and accepts an explicit `--icon` override. It copies selected artwork into each program release so it survives moving the source checkout.
