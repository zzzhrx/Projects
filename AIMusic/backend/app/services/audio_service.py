import os
import subprocess
from app.config import settings
from app.services.music_service import music_service


class AudioService:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def abc_to_midi_file(self, abc_notation: str, filename: str = "output.mid") -> str:
        midi_path = os.path.join(self.output_dir, filename)
        music_service.abc_to_midi_file(abc_notation, midi_path, instrument="钢琴")
        return midi_path

    def midi_to_wav(self, midi_path: str, output_filename: str = "output.wav") -> str:
        audio_path = os.path.join(self.output_dir, output_filename)

        # Try fluidsynth with common SoundFont paths
        soundfont_paths = [
            "/usr/share/sounds/sf2/FluidR3_GM.sf2",
            "/usr/share/sounds/sf2/TimGM6mb.sf2",
            "/usr/local/share/sounds/sf2/FluidR3_GM.sf2",
            os.path.expanduser("~/.fluidsynth/default.sf2"),
            "/opt/homebrew/share/sounds/sf2/FluidR3_GM.sf2",
        ]

        soundfont = None
        for sf_path in soundfont_paths:
            if os.path.exists(sf_path):
                soundfont = sf_path
                break

        if soundfont is None:
            raise RuntimeError(
                "未找到 SoundFont 文件。请安装 fluidsynth 和 SoundFont：\n"
                "  macOS: brew install fluidsynth fluid-soundfont\n"
                "  Ubuntu: sudo apt install fluidsynth fluid-soundfont-gm"
            )

        try:
            subprocess.run(
                ["fluidsynth", "-ni", "-F", audio_path, soundfont, midi_path],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "未找到 fluidsynth。请安装：\n"
                "  macOS: brew install fluidsynth\n"
                "  Ubuntu: sudo apt install fluidsynth"
            ) from None

        return audio_path

    def abc_to_audio(self, abc_notation: str, output_filename: str = "output.wav") -> str:
        midi_path = self.abc_to_midi_file(abc_notation, "temp_render.mid")
        audio_path = self.midi_to_wav(midi_path, output_filename)
        # Clean up temp MIDI file
        try:
            os.unlink(midi_path)
        except OSError:
            pass
        return audio_path


audio_service = AudioService()
