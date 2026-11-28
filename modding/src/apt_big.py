from struct import pack_into, unpack_from


def read_index(big):
    total, = unpack_from("<I", big, 4)
    count, header_size = unpack_from(">II", big, 8)
    assert big[:4] == b"BIGF" and total == len(big)
    entries = {}
    position = 16
    for _ in range(count):
        offset, size = unpack_from(">II", big, position)
        end = big.index(0, position + 8, header_size + 1)
        name = big[position + 8:end]
        assert name not in entries and header_size <= offset <= offset + size <= len(big)
        entries[name] = (position, offset, size)
        position = end + 1
    return entries, header_size


def member_bytes(big, entry):
    _, offset, size = entry
    return big[offset:offset + size]


def replace_members(original, entries, header_size, changes):
    rebuilt = bytearray(original[:header_size])
    end = header_size
    for name, (index, start, size) in sorted(entries.items(), key=lambda item: item[1][1]):
        assert end <= start
        rebuilt.extend(original[end:start])
        payload = changes.get(name, original[start:start + size])
        pack_into(">II", rebuilt, index, len(rebuilt), len(payload))
        rebuilt.extend(payload)
        end = start + size
    rebuilt.extend(original[end:])
    pack_into("<I", rebuilt, 4, len(rebuilt))
    return bytes(rebuilt)


