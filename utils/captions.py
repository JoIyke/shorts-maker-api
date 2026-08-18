import os
import random
from utils import emojis

CAPTION_STYLES = [
    'hormozi_yellow',
    'beast_green',
    'cyber_cyan',
    'fire_orange',
    'clean_minimal',
    'boxed_badge'
]

def ms_to_ass_time(ms):
    seconds, milliseconds = divmod(int(ms), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    centiseconds = int(milliseconds / 10)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

def generate_ass_subtitles(words, caption_style=None, output_file="subtitles.ass", res_x=1080, res_y=1920):
    if not words:
        return None, []

    if not caption_style or caption_style == 'random':
        caption_style = random.choice(CAPTION_STYLES)
        print(f"Random Caption Style Selected: '{caption_style}'")
    else:
        caption_style = caption_style.lower()

    margin_v = int(res_y * 0.15)
    font_size = int(res_x * 0.072)
    border_style = 1
    outline_width = 4
    shadow_depth = 2

    if caption_style in ['hormozi_yellow', 'hormozi']:
        highlight_color = "&H0000FFFF&"  # Electric Yellow
        inactive_color = "&H00FFFFFF&"   # White
        outline_color = "&H00000000&"
    elif caption_style == 'beast_green':
        highlight_color = "&H0014FF39&"  # Neon Green
        inactive_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"
    elif caption_style == 'cyber_cyan':
        highlight_color = "&H00FFFF00&"  # Cyan
        inactive_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"
    elif caption_style in ['fire_orange', 'red_bold']:
        highlight_color = "&H000045FF&"  # Orange
        inactive_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"
    elif caption_style == 'clean_minimal':
        highlight_color = "&H00FFFFFF&"  # White
        inactive_color = "&H00888888&"   # Muted Grey
        outline_color = "&H00000000&"
        outline_width = 2
        shadow_depth = 0
    elif caption_style == 'boxed_badge':
        highlight_color = "&H0000FFFF&"
        inactive_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"
        border_style = 3
        outline_width = 8
    else:
        highlight_color = "&H0000FFFF&"
        inactive_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortCap,Anton,{font_size},{inactive_color},&H00000000,{outline_color},&H90000000,-1,0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_depth},2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []
    emoji_events = []
    chunk_size = 3

    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue

        for j, active_word in enumerate(chunk):
            slice_start = float(active_word['start'])
            if j < len(chunk) - 1:
                slice_end = float(chunk[j + 1]['start'])
            else:
                slice_end = float(active_word['end'])

            start_str = ms_to_ass_time(slice_start)
            end_str = ms_to_ass_time(slice_end)

            # Check if this focused active word has a matching emoji
            hex_code = emojis.get_emoji_hex(active_word['text'])
            if hex_code:
                emoji_events.append({
                    "hex": hex_code,
                    "start": slice_start / 1000.0,
                    "end": slice_end / 1000.0,
                    "chunk_idx": j,
                    "chunk_len": len(chunk)
                })

            line_parts = []
            for k, w in enumerate(chunk):
                # Clean text: ONLY uppercase letters/numbers, NO raw emoji unicode
                raw_text = str(w['text']).upper().strip()

                if k == j:
                    # SPRING POP ANIMATION: Pops in at 125% and springs to 100% in 100ms
                    bounce_tag = r"{\fscx125\fscy125\t(0,100,\fscx100\fscy100)}"
                    line_parts.append(f"{bounce_tag}{{\\c{highlight_color}}}{raw_text}{{\\r}}")
                else:
                    line_parts.append(f"{{\\c{inactive_color}}}{raw_text}")

            full_line_text = " ".join(line_parts)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},ShortCap,,0,0,0,,{full_line_text}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(dialogue_lines))

    print(f"Generated Clean Subtitles with {len(emoji_events)} Floating Emoji Events: {output_file}")
    return output_file, emoji_events
