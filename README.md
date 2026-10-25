# Islamic Songs Lyrics Telegram Bot

Input example:

[T] കൺമണി ബീവി ഖദീജ
[C] Madh & Naat
[S] Ashkar Thekkekad, Salman Kallur
[Y] https://youtu.be/example

[L]
ഇവിടെ മുഴുവൻ lyrics...

## Render settings
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

Environment variables:
BOT_TOKEN = your BotFather token
CHANNEL_USERNAME = @islamicsongslyrics
START_NUMBER = 526
OWNER_ID = your numeric Telegram user ID (recommended)

After deployment, set Telegram webhook:
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://YOUR-RENDER-URL.onrender.com/webhook

Do not commit your BOT_TOKEN to GitHub.

Note: the simple counter is stored in /tmp and can reset when the service restarts. For permanent numbering, connect a persistent database before relying on it long-term.
