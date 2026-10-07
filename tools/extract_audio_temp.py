import struct
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit("Usage: python extract_audio_temp.py <input-video> [output.m4a]")
source = Path(sys.argv[1]).expanduser()
output = (Path(sys.argv[2]).expanduser() if len(sys.argv) > 2
          else Path(__file__).resolve().parents[1] / "site" / "assets" / "audio" / "background-music.m4a")
data = source.read_bytes()

def boxes(start, end):
    pos = start
    while pos + 8 <= end:
        size, kind = struct.unpack_from(">I4s", data, pos)
        header = 8
        if size == 1:
            size = struct.unpack_from(">Q", data, pos + 8)[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            break
        yield pos, size, kind.decode("latin1"), header
        pos += size

def children(box):
    pos, size, _, header = box
    return list(boxes(pos + header, pos + size))

def find(box, kind):
    return next(child for child in children(box) if child[2] == kind)

def table(box, count_size=4):
    pos, _, _, header = box
    payload = pos + header
    count = struct.unpack_from(">I", data, payload + 4)[0]
    return payload + 8, count

def descriptor(data_bytes, wanted):
    # MPEG-4 descriptor lengths are 7-bit continuation values.
    for start, value in enumerate(data_bytes):
        if value != wanted:
            continue
        offset, length = start + 1, 0
        for _ in range(4):
            if offset >= len(data_bytes):
                break
            byte = data_bytes[offset]
            offset += 1
            length = (length << 7) | (byte & 0x7f)
            if not byte & 0x80:
                if offset + length <= len(data_bytes) and 1 <= length <= 8:
                    return data_bytes[offset:offset + length]
                break
    raise ValueError("AAC decoder configuration not found")

moov = next(box for box in boxes(0, len(data)) if box[2] == "moov")
audio_track = None
for track in (box for box in children(moov) if box[2] == "trak"):
    mdia = find(track, "mdia")
    hdlr = find(mdia, "hdlr")
    if data[hdlr[0] + 16:hdlr[0] + 20] == b"soun":
        audio_track = mdia
        break
if audio_track is None:
    raise ValueError("No audio track found")

stbl = find(find(audio_track, "minf"), "stbl")
mdhd = find(audio_track, "mdhd")
mdhd_version = data[mdhd[0] + mdhd[3] + 0]
if mdhd_version == 0:
    audio_timescale = struct.unpack_from(">I", data, mdhd[0] + mdhd[3] + 12)[0]
else:
    audio_timescale = struct.unpack_from(">I", data, mdhd[0] + mdhd[3] + 20)[0]
stts = find(stbl, "stts")
stts_data, stts_count = table(stts)
timing = [struct.unpack_from(">II", data, stts_data + i * 8) for i in range(stts_count)]
duration = sum(count * delta for count, delta in timing)
stsd = find(stbl, "stsd")
entry_pos = stsd[0] + stsd[3] + 8
entry_size = struct.unpack_from(">I", data, entry_pos)[0]
entry_type = data[entry_pos + 4:entry_pos + 8]
if entry_type != b"mp4a":
    raise ValueError(f"Expected AAC/mp4a audio, found {entry_type!r}")
esds = next(box for box in boxes(entry_pos + 36, entry_pos + entry_size) if box[2] == "esds")
asc = descriptor(data[esds[0] + esds[3] + 4:esds[0] + esds[1]], 0x05)
object_type = asc[0] >> 3
frequency_index = ((asc[0] & 7) << 1) | (asc[1] >> 7)
channel_config = (asc[1] >> 3) & 0x0f
if object_type < 1 or frequency_index > 12:
    raise ValueError(f"Unsupported AAC AudioSpecificConfig: {asc.hex()}")

stsz = find(stbl, "stsz")
fixed_size = struct.unpack_from(">I", data, stsz[0] + stsz[3] + 4)[0]
sample_count = struct.unpack_from(">I", data, stsz[0] + stsz[3] + 8)[0]
if fixed_size:
    sizes = [fixed_size] * sample_count
else:
    sizes = list(struct.unpack_from(f">{sample_count}I", data, stsz[0] + stsz[3] + 12))

stco = next((box for box in children(stbl) if box[2] in ("stco", "co64")), None)
offset_data, chunk_count = table(stco)
offset_fmt = ">I" if stco[2] == "stco" else ">Q"
offset_size = 4 if stco[2] == "stco" else 8
chunk_offsets = [struct.unpack_from(offset_fmt, data, offset_data + i * offset_size)[0] for i in range(chunk_count)]

stsc = find(stbl, "stsc")
stsc_data, stsc_count = table(stsc)
stsc_entries = [struct.unpack_from(">III", data, stsc_data + i * 12) for i in range(stsc_count)]

samples = []
sample_index = 0
for chunk_number, chunk_offset in enumerate(chunk_offsets, start=1):
    mapping = max(entry for entry in stsc_entries if entry[0] <= chunk_number)
    per_chunk = mapping[1]
    offset = chunk_offset
    for _ in range(per_chunk):
        if sample_index >= len(sizes):
            break
        sample_size = sizes[sample_index]
        samples.append(data[offset:offset + sample_size])
        offset += sample_size
        sample_index += 1
if sample_index != sample_count or any(not sample for sample in samples):
    raise ValueError(f"Extracted {sample_index} of {sample_count} AAC samples")

def atom(kind, payload):
    return struct.pack(">I4s", len(payload) + 8, kind.encode("ascii")) + payload

def fullbox(kind, payload, version=0, flags=0):
    return atom(kind, bytes((version,)) + flags.to_bytes(3, "big") + payload)

matrix = struct.pack(">9I", 0x10000, 0, 0, 0, 0x10000, 0, 0, 0, 0x40000000)
mvhd_payload = (struct.pack(">IIII", 0, 0, audio_timescale, duration)
                + struct.pack(">IHH", 0x10000, 0x0100, 0) + bytes(8)
                + matrix + bytes(24) + struct.pack(">I", 2))
mvhd = fullbox("mvhd", mvhd_payload)
tkhd_payload = (struct.pack(">IIIII", 0, 0, 1, 0, duration) + bytes(8)
                + struct.pack(">hhhh", 0, 0, 0x0100, 0) + matrix + bytes(8))
tkhd = fullbox("tkhd", tkhd_payload, flags=7)
if mdhd_version == 0:
    mdhd_payload = struct.pack(">IIIIHH", 0, 0, audio_timescale, duration, 0x55c4, 0)
else:
    mdhd_payload = struct.pack(">QQIQHH", 0, 0, audio_timescale, duration, 0x55c4, 0)
mdhd_box = fullbox("mdhd", mdhd_payload, version=mdhd_version)
hdlr = fullbox("hdlr", struct.pack(">I4s12s", 0, b"soun", bytes(12)) + b"SoundHandler\0")
smhd = fullbox("smhd", struct.pack(">HH", 0, 0))
url = fullbox("url ", b"", flags=1)
dinf = atom("dinf", fullbox("dref", struct.pack(">I", 1) + url))
stsd_box = fullbox("stsd", struct.pack(">I", 1) + data[entry_pos:entry_pos + entry_size])
stts_box = fullbox("stts", struct.pack(">I", len(timing)) + b"".join(struct.pack(">II", *row) for row in timing))
stsc_box = fullbox("stsc", struct.pack(">IIII", 1, 1, sample_count, 1))
stsz_box = fullbox("stsz", struct.pack(">II", 0, sample_count) + b"".join(struct.pack(">I", len(sample)) for sample in samples))
sample_data = b"".join(samples)
ftyp = atom("ftyp", b"M4A \0\0\0\0M4A isommp42")

def make_moov(chunk_offset):
    stco_box = fullbox("stco", struct.pack(">II", 1, chunk_offset))
    stbl_box = atom("stbl", stsd_box + stts_box + stsc_box + stsz_box + stco_box)
    minf_box = atom("minf", smhd + dinf + stbl_box)
    mdia_box = atom("mdia", mdhd_box + hdlr + minf_box)
    trak_box = atom("trak", tkhd + mdia_box)
    return atom("moov", mvhd + trak_box)

moov = make_moov(0)
chunk_offset = len(ftyp) + len(moov) + 8
moov = make_moov(chunk_offset)
output.write_bytes(ftyp + moov + atom("mdat", sample_data))
print(f"Extracted {sample_count} AAC frames ({output.stat().st_size} bytes) to audio-only {output.name}")
