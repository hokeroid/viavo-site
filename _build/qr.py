#!/usr/bin/env python3
"""Minimal QR Code generator (byte mode, error correction M, versions 1-10) writing an SVG.

Follows ISO/IEC 18004 the way Nayuki's reference implementation does; no third-party packages.
Usage: qr.py <text> <out.svg>
"""
import sys

# per version 1..10, level M: (ec codewords per block, [(blocks, data codewords per block), ...])
EC_M = {1: (10, [(1, 16)]), 2: (16, [(1, 28)]), 3: (26, [(1, 44)]), 4: (18, [(2, 32)]), 5: (24, [(2, 43)]),
        6: (16, [(4, 27)]), 7: (18, [(4, 31)]), 8: (22, [(2, 38), (2, 39)]), 9: (22, [(3, 36), (2, 37)]),
        10: (26, [(4, 43), (1, 44)])}
ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42],
         9: [6, 26, 46], 10: [6, 28, 50]}


def gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF


def rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(len(result)):
            result[j] = gf_mul(result[j], root)
            if j + 1 < len(result):
                result[j] ^= result[j + 1]
        root = gf_mul(root, 0x02)
    return result


def rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= gf_mul(coef, factor)
    return result


def encode(text):
    data = text.encode('utf-8')
    for ver in range(1, 11):
        ecl, groups = EC_M[ver]
        capacity = sum(n * k for n, k in groups)
        count_bits = 8 if ver < 10 else 16
        if 4 + count_bits + 8 * len(data) <= capacity * 8:
            break
    else:
        raise ValueError('text too long for versions 1-10')
    bits = [0, 1, 0, 0] + [(len(data) >> i) & 1 for i in range(count_bits - 1, -1, -1)]
    for b in data:
        bits += [(b >> i) & 1 for i in range(7, -1, -1)]
    bits += [0] * min(4, capacity * 8 - len(bits))
    bits += [0] * (-len(bits) % 8)
    words = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    n = 0
    while len(words) < capacity:
        words.append((0xEC, 0x11)[n % 2])
        n += 1
    # split into blocks, add error correction, interleave
    div = rs_divisor(ecl)
    blocks, k = [], 0
    for n, size in groups:
        for _ in range(n):
            d = words[k:k + size]
            k += size
            blocks.append((d, rs_remainder(d, div)))
    out = []
    for i in range(max(len(d) for d, _ in blocks)):
        out += [d[i] for d, _ in blocks if i < len(d)]
    for i in range(ecl):
        out += [ec[i] for _, ec in blocks]
    return ver, out


def build(text):
    ver, codewords = encode(text)
    size = ver * 4 + 17
    mod = [[False] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]

    def setf(x, y, v):
        mod[y][x] = v
        fn[y][x] = True

    for i in range(size):  # timing
        setf(6, i, i % 2 == 0)
        setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):  # finders + separators
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    d = max(abs(dx), abs(dy))
                    setf(x, y, d not in (2, 4))
    al = ALIGN[ver]
    for i, a in enumerate(al):
        for j, b in enumerate(al):
            if (i == 0 and j == 0) or (i == 0 and j == len(al) - 1) or (i == len(al) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setf(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)
    # reserve format and version areas
    for i in range(9):
        fn[8][i] = fn[i][8] = True
    for i in range(8):
        fn[8][size - 1 - i] = fn[size - 1 - i][8] = True
    setf(8, size - 8, True)  # dark module
    if ver >= 7:
        rem = ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        vbits = ver << 12 | rem
        for i in range(18):
            bit = (vbits >> i) & 1 == 1
            a, b = size - 11 + i % 3, i // 3
            setf(a, b, bit)
            setf(b, a, bit)
    # place data in zigzag
    allbits = [(cw >> (7 - j)) & 1 for cw in codewords for j in range(8)]
    i = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                upward = ((right + 1) & 2) == 0
                y = size - 1 - vert if upward else vert
                if not fn[y][x] and i < len(allbits):
                    mod[y][x] = allbits[i] == 1
                    i += 1
        right -= 2

    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
             lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
             lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
             lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

    def draw_format(grid, mask):
        data = (0 << 3) | mask  # level M = 0b00
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = ((data << 10) | rem) ^ 0x5412
        g = lambda k: (bits >> k) & 1 == 1
        for k in range(6):
            grid[k][8] = g(k)
        grid[7][8] = g(6)
        grid[8][8] = g(7)
        grid[8][7] = g(8)
        for k in range(9, 15):
            grid[8][14 - k] = g(k)
        for k in range(8):
            grid[8][size - 1 - k] = g(k)
        for k in range(8, 15):
            grid[size - 15 + k][8] = g(k)
        grid[size - 8][8] = True

    def penalty(g):
        p = 0
        for rows in (g, [list(c) for c in zip(*g)]):
            for row in rows:
                run, prev = 0, None
                for v in row:
                    if v == prev:
                        run += 1
                    else:
                        if run >= 5:
                            p += run - 2
                        run, prev = 1, v
                if run >= 5:
                    p += run - 2
                s = ''.join('1' if v else '0' for v in row)
                p += 40 * (s.count('10111010000') + s.count('00001011101'))
        for y in range(size - 1):
            for x in range(size - 1):
                if g[y][x] == g[y][x + 1] == g[y + 1][x] == g[y + 1][x + 1]:
                    p += 3
        dark = sum(v for row in g for v in row)
        p += abs(dark * 20 - size * size * 10) // (size * size) * 10
        return p

    best = None
    for m, f in enumerate(masks):
        g = [[mod[y][x] ^ (not fn[y][x] and f(x, y)) for x in range(size)] for y in range(size)]
        draw_format(g, m)
        score = penalty(g)
        if best is None or score < best[0]:
            best = (score, g)
    return best[1]


def svg(grid, border=2):
    n = len(grid) + 2 * border
    path = ''.join(f'M{x + border},{y + border}h1v1h-1z' for y, row in enumerate(grid) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path d="{path}" fill="#000"/></svg>')


if __name__ == '__main__':
    open(sys.argv[2], 'w').write(svg(build(sys.argv[1])))
