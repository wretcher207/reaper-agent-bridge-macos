"""Validate/write constant-tempo note plans; verify REAPER MIDI readback offline."""
import argparse
import json
import math
from pathlib import Path
import struct

PPQ = 960


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def integer(value, low, high, label):
    number(value, label)
    if int(value) != value or not low <= value <= high:
        raise ValueError(f"{label} must be an integer in {low}..{high}")
    return int(value)


def validate(plan):
    bpm = number(plan['bpm'], 'bpm')
    if bpm <= 0 or not 1 <= round(60000000 / bpm) <= 0xffffff:
        raise ValueError('bpm cannot be represented in MIDI')
    length = number(plan['length_qn'], 'length_qn')
    if length <= 0 or not 1 <= round(length * PPQ) <= 0xfffffff:
        raise ValueError('length_qn is outside supported MIDI bounds')
    name = plan.get('name', 'Arrangement MIDI')
    if not isinstance(name, str):
        raise ValueError('name must be a string')
    rows = []
    for note in plan['notes']:
        start = number(note['start_qn'], 'start_qn')
        end = number(note['end_qn'], 'end_qn')
        if not 0 <= start < end <= length:
            raise ValueError('note must have positive duration inside the item')
        start, end = round(start * PPQ), round(end * PPQ)
        if start >= end:
            raise ValueError('note collapses at 960 PPQ')
        rows.append((start, end, integer(note['pitch'], 0, 127, 'pitch'),
                     integer(note['velocity'], 1, 127, 'velocity'),
                     integer(note.get('channel', 0), 0, 15, 'channel')))
    if not rows:
        raise ValueError('plan has no notes')
    last_end = {}
    for start, end, pitch, _, channel in sorted(rows):
        key = channel, pitch
        if start < last_end.get(key, -1):
            raise ValueError(f'overlapping pitch {pitch} on channel {channel}')
        last_end[key] = end
    return sorted(rows)


def vlq(value):
    parts = [value & 127]
    value >>= 7
    while value:
        parts.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(parts)


def write(plan, output):
    rows = validate(plan)
    name = plan.get('name', 'Arrangement MIDI').encode('utf-8')
    events = [(0, -2, b'\xff\x51\x03' + round(60000000 / plan['bpm']).to_bytes(3, 'big')),
              (0, -1, b'\xff\x03' + vlq(len(name)) + name)]
    for start, end, pitch, velocity, channel in rows:
        events += [(start, 1, bytes([0x90 | channel, pitch, velocity])),
                   (end, 0, bytes([0x80 | channel, pitch, 0]))]
    events.append((round(plan['length_qn'] * PPQ), 2, b'\xff\x2f\x00'))
    previous = 0
    body = bytearray()
    for tick, _, message in sorted(events):
        body.extend(vlq(tick - previous) + message)
        previous = tick
    data = b'MThd' + struct.pack('>IHHH', 6, 0, 1, PPQ)
    data += b'MTrk' + struct.pack('>I', len(body)) + body
    with Path(output).open('xb') as stream:
        stream.write(data)
    return len(rows)


def verify(plan, result):
    expected = validate(plan)
    if result.get('ok') is False:
        raise ValueError('REAPER read failed')
    data = result.get('data', result)
    if data.get('truncated'):
        raise ValueError('readback is truncated')
    resolution = number(data['ppq_per_quarter'], 'readback PPQ')
    if resolution <= 0:
        raise ValueError('readback PPQ must be positive')
    if data['note_count'] != len(expected) or len(data['notes']) != len(expected):
        raise ValueError('note count mismatch')
    actual = []
    for note in data['notes']:
        if note['muted']:
            raise ValueError('a written note is muted')
        actual.append((number(note['ppq'], 'ppq') * PPQ / resolution,
                       number(note['end_ppq'], 'end_ppq') * PPQ / resolution,
                       integer(note['pitch'], 0, 127, 'pitch'),
                       integer(note['velocity'], 1, 127, 'velocity'),
                       integer(note['channel'], 0, 15, 'channel')))
    for wanted, got in zip(expected, sorted(actual)):
        if wanted[2:] != got[2:] or any(abs(wanted[i] - got[i]) > 1e-6 for i in (0, 1)):
            raise ValueError(f'note mismatch: expected {wanted}, received {got}')
    return len(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['write', 'verify'])
    parser.add_argument('plan', type=Path)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
        if args.operation == 'write':
            count = write(plan, args.target)
        else:
            count = verify(plan, json.loads(args.target.read_text(encoding='utf-8-sig')))
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        parser.exit(1, f'ERROR: {error}\n')
    print(f'{args.operation}: {count} notes; {args.target}')


if __name__ == '__main__':
    main()
