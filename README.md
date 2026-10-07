# Birthday site

A static birthday page for Paridhi. The deployable website is in `site/`; the original image files and source utilities are kept outside that folder so GitHub Pages publishes only the optimized site.

## Folder layout

- `site/index.html` — page entry point
- `site/css/` and `site/js/` — styles and interactions
- `site/assets/images/` — optimized WebP photos and cat images
- `site/assets/stickers/` — optimized transparent WebP stickers
- `site/assets/videos/` — MP4 memories used by the page
- `site/assets/audio/` — M4A music with an MP3 fallback
- `originals/` — original photos, sticker files, and unused video copies
- `tools/` — local media preparation scripts; not deployed

## Publish with GitHub Pages

1. Push this repository to GitHub on the `main` branch.
2. In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**.
3. Open the **Actions** tab and allow the Pages deployment workflow if GitHub asks.
4. The workflow publishes the contents of `site/` on each push to `main`. Once its first run succeeds, the Pages settings screen shows the live URL. A project site uses `https://YOUR-USERNAME.github.io/REPOSITORY/`.

The workflow needs the repository's Pages build/deployment permissions, which GitHub grants to the workflow token through its declared permissions. No Node.js build step is needed because the page is plain HTML, CSS, JavaScript, and media.

## Media notes

The WebP files in `site/assets/` are generated from originals under `originals/`. To regenerate them, install Pillow with `python -m pip install Pillow`, run `python tools/optimize_images.py`, and update the matching reference in `site/index.html`. The optional sticker cutout utility needs Pillow and NumPy; it writes intermediate files under `tools/generated-stickers/`. Keep site URLs relative so the page works under the repository subpath on GitHub Pages.
