# Islamic Songs Lyrics Bot — V3

Render/Gunicorn Telegram bot for `@islamicsongslyrics`.

## Input
```text
[T] Title
[C] Category
[S] Singer
[Y] YouTube Link

[L]
Full Lyrics
```

## Image template
- High-resolution Masjid an-Nabawi photo downloaded automatically at startup
- Fixed professional category box
- Fixed professional title box
- Dynamic lyrics area (poster grows vertically)
- Fixed `CREATED BY` box
- Singer and YouTube link are NOT placed on the image
- Malayalam font is bundled in `fonts/`
- Final text is rendered programmatically, so Malayalam spelling stays crisp and accurate

## Background image
The default background is **Masjid An-Nabawi in Madinah** by Adli Wahid, 2,978 × 4,382 px, from Wikimedia Commons.
License: **CC BY-SA 4.0**. The bot downloads the original high-resolution file from Wikimedia Commons at startup.
Source: https://commons.wikimedia.org/wiki/File:Masjid_An-Nabawi_in_Madinah.jpg

You may override the source with the `BACKGROUND_URL` environment variable if desired.

## Environment variables
- `BOT_TOKEN`
- `CHANNEL_USERNAME` (default `@islamicsongslyrics`)
- `OWNER_ID` (optional)
- `START_NUMBER` (default `526`)
- `COUNTER_FILE` (default `/tmp/post_counter.json`)
- `BACKGROUND_URL` (optional)

The post number advances only after a successful channel publish.
