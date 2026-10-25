import os, re, json, html, textwrap, tempfile
from io import BytesIO
from flask import Flask, request
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.getenv("CHANNEL_USERNAME", "@islamicsongslyrics")
OWNER_ID = os.getenv("OWNER_ID", "")
CREATOR = "MOHAMED ABDUL JALAL"
COUNTER_FILE = "/tmp/post_counter.json"
START_NUMBER = int(os.getenv("START_NUMBER", "526"))
BASE = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
drafts = {}

def api(method, data=None, files=None):
    r = requests.post(f"{BASE}/{method}", data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()

def get_number():
    try:
        with open(COUNTER_FILE) as f:
            return int(json.load(f)["next"])
    except Exception:
        return START_NUMBER

def advance_number(n):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"next": n + 1}, f)

def parse_song(s):
    tags = {}
    pattern = re.compile(r'^\[(T|C|S|Y|L)\]\s*(.*)$', re.M)
    matches = list(pattern.finditer(s))
    for i,m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(s)
        first = m.group(2).strip()
        rest = s[start:end].strip()
        tags[key] = (first + ("\n" + rest if rest else "")).strip()
    return tags

def text_post(d, n):
    title=d.get("T","").strip(); cat=d.get("C","").strip()
    singer=d.get("S","").strip(); yt=d.get("Y","").strip(); lyrics=d.get("L","").strip()
    parts = [
        "🔊 ISLAMIC SONGS LYRICS 🔊",
        "🌐🌺🌺🌺🔊🔊🌺🌺🌺🌐",
        f"💎 {cat} 💎" if cat else "",
        f"🎶 {title} 🎶" if title else "",
        "------------------------------------------",
        lyrics,
        "------------------------------------------",
        f"🎤 Singer : {singer}" if singer else "",
        f"📺 Watch & Download 📥 : {yt}" if yt else "",
        f"😀 CREATED BY : ({n}) {CREATOR}",
    ]
    return "\n".join(x for x in parts if x)

def font(size):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansMalayalam-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, maxw):
    out=[]
    for para in text.splitlines():
        if not para.strip():
            out.append(""); continue
        words=para.split()
        line=""
        for w in words:
            test=(line+" "+w).strip()
            if draw.textbbox((0,0), test, font=fnt)[2] <= maxw:
                line=test
            else:
                if line: out.append(line)
                line=w
        if line: out.append(line)
    return out

def make_image(d, n):
    W=1600; margin=130
    tmp=Image.new("RGB",(W,2000),"white"); dr=ImageDraw.Draw(tmp)
    bodyf=font(44); titlef=font(66); headf=font(56); catf=font(46); footf=font(36)
    lines=wrap(dr,d.get("L",""),bodyf,W-2*margin)
    line_h=62
    H=max(2100, 600 + len(lines)*line_h + 300)

    bg_path=os.path.join(os.path.dirname(__file__),"background.jpg")
    if os.path.exists(bg_path):
        bg=Image.open(bg_path).convert("RGB")
        ratio=max(W/bg.width,H/bg.height)
        bg=bg.resize((int(bg.width*ratio),int(bg.height*ratio)))
        left=(bg.width-W)//2; top=(bg.height-H)//2
        img=bg.crop((left,top,left+W,top+H)).filter(ImageFilter.GaussianBlur(5))
    else:
        img=Image.new("RGB",(W,H),(239,231,210))

    overlay=Image.new("RGBA",(W,H),(255,255,255,150))
    img=Image.alpha_composite(img.convert("RGBA"),overlay)
    dr=ImageDraw.Draw(img)

    def centered(y, txt, fnt, fill):
        box=dr.textbbox((0,0),txt,font=fnt); x=(W-(box[2]-box[0]))//2
        dr.text((x,y),txt,font=fnt,fill=fill)

    centered(70,"ISLAMIC SONGS LYRICS",headf,(15,86,65,255))
    centered(155,d.get("C",""),catf,(130,91,25,255))
    centered(235,d.get("T",""),titlef,(7,92,62,255))
    y=360
    for line in lines:
        dr.text((margin,y),line,font=bodyf,fill=(20,20,20,255))
        y+=line_h
    centered(H-150,f"CREATED BY : ({n}) {CREATOR}",footf,(15,86,65,255))
    out=BytesIO(); img.convert("RGB").save(out,"JPEG",quality=95,optimize=True); out.seek(0)
    return out

def allowed(uid):
    return not OWNER_ID or str(uid)==str(OWNER_ID)

@app.get("/")
def home(): return "Islamic Songs Lyrics Bot is running", 200

@app.post("/webhook")
def webhook():
    u=request.get_json(silent=True) or {}
    msg=u.get("message")
    if msg and allowed(msg["from"]["id"]):
        chat=msg["chat"]["id"]; txt=msg.get("text","")
        if txt.startswith("/start"):
            api("sendMessage",{"chat_id":chat,"text":"Send song data using [T] [C] [S] [Y] [L]."})
        else:
            d=parse_song(txt)
            if d.get("T") and d.get("L"):
                n=get_number(); drafts[str(chat)]={"data":d,"n":n}
                preview=text_post(d,n)
                kb={"inline_keyboard":[[{"text":"✅ POST","callback_data":"post"},{"text":"❌ CANCEL","callback_data":"cancel"}]]}
                api("sendMessage",{"chat_id":chat,"text":preview[:4096],"reply_markup":json.dumps(kb)})
                im=make_image(d,n)
                api("sendPhoto",{"chat_id":chat,"caption":"Lyrics image preview"},files={"photo":("lyrics.jpg",im,"image/jpeg")})
            else:
                api("sendMessage",{"chat_id":chat,"text":"Need at least [T] Title and [L] Lyrics."})

    cq=u.get("callback_query")
    if cq and allowed(cq["from"]["id"]):
        chat=cq["message"]["chat"]["id"]; action=cq["data"]
        api("answerCallbackQuery",{"callback_query_id":cq["id"]})
        if action=="cancel":
            drafts.pop(str(chat),None)
            api("sendMessage",{"chat_id":chat,"text":"Cancelled."})
        elif action=="post" and str(chat) in drafts:
            item=drafts[str(chat)]; d=item["data"]; n=item["n"]
            api("sendMessage",{"chat_id":CHANNEL,"text":text_post(d,n)})
            im=make_image(d,n)
            api("sendPhoto",{"chat_id":CHANNEL},files={"photo":("lyrics.jpg",im,"image/jpeg")})
            advance_number(n); drafts.pop(str(chat),None)
            api("sendMessage",{"chat_id":chat,"text":f"Posted successfully. Next number: {n+1}"})
    return "ok",200
