"""Offline acceptance checks for MIDI boundaries and verification failures."""
import copy
import tempfile
from pathlib import Path
import unittest

import midi_plan as midi


class MidiPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'bpm': 148, 'length_qn': 8, 'notes': [
            {'start_qn': 0, 'end_qn': 4, 'pitch': 60, 'velocity': 85},
            {'start_qn': 4, 'end_qn': 7.5, 'pitch': 60, 'velocity': 80}]}
        self.read = {'note_count': 2, 'truncated': False, 'ppq_per_quarter': 480,
                     'notes': [dict(ppq=0, end_ppq=1920, pitch=60, velocity=85, channel=0, muted=False),
                               dict(ppq=1920, end_ppq=3600, pitch=60, velocity=80, channel=0, muted=False)]}

    def test_readback_resolution_conversion(self):
        self.assertEqual(midi.verify(self.plan, {'ok': True, 'data': self.read}), 2)

    def test_reaper_shortened_end_is_failure(self):
        self.read['notes'][0]['end_ppq'] -= 1
        with self.assertRaises(ValueError):
            midi.verify(self.plan, self.read)

    def test_channel_and_muted_and_truncation_fail(self):
        for key, value in [('channel', 1), ('muted', True), ('velocity', 30)]:
            read = copy.deepcopy(self.read)
            read['notes'][0][key] = value
            with self.assertRaises(ValueError):
                midi.verify(self.plan, read)
        self.read['truncated'] = True
        with self.assertRaises(ValueError):
            midi.verify(self.plan, self.read)

    def test_overlap_and_bad_time_fail(self):
        for start in [3.9, -1, float('nan')]:
            plan = copy.deepcopy(self.plan)
            plan['notes'][1]['start_qn'] = start
            with self.assertRaises(ValueError):
                midi.validate(plan)

    def test_chords_allowed_but_collapsed_notes_fail(self):
        self.plan['notes'][1].update(start_qn=0, pitch=67)
        self.assertEqual(len(midi.validate(self.plan)), 2)
        self.plan['notes'][1].update(end_qn=.00001)
        with self.assertRaises(ValueError):
            midi.validate(self.plan)

    def test_actual_file_event_order_and_end(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'part.mid'
            midi.write(self.plan, path)
            data = path.read_bytes()
            self.assertEqual(data[:14], bytes.fromhex('4d546864000000060000000103c0'))
            self.assertEqual(int.from_bytes(data[18:22], 'big'), len(data) - 22)
            # At the shared boundary, note-off precedes note-on with zero delta.
            self.assertIn(bytes([0x80, 60, 0, 0, 0x90, 60, 80]), data)
            self.assertTrue(data.endswith(bytes([0x83, 0x60, 0xff, 0x2f, 0])))
            with self.assertRaises(FileExistsError):
                midi.write(self.plan, path)
            self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
