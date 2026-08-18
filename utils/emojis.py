import re
import os
import urllib.request
import subprocess

# Maps hundreds of words, synonyms, and conversational phrases to Twemoji Hex Codes
EMOJI_HEX_MAP = {
    # --- CONVERSATIONAL & COMMON WORDS ---
    "you": "1f449", "your": "1f449", "yours": "1f449", "u": "1f449", "look": "👀", "see": "👀", "watch": "👀",
    "yes": "2705", "yeah": "2705", "yep": "2705", "sure": "2705", "ok": "2705", "okay": "2705", "agreed": "2705", "correct": "2705",
    "no": "274c", "nope": "274c", "never": "274c", "not": "274c", "wrong": "274c", "false": "274c", "stop": "1f6d1", "halt": "1f6d1",
    "people": "1f465", "everyone": "1f465", "crowd": "1f465", "us": "1f465", "we": "1f465", "together": "1f91d", "community": "1f465",
    "message": "💬", "messages": "💬", "talk": "💬", "talking": "💬", "speak": "🎙️", "speaking": "🎙️", "said": "💬", "word": "💬", "words": "💬",
    "heard": "1f442", "hear": "1f442", "hearing": "1f442", "listen": "1f442", "listening": "1f442", "sound": "🔊",
    "join": "1f91d", "join us": "1f91d", "invite": "📩", "invites": "📩", "invitation": "📩", "welcome": "🤝",
    "moment": "⏳", "now": "⏰", "today": "📅", "time": "⏰", "clock": "⏰", "hour": "⏰", "minute": "⏱️", "second": "⏱️",
    "week": "1f4c5", "annual": "1f5d3", "annual revival": "🔥", "yearly": "1f5d3", "year": "📅", "date": "📅",
    "here": "📍", "location": "📍", "place": "📍", "come": "🏃", "go": "🏃", "run": "🏃", "enter": "🚪",

    # --- CHURCH, CHRISTIANITY, FAITH, WORSHIP & MINISTRY ---
    "church": "26ea", "cathedral": "26ea", "chapel": "26ea", "temple": "26ea", "altar": "26ea", "sanctuary": "26ea",
    "god": "271d", "jesus": "271d", "christ": "271d", "lord": "1f451", "savior": "271d", "messiah": "271d", "yahweh": "271d",
    "pray": "1f64f", "prayer": "1f64f", "prayers": "1f64f", "praying": "1f64f", "amen": "1f64f", "intercession": "1f64f", "supplication": "1f64f",
    "bible": "1f4d6", "scripture": "1f4d6", "scriptures": "1f4d6", "gospel": "1f4d6", "verse": "1f4d6", "testament": "1f4d6",
    "faith": "1f54a", "believe": "1f54a", "believer": "1f54a", "belief": "1f54a", "trust": "1f54a", "hope": "1f54a",
    "holy": "1f54a", "spirit": "1f54a", "ghost": "1f54a", "anointing": "1f54a", "anointed": "1f54a", "presence": "1f54a",
    "glory": "2728", "glorious": "2728", "greater": "1f31f", "praise": "1f64c", "worship": "1f64c", "hallelujah": "1f64c", "hosanna": "1f64c", "exalt": "1f64c",
    "revival": "1f525", "crusade": "1f525", "fire": "1f525", "flame": "1f525", "flames": "1f525", "breakthrough": "26a1",
    "miracle": "2728", "miracles": "2728", "wonder": "2728", "wonders": "2728", "sign": "2728", "signs": "2728", "heal": "✨", "healing": "✨", "deliverance": "✨",
    "pastor": "1f399", "priest": "26ea", "bishop": "26ea", "minister": "1f399", "preacher": "1f399", "apostle": "1f4dc", "prophet": "1f4dc", "leadership": "👑",
    "cross": "271d", "crucifix": "271d", "salvation": "271d", "redeemed": "271d", "grace": "1f54a", "mercy": "1f54a",
    "heaven": "1f47c", "angel": "1f47c", "angels": "1f47c", "celestial": "2601", "paradise": "2601", "eternal": "♾️",
    "devil": "1f608", "satan": "1f608", "demon": "1f608", "demons": "1f608", "enemy": "1f6ab", "evil": "1f6ab", "darkness": "🌑",
    "bless": "1f4ab", "blessing": "1f4ab", "blessed": "1f4ab", "favor": "1f4ab", "abundance": "1f33e", "overflow": "1f30a",
    "defender": "1f6e1", "shield": "1f6e1", "fortress": "1f3f0", "warrior": "2694", "fight": "2694", "fighting": "2694", "armor": "1f6e1", "victory": "1f3c6",

    # --- MONEY, FINANCE, BUSINESS & SUCCESS ---
    "money": "1f4b0", "cash": "1f4b5", "dollar": "1f4b5", "dollars": "1f4b5", "rich": "1f911", "wealth": "1f4b0", "wealthy": "1f4b0",
    "millionaire": "1f48e", "billionaire": "1f48e", "crypto": "1f4c8", "bitcoin": "1fa99", "invest": "1f4c8", "investment": "1f4c8",
    "profit": "1f4c8", "profits": "1f4c8", "revenue": "1f4c8", "gains": "1f4c8", "expensive": "1f48e", "luxury": "1f48e",
    "gold": "1fa99", "diamond": "1f48e", "win": "1f3c6", "winner": "1f3c6", "winning": "1f3c6", "champion": "1f3c6", "trophy": "1f3c6",
    "king": "1f451", "queen": "1f451", "royal": "1f451", "crown": "1f451", "leader": "1f451", "boss": "1f4bc", "ceo": "1f4bc", "business": "1f4bc",

    # --- MIND, BODY, STRENGTH & ENERGY ---
    "brain": "1f9e0", "mind": "1f9e0", "think": "1f4a1", "thinking": "1f4a1", "smart": "1f9e0", "idea": "1f4a1", "inspired": "1f4a1", "inspire": "1f4a1",
    "strong": "1f4aa", "strength": "1f4aa", "gym": "1f3cb", "muscle": "1f4aa", "workout": "1f3cb", "power": "26a1", "powerful": "26a1",
    "heart": "2764", "love": "2764", "care": "2764", "passion": "1f525", "soul": "2728",
    "lightning": "26a1", "electric": "26a1", "electricity": "26a1", "energy": "26a1", "spark": "26a1",
    "fast": "1f680", "speed": "26a1", "quick": "26a1", "rocket": "1f680", "launch": "1f680", "blast": "1f680",

    # --- EMOTIONS, REACTIONS & VIRAL HOOKS ---
    "crazy": "1f92f", "insane": "1f92f", "wild": "1f92f", "shocking": "1f92f",
    "dead": "1f480", "dying": "1f480", "skull": "1f480", "rip": "1f480",
    "laugh": "1f602", "laughing": "1f602", "funny": "1f602", "hilarious": "1f602", "lol": "1f602",
    "cry": "1f62d", "crying": "1f62d", "tears": "1f62d", "sad": "1f62d",
    "shocked": "1f632", "wow": "1f632", "omg": "1f632", "surprise": "1f632", "surprised": "1f632",
    "secret": "1f92b", "quiet": "1f92b", "silent": "1f92b", "hush": "1f92b", "whisper": "1f92b",
    "eye": "1f440", "eyes": "1f440",
    "hundred": "1f4af", "truth": "1f4af", "real": "1f4af", "facts": "1f4af", "fact": "1f4af",
    "star": "2b50", "famous": "2b50", "celebrity": "2b50", "shine": "2728",
    "gift": "1f381", "present": "1f381", "free": "1f381", "bonus": "1f381",

    # --- ACTIONS, OBJECTS, TRAVEL & WARNINGS ---
    "car": "1f697", "drive": "1f697", "driving": "1f697", "vehicle": "1f697",
    "house": "1f3e0", "home": "1f3e0", "building": "1f3e2", "mansion": "1f3f0",
    "phone": "1f4f1", "call": "1f4de", "text": "1f4ac",
    "music": "1f3b5", "song": "1f3b6", "sing": "1f3a4",
    "danger": "26a0", "warning": "26a0", "alert": "1f6a8", "hazard": "26a0",
    "target": "1f3af", "goal": "1f3af", "aim": "1f3af", "focus": "1f3af",
    "earth": "1f30d", "world": "1f30d", "global": "1f310", "international": "1f310"
}

def get_emoji_hex(raw_word):
    """Returns the hex code for a word if matched, else None."""
    if not raw_word:
        return None
    cleaned = re.sub(r'[^\w\s]', '', str(raw_word)).strip().lower()
    return EMOJI_HEX_MAP.get(cleaned, None)

def fetch_emoji_png(hex_code, size=140):
    """Downloads high-res 140px color emoji PNG from Twemoji CDN and formats it."""
    filename = f"sticker_{hex_code}.png"
    if os.path.exists(filename):
        return filename
    try:
        url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{hex_code}.png"
        raw_tmp = f"raw_{hex_code}.png"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(raw_tmp, 'wb') as out_f:
            out_f.write(resp.read())

        cmd = [
            "ffmpeg", "-y", "-i", raw_tmp,
            "-vf", f"scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=black@0",
            "-pix_fmt", "rgba", filename
        ]
        subprocess.run(cmd, check=True)
        if os.path.exists(raw_tmp):
            os.remove(raw_tmp)
        return filename
    except Exception as e:
        print(f"Warning: Could not fetch emoji {hex_code}: {e}")
        return None
