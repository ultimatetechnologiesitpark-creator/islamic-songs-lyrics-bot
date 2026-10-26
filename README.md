# Islamic Songs Lyrics Bot — V4 Multilanguage Fix

This replacement fixes square-box characters in generated images.

Supported image text:
- Malayalam — Noto Sans Malayalam
- Arabic — Noto Sans Arabic + RAQM shaping / RTL
- English and numbers — Noto Sans

Upload/replace `app.py`, `requirements.txt`, and the entire `fonts` folder in GitHub.
Do not upload the ZIP itself. Render should redeploy automatically.

The background remains downloaded from the configured high-resolution `BACKGROUND_URL`.


## V5 fix
V5 changes lyric rendering from one-font-per-line to character/script-run font fallback.
This specifically fixes English and Arabic becoming square boxes when a line also
contains Malayalam. Pure Arabic lines are right-aligned and rendered with RAQM.
