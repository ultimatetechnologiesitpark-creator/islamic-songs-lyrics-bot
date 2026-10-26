import os, re, json, html, time
from io import BytesIO
from flask import Flask, request
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.getenv("CHANNEL_USERNAME", "@islamicsongslyrics")
OWNER_ID = os.getenv("OWNER_ID", "")
START_NUMBER = int(os.getenv("START_NUMBER", "526"))
COUNTER_FILE = os.getenv("COUNTER_FILE", "/tmp/post_counter.json")
CREATOR_TEXT = "MoHaMeD AbDuL JaLaL"
CREATOR_IMAGE = "MOHAMED ABDUL JALAL"
BASE = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
drafts = {}


def api(method, data=None, files=None):
    r = requests.post(f"{BASE}/{method}", data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()


def get_number():
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f)["next"])
    except Exception:
        return START_NUMBER


def advance_number(n):
    parent = os.path.dirname(COUNTER_FILE)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = COUNTER_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"next": n + 1}, f)
    os.replace(tmp, COUNTER_FILE)


def parse_song(s):
    tags = {}
    pattern = re.compile(r"^\[(T|C|S|Y|L)\]\s*(.*)$", re.M)
    matches = list(pattern.finditer(s))
    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(s)
        first = m.group(2).strip()
        rest = s[start:end].strip()
        tags[key] = (first + ("\n" + rest if rest else "")).strip()
    return tags


def text_post(d, n):
    title = html.escape(d.get("T", "").strip())
    cat = html.escape(d.get("C", "").strip())
    singer = html.escape(d.get("S", "").strip())
    yt = html.escape(d.get("Y", "").strip())
    lyrics = html.escape(d.get("L", "").strip())

    parts = [
        "<b>🔉ISLAMIC SONGS LYRICS🔉</b>",
        "🌐💐💐💐🔊🔊💐💐💐🌐",
        f"           💎 {cat} 💎" if cat else "",
        "💠🌹🌹🌹💠💠🌹🌹🌹💠",
        f"      🎶<b>{title}</b>🎶" if title else "",
        "----------------------------------------------------",
        "LYRICS",
        "",
        lyrics,
        "",
        "----------------------------------------------------",
        f"Singer🎤 :  {singer}" if singer else "",
        f"📺Watch &amp; Download📥 : {yt}" if yt else "",
        f"😀Created by ( {n} ) ✍️ :  {CREATOR_TEXT}",
    ]
    return "\n".join(x for x in parts if x != "")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

FONT_FILES = {
    ("ml", False): os.path.join(FONT_DIR, "NotoSansMalayalam-Regular.ttf"),
    ("ml", True):  os.path.join(FONT_DIR, "NotoSansMalayalam-Bold.ttf"),
    ("ar", False): os.path.join(FONT_DIR, "NotoSansArabic-Regular.ttf"),
    ("ar", True):  os.path.join(FONT_DIR, "NotoSansArabic-Bold.ttf"),
    ("en", False): os.path.join(FONT_DIR, "NotoSans-Regular.ttf"),
    ("en", True):  os.path.join(FONT_DIR, "NotoSans-Bold.ttf"),
}

BACKGROUND_URL = os.getenv(
    "BACKGROUND_URL",
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Masjid_An-Nabawi_in_Madinah.jpg"
)
BACKGROUND_FILE = os.path.join(BASE_DIR, "background_remote.jpg")


def ensure_background():
    """Download the high-resolution Madina background once on startup."""
    if os.path.exists(BACKGROUND_FILE) and os.path.getsize(BACKGROUND_FILE) > 200000:
        return BACKGROUND_FILE
    try:
        r = requests.get(BACKGROUND_URL, timeout=45,
                         headers={"User-Agent": "IslamicSongsLyricsBot/1.0"})
        r.raise_for_status()
        tmp = BACKGROUND_FILE + ".tmp"
        with open(tmp, "wb") as f:
            f.write(r.content)
        os.replace(tmp, BACKGROUND_FILE)
        return BACKGROUND_FILE
    except Exception:
        return None


def fallback_background(W, H):
    base = Image.new("RGB", (W, H), (231, 222, 204))
    d = ImageDraw.Draw(base)
    for y in range(H):
        t = y / max(1, H - 1)
        c = (int(205 + 35*t), int(220 + 18*t), int(218 + 5*t))
        d.line((0, y, W, y), fill=c)
    return base


def script_of(text):
    """Choose the correct font for Malayalam, Arabic or English text."""
    ml = sum(0x0D00 <= ord(ch) <= 0x0D7F for ch in text)
    ar = sum(
        (0x0600 <= ord(ch) <= 0x06FF) or
        (0x0750 <= ord(ch) <= 0x077F) or
        (0x08A0 <= ord(ch) <= 0x08FF)
        for ch in text
    )
    if ar > ml and ar > 0:
        return "ar"
    if ml > 0:
        return "ml"
    return "en"


def load_font(size, bold=False, text=""):
    script = script_of(text)
    path = FONT_FILES[(script, bool(bold))]
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def draw_text(draw, xy, text, font, fill, **kwargs):
    # RAQM shapes Arabic correctly. RTL is applied only to Arabic lines.
    if script_of(text) == "ar":
        kwargs.setdefault("direction", "rtl")
        kwargs.setdefault("language", "ar")
    draw.text(xy, text, font=font, fill=fill, **kwargs)

def text_width(draw, text, font):
    kw = {}
    if script_of(text) == "ar":
        kw = {"direction": "rtl", "language": "ar"}
    b = draw.textbbox((0, 0), text, font=font, **kw)
    return b[2] - b[0]



def char_script(ch):
    cp = ord(ch)
    if 0x0D00 <= cp <= 0x0D7F:
        return "ml"
    if ((0x0600 <= cp <= 0x06FF) or
        (0x0750 <= cp <= 0x077F) or
        (0x08A0 <= cp <= 0x08FF) or
        (0xFB50 <= cp <= 0xFDFF) or
        (0xFE70 <= cp <= 0xFEFF)):
        return "ar"
    return "en"


def split_script_runs(text):
    """Split one visual line into Malayalam / Arabic / Latin runs."""
    if not text:
        return []
    runs = []
    current = ""
    current_script = None
    for ch in text:
        s = char_script(ch)
        # Spaces/punctuation stay with the surrounding run.
        if ch.isspace() or (not ch.isalnum() and s == "en"):
            current += ch
            continue
        if current_script is None:
            current_script = s
            current += ch
        elif s == current_script:
            current += ch
        else:
            if current:
                runs.append((current_script or "en", current))
            current_script = s
            current = ch
    if current:
        runs.append((current_script or "en", current))
    return runs


def font_for_script(script, size=48, bold=False):
    return ImageFont.truetype(
        FONT_FILES[(script, bool(bold))],
        size,
        layout_engine=ImageFont.Layout.RAQM
    )


def run_width(draw, script, text, font):
    kwargs = {}
    if script == "ar":
        kwargs = {"direction": "rtl", "language": "ar"}
    b = draw.textbbox((0, 0), text, font=font, **kwargs)
    return b[2] - b[0]


def mixed_text_width(draw, text, size=48, bold=False):
    return sum(
        run_width(draw, s, t, font_for_script(s, size, bold))
        for s, t in split_script_runs(text)
    )


def draw_mixed_text(draw, xy, text, size=48, bold=False, fill=(24, 30, 28, 255)):
    """Render each Unicode script with its own bundled font."""
    x, y = xy
    for script, chunk in split_script_runs(text):
        font = font_for_script(script, size, bold)
        kwargs = {}
        if script == "ar":
            kwargs = {"direction": "rtl", "language": "ar"}
        draw.text((x, y), chunk, font=font, fill=fill, **kwargs)
        x += run_width(draw, script, chunk, font)


def wrap_mixed_words(draw, text, max_width, size=48, bold=False):
    """Wrap by words while measuring every word with its proper script font."""
    out = []
    for para in text.splitlines():
        if not para.strip():
            out.append("")
            continue
        words = para.split()
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if mixed_text_width(draw, trial, size, bold) <= max_width:
                line = trial
            else:
                if line:
                    out.append(line)
                line = word
        if line:
            out.append(line)
    return out

def wrap_words(draw, text, font, max_width):
    lines = []
    for para in text.splitlines():
        if not para.strip():
            lines.append("")
            continue
        words = para.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if text_width(draw, test, font) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def fit_box_text(draw, text, max_width, max_size, min_size, bold=True):
    for size in range(max_size, min_size - 1, -2):
        f = load_font(size, bold=bold, text=text)
        if text_width(draw, text, f) <= max_width:
            return f
    return load_font(min_size, bold=bold, text=text)


def rounded_box(draw, xy, radius, fill, outline, width=3):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def make_image(d, n):
    W = 1600
    margin = 150
    title = d.get("T", "").strip()
    category = d.get("C", "").strip()
    lyrics = d.get("L", "").strip()

    # Measure content first so the poster grows vertically instead of shrinking the lyrics.
    probe = Image.new("RGB", (W, 100), "white")
    pdraw = ImageDraw.Draw(probe)
    body_font = None
    # V5: measure and wrap mixed Malayalam + English + Arabic correctly.
    lyric_lines = wrap_mixed_words(pdraw, lyrics, W - 2 * margin, size=48, bold=False)
    line_h = 70
    blank_extra = 18

    title_font = fit_box_text(pdraw, title, 1200, 72, 42, bold=True)
    cat_font = fit_box_text(pdraw, category, 1150, 50, 32, bold=True)

    title_box_h = 170
    cat_box_h = 105
    header_h = 170
    footer_h = 170
    lyrics_top = header_h + cat_box_h + 45 + title_box_h + 65
    lyrics_h = max(160, len(lyric_lines) * line_h + 30)
    H = max(2200, lyrics_top + lyrics_h + footer_h + 100)

    bg_path = ensure_background()
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        # Keep the photo sharp. Only a very light softening is applied so the overlaid lyrics remain easy to read.
        scale = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * scale), int(bg.height * scale)), Image.Resampling.LANCZOS)
        if bg.height < H:
            # Extend with a mirrored copy rather than stretching the photo.
            extra = H - bg.height
            ext = bg.crop((0, max(0, bg.height-extra), W, bg.height)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            canvas = Image.new("RGB", (W, H))
            canvas.paste(bg, (0, 0))
            canvas.paste(ext, (0, bg.height))
            bg = canvas
        left = max(0, (bg.width - W) // 2)
        top = max(0, (bg.height - H) // 2)
        img = bg.crop((left, top, left + W, top + H))
        img = img.filter(ImageFilter.GaussianBlur(0.8))
    else:
        img = fallback_background(W, H)

    # Light readability veil, not a heavy blur.
    veil = Image.new("RGBA", (W, H), (248, 243, 231, 105))
    img = Image.alpha_composite(img.convert("RGBA"), veil)
    dr = ImageDraw.Draw(img)

    # Header
    header = "ISLAMIC SONGS LYRICS"
    header_font = load_font(62, bold=True, text=header)
    hx = (W - text_width(dr, header, header_font)) // 2
    dr.text((hx, 58), header, font=header_font, fill=(18, 71, 57, 255), stroke_width=2, stroke_fill=(255,255,255,220))
    dr.line((W//2-360, 145, W//2+360, 145), fill=(18,71,57,180), width=3)

    # Category fixed box.
    cat_y = header_h
    cat_x1, cat_x2 = 220, W - 220
    rounded_box(dr, (cat_x1, cat_y, cat_x2, cat_y + cat_box_h), 28, (12, 82, 64, 235), (210, 167, 70, 255), 4)
    cat_text = category or ""
    cx = (W - text_width(dr, cat_text, cat_font)) // 2
    cy = cat_y + (cat_box_h - (cat_font.size if hasattr(cat_font, 'size') else 50)) // 2 - 4
    cat_scripts = {s for s, t in split_script_runs(cat_text) if t.strip()}
    if len(cat_scripts) > 1:
        cw2 = mixed_text_width(dr, cat_text, size=42, bold=True)
        draw_mixed_text(dr, ((W-cw2)//2, cy), cat_text, size=42, bold=True,
                        fill=(255, 248, 226, 255))
    else:
        draw_text(dr, (cx, cy), cat_text, cat_font, (255, 248, 226, 255))

    # Title fixed box.
    title_y = cat_y + cat_box_h + 45
    tx1, tx2 = 130, W - 130
    rounded_box(dr, (tx1, title_y, tx2, title_y + title_box_h), 32, (255, 252, 244, 220), (12, 82, 64, 255), 5)
    # Elegant inner rule.
    dr.line((tx1 + 40, title_y + 20, tx2 - 40, title_y + 20), fill=(210,167,70,180), width=2)
    dr.line((tx1 + 40, title_y + title_box_h - 20, tx2 - 40, title_y + title_box_h - 20), fill=(210,167,70,180), width=2)
    tw = text_width(dr, title, title_font)
    tx = (W - tw) // 2
    tb = dr.textbbox((0,0), title, font=title_font)
    th = tb[3] - tb[1]
    ty = title_y + (title_box_h - th) // 2 - tb[1]
    title_scripts = {s for s, t in split_script_runs(title) if t.strip()}
    if len(title_scripts) > 1:
        tw2 = mixed_text_width(dr, title, size=52, bold=True)
        draw_mixed_text(dr, ((W-tw2)//2, ty), title, size=52, bold=True,
                        fill=(10, 86, 64, 255))
    else:
        draw_text(dr, (tx, ty), title, title_font, (10, 86, 64, 255),
                  stroke_width=1, stroke_fill=(255,255,255,255))

    # Lyrics.
    y = title_y + title_box_h + 70
    for line in lyric_lines:
        if line == "":
            y += blank_extra
        else:
            # Pure Arabic lines are right-aligned. Mixed/Latin/Malayalam lines
            # keep normal left-to-right layout, but every script gets its own font.
            scripts = {s for s, t in split_script_runs(line) if t.strip()}
            lw = mixed_text_width(dr, line, size=48, bold=False)
            x = W - margin - lw if scripts == {"ar"} else margin
            draw_mixed_text(dr, (x, y), line, size=48, bold=False,
                            fill=(24, 30, 28, 255))
            y += line_h

    # Fixed creator box.
    foot_y = H - footer_h + 25
    fx1, fx2 = 230, W - 230
    rounded_box(dr, (fx1, foot_y, fx2, foot_y + 110), 28, (12, 82, 64, 242), (210,167,70,255), 4)
    footer = f"CREATED BY : ({n}) {CREATOR_IMAGE}"
    footer_font = fit_box_text(dr, footer, fx2-fx1-70, 42, 28, bold=True)
    fw = text_width(dr, footer, footer_font)
    dr.text(((W-fw)//2, foot_y+27), footer, font=footer_font, fill=(255,250,235,255))

    out = BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=96, optimize=True)
    out.seek(0)
    return out

# Fetch the clean photo at startup so Render uses the high-resolution background.
ensure_background()


def allowed(uid):
    return not OWNER_ID or str(uid) == str(OWNER_ID)


@app.get("/")
def home():
    return "Islamic Songs Lyrics Bot is running", 200


@app.post("/webhook")
def webhook():
    u = request.get_json(silent=True) or {}
    msg = u.get("message")
    if msg and allowed(msg["from"]["id"]):
        chat = msg["chat"]["id"]
        txt = msg.get("text", "")
        if txt.startswith("/start"):
            api("sendMessage", {"chat_id": chat, "text": "Send song data using [T] [C] [S] [Y] [L]."})
        else:
            d = parse_song(txt)
            if d.get("T") and d.get("L"):
                n = get_number()
                drafts[str(chat)] = {"data": d, "n": n}
                preview = text_post(d, n)
                kb = {"inline_keyboard": [[{"text": "✅ POST", "callback_data": "post"}, {"text": "❌ CANCEL", "callback_data": "cancel"}]]}
                api("sendMessage", {"chat_id": chat, "text": preview[:4096], "parse_mode": "HTML", "reply_markup": json.dumps(kb)})
                im = make_image(d, n)
                api("sendPhoto", {"chat_id": chat, "caption": "Image preview"}, files={"photo": ("lyrics.jpg", im, "image/jpeg")})
            else:
                api("sendMessage", {"chat_id": chat, "text": "Need at least [T] Title and [L] Lyrics."})

    cq = u.get("callback_query")
    if cq and allowed(cq["from"]["id"]):
        chat = cq["message"]["chat"]["id"]
        action = cq["data"]
        api("answerCallbackQuery", {"callback_query_id": cq["id"]})
        if action == "cancel":
            drafts.pop(str(chat), None)
            api("sendMessage", {"chat_id": chat, "text": "Cancelled."})
        elif action == "post" and str(chat) in drafts:
            item = drafts[str(chat)]
            d, n = item["data"], item["n"]
            api("sendMessage", {"chat_id": CHANNEL, "text": text_post(d, n), "parse_mode": "HTML"})
            im = make_image(d, n)
            api("sendPhoto", {"chat_id": CHANNEL}, files={"photo": ("lyrics.jpg", im, "image/jpeg")})
            advance_number(n)
            drafts.pop(str(chat), None)
            api("sendMessage", {"chat_id": chat, "text": f"Posted successfully. Next number: {n+1}"})
    return "ok", 200
