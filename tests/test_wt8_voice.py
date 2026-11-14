"""Unit tests for offline Australian annunciation; no audio device needed."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import wave
from wt8_voice import VoiceAnnunciator, canonical_state, phrase_path


class VoiceTests(unittest.TestCase):
    def test_state_normalisation(self):
        self.assertEqual(canonical_state("MANUAL (AZ+ + EL+)"), "manual")
        self.assertEqual(canonical_state("PARKING"), "parking")
        self.assertEqual(canonical_state("SLEW TIMEOUT"), "slew timeout")
        self.assertIsNone(canonical_state("unknown 123"))

    def test_east_west_prefix_and_no_arbitrary_file_names(self):
        root = Path("/tmp/voice_test")
        self.assertEqual(phrase_path("East", "TRACKING", root),
                         root / "east_tracking.wav")
        self.assertEqual(phrase_path("West", "SERVICE", root),
                         root / "west_service.wav")
        self.assertIsNone(phrase_path("../other", "TRACKING", root))
        self.assertIsNone(phrase_path("East", "../../etc", root))

    def test_volume_pcm(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(22050)
                output.writeframes((10000).to_bytes(2, "little", signed=True) * 4)
            silent = VoiceAnnunciator._volume_adjusted_wav(path, 0)
            self.assertIn(bytes(8), silent)
            original = VoiceAnnunciator._volume_adjusted_wav(path, 100)
            self.assertIn((10000).to_bytes(2, "little", signed=True) * 4, original)

    def test_phrase_matches_display_state(self):
        from wt8_voice import PHRASES
        self.assertEqual(PHRASES["service"], "service")
        self.assertEqual(PHRASES["scan"], "scan")
        self.assertEqual(PHRASES["yfactor"], "Y factor")

    def test_obsolete_announcements_are_invalidated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("east_tracking.wav", "east_stopped.wav", "east_test.wav"):
                (root / name).write_bytes(b"dummy")
            with patch("wt8_voice.shutil.which", return_value="/usr/bin/aplay"):
                voice = VoiceAnnunciator(root)
            try:
                voice.set_muted(False)
                self.assertTrue(voice.announce("East", "TRACKING"))
                self.assertTrue(voice.announce("East", "STOPPED"))
                self.assertEqual(voice._latest_announcements["east"], 2)
            finally:
                voice.close()

    def test_missing_pack_fails_silently(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("wt8_voice.shutil.which", return_value="/usr/bin/aplay"):
                voice = VoiceAnnunciator(directory)
            try:
                self.assertFalse(voice.ready)
                voice.set_muted(False)
                self.assertFalse(voice.announce("East", "TRACKING"))
            finally:
                voice.close()


if __name__ == "__main__":
    unittest.main()
