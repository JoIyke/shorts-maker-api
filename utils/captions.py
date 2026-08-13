import os

def ms_to_ass_time(ms):
    """Converts milliseconds (1250) to ASS format (0:00:01.25)"""
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    centiseconds = int(milliseconds / 10)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

def generate_ass_subtitles(words, caption_style="hormozi", output_file="subtitles.ass"):
    if not words:
        return None

    # Style Options
    if caption_style == "hormozi":
        font_size = 75
        primary_color = "&H00FFFFFF&"  # White
        outline_color = "&H00000000&"  # Black
        vertical_margin = 280
    elif caption_style == "red_bold":
        font_size = 85
        primary_color = "&H000000FF&"  # Red
        outline_color = "&H00FFFFFF&"  # White
        vertical_margin = 280
    else:  # classic
        font_size = 65
        primary_color = "&H00FFFFFF&"
        outline_color = "&H00000000&"
        vertical_margin = 220

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortCap,Impact,{font_size},{primary_color},&H00000000,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,10,10,{vertical_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []
    chunk_size = 3  # Group words in chunks of 3 for smooth reading

    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue

        chunk_start = chunk[0]['start']
        chunk_end = chunk[-1]['end']

        start_str = ms_to_ass_time(chunk_start)
        end_str = ms_to_ass_time(chunk_end)

        line_text = " ".join([w['text'].upper() for w in chunk])
        dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},ShortCap,,0,0,0,,{line_text}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(dialogue_lines))

    print(f"Subtitles generated successfully: {output_file}")
    return output_file
