import music21
import tempfile
import os
import re
from app.config import settings


class MusicService:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_abc(self, abc_notation: str) -> music21.stream.Stream:
        return music21.converter.parseData(abc_notation, format="abc")

    def normalize_abc_block(self, abc_notation: str) -> str:
        cleaned = abc_notation.strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        header_match = re.search(r"^(X:|T:|M:|L:|Q:|K:)", cleaned, re.MULTILINE)
        if header_match:
            cleaned = cleaned[header_match.start():]

        return cleaned.strip()

    def split_abc_tracks(self, abc_notation: str, instrument: str = "钢琴") -> tuple[str, str]:
        sections = re.split(r"^\s*===\s*(.+?)\s*===\s*$", abc_notation, flags=re.MULTILINE)
        vocal_abc = ""
        instrument_abc = ""

        if len(sections) >= 3:
            for index in range(1, len(sections), 2):
                title = sections[index].strip()
                content = self.normalize_abc_block(sections[index + 1])
                if not content:
                    continue

                title_lower = title.lower()
                if "人声" in title or "vocal" in title_lower:
                    vocal_abc = content
                elif instrument in title or "伴奏" in title or "instrument" in title_lower:
                    instrument_abc = content
                elif not vocal_abc:
                    vocal_abc = content
                elif not instrument_abc:
                    instrument_abc = content

        if not vocal_abc and not instrument_abc:
            normalized = self.normalize_abc_block(abc_notation)
            tunes = [chunk.strip() for chunk in re.split(r"(?=^X:\d+\s*$)", normalized, flags=re.MULTILINE) if chunk.strip()]
            if len(tunes) >= 2:
                vocal_abc = tunes[0]
                instrument_abc = tunes[1]
            else:
                vocal_abc = normalized

        return vocal_abc, instrument_abc

    def combine_abc_tracks(self, vocal_abc: str, instrument_abc: str) -> str:
        return "\n\n".join(part for part in [vocal_abc.strip(), instrument_abc.strip()] if part)

    def _extract_abc_header(self, abc_str: str) -> dict:
        """Extract tempo, key, meter from ABC header."""
        info = {"tempo": 72, "key": "C", "meter": "4/4"}
        for line in abc_str.split("\n"):
            line = line.strip()
            if line.startswith("Q:"):
                m = re.search(r"(\d+)", line)
                if m:
                    info["tempo"] = int(m.group(1))
            elif line.startswith("K:"):
                info["key"] = line[2:].strip()
            elif line.startswith("M:"):
                info["meter"] = line[2:].strip()
        return info

    def extract_lyrics_from_abc(self, abc_str: str) -> list[str]:
        """Extract lyric phrases from ABC w: lines."""
        return self._extract_lyrics_from_abc(abc_str)

    def _extract_lyrics_from_abc(self, abc_str: str) -> list[str]:
        """Extract lyric phrases from ABC w: lines, joining continuations."""
        lyric_words: list[str] = []
        for line in abc_str.split("\n"):
            stripped = line.strip()
            if stripped.startswith("w:"):
                words = stripped[2:].strip()
                lyric_words.append(words)
        all_text = " ".join(lyric_words)
        phrases = [p.strip() for p in all_text.split("*") if p.strip()]
        return phrases

    def _get_instrument_program(self, instrument: str) -> int:
        """Map instrument name to General MIDI program number."""
        mapping = {
            "钢琴": 0,    # Acoustic Grand Piano
            "古筝": 107,  # Koto (closest GM instrument)
            "小提琴": 40, # Violin
        }
        return mapping.get(instrument, 0)

    def abc_to_midi_file(
        self,
        abc_notation: str,
        output_path: str,
        instrument: str = "钢琴",
        vocal_lyrics: list[str] | None = None,
    ):
        """Convert ABC to MIDI with proper instrument sounds and lyrics.

        Strategy: use music21's built-in streamToMidiFile for basic conversion,
        then post-process the MIDI to inject program changes and lyrics.
        """
        # Split by X: directive and parse each tune separately
        tunes = re.split(r"(?=^X:\d+)", abc_notation, flags=re.MULTILINE)
        tunes = [t.strip() for t in tunes if t.strip()]

        if len(tunes) == 0:
            raise ValueError("No ABC content found")

        # Auto-extract lyrics from vocal ABC (first tune)
        if vocal_lyrics is None and len(tunes) >= 1:
            vocal_lyrics = self._extract_lyrics_from_abc(tunes[0])

        # Parse each tune individually and convert to MIDI streams
        streams = []
        for tune in tunes:
            try:
                s = music21.converter.parseData(tune, format="abc")
                streams.append(s)
            except Exception:
                continue

        if len(streams) == 0:
            raise ValueError("Failed to parse any ABC tunes")

        # Create combined score with proper instrument assignments and lyrics
        import struct
        from music21.midi import translate as midi_translate

        combined = music21.stream.Score()
        for i, s in enumerate(streams):
            for part in s.parts:
                np = music21.stream.Part()
                # Insert program change
                if i == 0:
                    inst_obj = music21.instrument.instrumentFromMidiProgram(53)
                else:
                    prog = self._get_instrument_program(instrument)
                    inst_obj = music21.instrument.instrumentFromMidiProgram(prog)
                np.insert(0, inst_obj)

                # Add lyrics to vocal notes
                notes_list = list(part.flatten().notesAndRests)
                if i == 0 and vocal_lyrics:
                    lyric_idx = 0
                    # Assign one lyric phrase per note
                    for el in notes_list:
                        if el.isNote and lyric_idx < len(vocal_lyrics):
                            el.lyric = vocal_lyrics[lyric_idx]
                            lyric_idx += 1
                        np.coreAppend(el)
                else:
                    for el in notes_list:
                        np.coreAppend(el)
                combined.insert(0, np)

        # Convert to MIDI
        mf = midi_translate.streamToMidiFile(combined)

        mf.open(output_path, 'wb')
        mf.write()
        mf.close()

    def abc_to_midi_bytes(
        self,
        abc_notation: str,
        instrument: str = "钢琴",
        vocal_lyrics: list[str] | None = None,
    ) -> bytes:
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            self.abc_to_midi_file(abc_notation, tmp.name, instrument, vocal_lyrics)
            tmp.seek(0)
            data = tmp.read()
        os.unlink(tmp.name)
        return data

    def generate_accompaniment_abc(
        self, vocal_abc: str, instrument: str = "钢琴", tempo: int = 72
    ) -> str:
        """Generate a musically varied accompaniment from vocal melody using music21."""
        try:
            vocal_stream = self.parse_abc(vocal_abc)
        except Exception:
            return self._fallback_accompaniment(vocal_abc, instrument, tempo)

        key_sig = vocal_stream.flat.getElementsByClass(music21.key.KeySignature)
        key_name = "C"
        if key_sig:
            ks = key_sig[0]
            key_name = ks.name if ks.name != "C" else f"{ks.sharps}#"
            if ks.sharps < 0:
                key_name = f"{-ks.sharps}b"

        notes = list(vocal_stream.flat.notesAndRests)
        # Determine chord per measure (approximate by splitting into equal chunks)
        measure_count = max(8, len(notes) // 4)
        chords_per_row = 4

        chord_map = {
            "C":  ["C4 E4 G4",  "C4 E4 G4",  "C E G c",   "E G c e"],
            "Dm": ["D4 F4 A4",  "D4 F4 A4",  "D F A d",   "F A d f"],
            "Em": ["E4 G4 B4",  "E4 G4 B4",  "E G B e",   "G B e g"],
            "F":  ["F4 A4 c4",  "F4 A4 c4",  "F A c f",   "A c f a"],
            "Gm": ["G4 B4 d4",  "G4 B4 d4",  "G B d g",   "B d g b"],
            "Am": ["A4 c4 e4",  "A4 c4 e4",  "A c e a",   "c e a c'"],
            "Bd": ["B4 d4 f4",  "B4 d4 f4",  "B d f b",   "d f b d'"],
        }

        progression = ["Dm", "Am", "Gm", "Dm", "F", "Am", "Gm", "Dm",
                       "F", "Am", "Gm", "Dm", "F", "Am", "Gm", "Dm"]
        if len(progression) < measure_count:
            progression = (progression * ((measure_count // len(progression)) + 1))[:measure_count]
        else:
            progression = progression[:measure_count]

        abc_lines = [
            f"X:2",
            f"T:{instrument}伴奏",
            f"M:4/4",
            f"L:1/8",
            f"Q:1/4={tempo}",
            f"K:{key_name}",
            f"%%staves [1]",
            f'V:1 clef=treble name="{instrument}"',
        ]

        total_bars = 0
        for i, chord_name in enumerate(progression):
            if total_bars >= measure_count:
                break
            patterns = chord_map.get(chord_name, chord_map["Dm"])
            pattern = patterns[i % len(patterns)]
            # Create rhythmic variation: each measure is a broken chord
            bar = f"[{pattern}] z2 [{pattern}] z2 |"
            abc_lines.append(bar)
            total_bars += 1

        return "\n".join(abc_lines)

    def _fallback_accompaniment(self, vocal_abc: str, instrument: str, tempo: int) -> str:
        """Generate a simple broken-chord accompaniment when music21 parsing fails."""
        chord_map = {
            "Dm": ["[D4F4A4]", "[F4A4d4]", "[D F A d]", "[F A d f]"],
            "Am": ["[A,4C4E4]", "[C4E4A4]", "[A, C E A]", "[C E A c]"],
            "Gm": ["[G,4B,4D4]", "[B,4D4G4]", "[G, B, D G]", "[B, D G B]"],
            "C":  ["[C4E4G4]",  "[E4G4c4]",  "[C E G c]",  "[E G c e]"],
            "F":  ["[F,4A,4C4]", "[A,4C4F4]", "[F, A, C F]", "[A, C F A]"],
            "Bb": ["[B,4D4F4]", "[D4F4B4]", "[B, D F B]", "[D F B d]"],
        }
        progression = ["Dm", "Am", "Gm", "Dm", "F", "C", "Gm", "Am",
                       "Dm", "Am", "Gm", "Dm", "F", "C", "Am", "Dm"]
        pattern_idx = 0
        bars = []
        for chord in progression[:16]:
            chord_patterns = chord_map.get(chord, chord_map["Dm"])
            pat = chord_patterns[pattern_idx % len(chord_patterns)]
            bars.append(f"{pat} z2 {pat} z2 |")
            pattern_idx += 1

        header = [
            f"X:2",
            f"T:{instrument}伴奏",
            f"M:4/4",
            f"L:1/8",
            f"Q:1/4={tempo}",
            f"K:C",
            f"%%staves [1]",
            f'V:1 clef=treble name="{instrument}"',
        ]
        return "\n".join(header + bars)

    def abc_to_midi(self, abc_notation: str, filename: str = "output.mid") -> str:
        score = self.parse_abc(abc_notation)
        midi_path = os.path.join(self.output_dir, filename)
        mf = music21.midi.translate.streamToMidiFile(score)
        mf.open(midi_path, "wb")
        mf.write()
        mf.close()
        return midi_path


music_service = MusicService()
