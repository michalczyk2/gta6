# troche-niepowaznie-media

Graphics and tooling for the @gta_6_daily_news Instagram account.

- `tools/render_html.py` (main) renders a carousel from `post.json` with headless Chromium: `python3 tools/render_html.py posts/<date>/post.json posts/<date>`. Slide kinds and fields are documented at the top of the file.
- `tools/render.py` is the older Pillow renderer, kept as a fallback.
- `posts/<date>/` holds each day's slides, post.json and caption.txt
