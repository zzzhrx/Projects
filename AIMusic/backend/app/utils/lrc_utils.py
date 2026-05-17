import re


def parse_lrc(lrc_content: str) -> list:
    lines = lrc_content.strip().split('\n')
    result = []
    for line in lines:
        match = re.match(r'\[(\d{2}:\d{2}\.\d{2,3})\](.*)', line)
        if match:
            time_str = match.group(1)
            text = match.group(2).strip()
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            time_ms = minutes * 60 * 1000 + int(seconds * 1000)
            result.append({"time": time_str, "time_ms": time_ms, "text": text})
    return result


def generate_lrc(lyrics_text: str) -> str:
    lines = lyrics_text.strip().split('\n')
    lrc_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'\[\d{2}:\d{2}\.\d{2,3}\]', line):
            lrc_lines.append(line)
        elif re.match(r'\[.*\]', line):
            lrc_lines.append(line)
        else:
            lrc_lines.append(line)
    return '\n'.join(lrc_lines)


def lyrics_to_lrc(lyrics_data: list) -> str:
    lines = []
    for item in lyrics_data:
        time_str = item.get("time", "00:00.00")
        text = item.get("text", "")
        lines.append(f"[{time_str}]{text}")
    return '\n'.join(lines)
