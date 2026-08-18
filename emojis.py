import re

# Curated 200+ keyword-to-emoji mapping
EMOJI_DICTIONARY = {
    # --- CHURCH, CHRISTIANITY, FAITH, WORSHIP & MINISTRY ---
    "church": "⛪", "cathedral": "⛪", "chapel": "⛪", "temple": "⛪", "altar": "⛪", "sanctuary": "⛪",
    "god": "✝️", "jesus": "✝️", "christ": "✝️", "lord": "👑", "savior": "✝️", "messiah": "✝️", "yahweh": "✝️",
    "pray": "🙏", "prayer": "🙏", "prayers": "🙏", "praying": "🙏", "amen": "🙏", "intercession": "🙏", "supplication": "🙏",
    "bible": "📖", "scripture": "📖", "scriptures": "📖", "gospel": "📖", "verse": "📖", "testament": "📖",
    "faith": "🕊️", "believe": "🕊️", "believer": "🕊️", "belief": "🕊️", "trust": "🕊️", "hope": "🕊️",
    "holy": "🕊️", "spirit": "🕊️", "ghost": "🕊️", "anointing": "🕊️", "anointed": "🕊️", "presence": "🕊️",
    "glory": "✨", "glorious": "✨", "greater": "🌟", "praise": "🙌", "worship": "🙌", "hallelujah": "🙌", "hosanna": "🙌", "exalt": "🙌",
    "revival": "🔥", "crusade": "🔥", "fire": "🔥", "flame": "🔥", "breakthrough": "⚡",
    "miracle": "✨", "miracles": "✨", "wonder": "✨", "wonders": "✨", "sign": "✨", "heal": "✨", "healing": "✨", "deliverance": "✨",
    "pastor": "🎙️", "priest": "⛪", "bishop": "⛪", "minister": "🎙️", "preacher": "🎙️", "apostle": "📜", "prophet": "📜",
    "cross": "✝️", "crucifix": "✝️", "salvation": "✝️", "redeemed": "✝️", "grace": "🕊️", "mercy": "🕊️",
    "heaven": "👼", "angel": "👼", "angels": "👼", "celestial": "☁️", "paradise": "☁️", "eternal": "♾️",
    "devil": "😈", "satan": "😈", "demon": "😈", "demons": "😈", "enemy": "🚫", "evil": "🚫", "darkness": "🌑",
    "bless": "💫", "blessing": "💫", "blessed": "💫", "favor": "💫", "abundance": "🌾", "overflow": "🌊",
    "defender": "🛡️", "shield": "🛡️", "fortress": "🏰", "warrior": "⚔️", "fight": "⚔️", "armor": "🛡️", "victory": "🏆",

    # --- MONEY, FINANCE, BUSINESS & SUCCESS ---
    "money": "💰", "cash": "💵", "dollar": "💵", "dollars": "💵", "rich": "🤑", "wealth": "💰", "wealthy": "💰",
    "millionaire": "💎", "billionaire": "💎", "crypto": "📈", "bitcoin": "🪙", "invest": "📈", "investment": "📈",
    "profit": "📈", "profits": "📈", "revenue": "📈", "gains": "📈", "expensive": "💎", "luxury": "💎",
    "gold": "🪙", "diamond": "💎", "win": "🏆", "winner": "🏆", "winning": "🏆", "champion": "🏆", "trophy": "🏆",
    "king": "👑", "queen": "👑", "royal": "👑", "crown": "👑", "leader": "👑", "boss": "💼", "ceo": "💼", "business": "💼",

    # --- MIND, BODY, STRENGTH & ENERGY ---
    "brain": "🧠", "mind": "🧠", "think": "💡", "thinking": "💡", "smart": "🧠", "intelligent": "🧠", "idea": "💡",
    "strong": "💪", "strength": "💪", "gym": "🏋️", "muscle": "💪", "workout": "🏋️", "power": "⚡", "powerful": "⚡",
    "heart": "❤️", "love": "❤️", "care": "❤️", "passion": "🔥", "soul": "✨",
    "lightning": "⚡", "electric": "⚡", "electricity": "⚡", "energy": "⚡", "spark": "⚡",
    "fast": "🚀", "speed": "⚡", "quick": "⚡", "rocket": "🚀", "launch": "🚀", "blast": "🚀",

    # --- EMOTIONS, REACTIONS & VIRAL HOOKS ---
    "crazy": "🤯", "insane": "🤯", "wild": "🤯", "unbelievable": "🤯", "shocking": "🤯",
    "dead": "💀", "dying": "💀", "skull": "💀", "rip": "💀",
    "laugh": "😂", "laughing": "😂", "funny": "😂", "hilarious": "😂", "lol": "😂",
    "cry": "😭", "crying": "😭", "tears": "😭", "sad": "😭",
    "shocked": "😲", "wow": "😲", "omg": "😲", "surprise": "😲", "surprised": "😲",
    "secret": "🤫", "quiet": "🤫", "silent": "🤫", "hush": "🤫", "whisper": "🤫",
    "eye": "👀", "eyes": "👀", "look": "👀", "watch": "👀", "see": "👀",
    "hundred": "💯", "truth": "💯", "real": "💯", "facts": "💯", "fact": "💯",
    "star": "⭐", "famous": "⭐", "celebrity": "⭐", "shine": "✨",
    "gift": "🎁", "present": "🎁", "free": "🎁", "bonus": "🎁",

    # --- ACTIONS, TIME, OBJECTS & WARNINGS ---
    "time": "⏰", "clock": "⏰", "hour": "⏰", "minute": "⏱️", "second": "⏱️", "late": "⌛", "early": "🌅",
    "car": "🚗", "drive": "🚗", "driving": "🚗", "lambo": "🏎️", "ferrari": "🏎️", "vehicle": "🚗",
    "house": "🏠", "home": "🏠", "building": "🏢", "mansion": "🏰",
    "phone": "📱", "call": "📞", "text": "💬", "message": "💬",
    "music": "🎵", "song": "🎶", "sound": "🔊", "audio": "🎙️", "voice": "🎙️", "sing": "🎤",
    "danger": "⚠️", "warning": "⚠️", "alert": "🚨", "hazard": "⚠️",
    "stop": "🛑", "halt": "🛑", "pause": "⏸️",
    "no": "❌", "wrong": "❌", "false": "❌", "fake": "🚫", "error": "⚠️", "lie": "🤥",
    "target": "🎯", "goal": "🎯", "aim": "🎯", "focus": "🎯",
    "earth": "🌍", "world": "🌍", "global": "🌍", "international": "🌐"
}

def get_emoji(raw_word):
    """Cleans a word and looks up a matching emoji."""
    if not raw_word:
        return ""
    # Strip punctuation and convert to lowercase
    cleaned = re.sub(r'[^\w\s]', '', str(raw_word)).strip().lower()
    return EMOJI_DICTIONARY.get(cleaned, "")
