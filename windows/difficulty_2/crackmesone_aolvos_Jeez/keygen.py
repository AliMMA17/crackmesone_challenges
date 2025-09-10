def _u8(x): return x & 0xFF
def _hex2(x): return f"{x & 0xFF:02X}"

def _to_letter(v, step_up):
    v &= 0xFF
    # step by ±4 until in 'A'..'Z'
    while not (0x41 <= v <= 0x5A):
        v = (v + 4) & 0xFF if step_up else (v - 4) & 0xFF
    return chr(v)

def _signed_byte(b):  # match movsx for name summation
    b &= 0xFF
    return b if b < 0x80 else b - 0x100

def make_serial(name: str) -> str:
    if len(name) <= 3:
        raise ValueError("name must be longer than 3 characters")

    L = len(name)
    nb = [ord(c) & 0xFF for c in name]

    # S = sum of first (L-3) bytes as signed
    S = sum(_signed_byte(nb[i]) for i in range(L - 3))
    S = _u8(S)

    # last three name bytes
    A = nb[L - 3]
    B = nb[L - 2]
    C = nb[L - 1]

    # choose b0, b1 deterministically from the name (any bytes work if consistent)
    b0 = _u8(S ^ A)
    b1 = _u8(B ^ C)

    # group 1 (offset +7): two bytes as hex pairs
    g1a = _u8(S * b0 - (b1 >> 4))
    g1b = _u8(A * b1 - (b0 >> 4))

    # group 2 (offset +12)
    g2a = _u8(b0 * B + (b0 >> 4))
    g2b = _u8(b1 * C + (b1 >> 4))

    # group 3 (offset +17) is just b0 || b1
    g3a, g3b = b0, b1

    # first 4 letters (401D79..)
    # positions 0,1 use b0; positions 2,3 use b1
    letters = [
        _to_letter(_u8(S * b0), True),
        _to_letter(_u8(A * b0), False),
        _to_letter(_u8(B * b1), True),
        _to_letter(_u8(C * b1), False),
    ]

    # last 2 hex of the 6-char header (401D34..401D50): ~(b0+b1)
    header_tail = _u8(~_u8(b0 + b1))

    header = "".join(letters) + _hex2(header_tail)

    serial = (
        f"{header}"
        f"-{_hex2(g1a)}{_hex2(g1b)}"
        f"-{_hex2(g2a)}{_hex2(g2b)}"
        f"-{_hex2(g3a)}{_hex2(g3b)}"
    )
    return serial

# --- Optional: simulate the program's checks to verify a serial ---
def verify(name: str, serial: str) -> bool:
    # expect format LLLLHH-XXXX-XXXX-XXXX (length > 20)
    try:
        h, g1, g2, g3 = serial.split("-")
    except ValueError:
        return False
    if len(h) != 6 or len(g1) != 4 or len(g2) != 4 or len(g3) != 4:
        return False

    # parse b0,b1 from last block (what the program does)
    b0 = int(g3[:2], 16)
    b1 = int(g3[2:], 16)

    L = len(name)
    if L <= 3:
        return False
    nb = [ord(c) & 0xFF for c in name]
    S = sum(_signed_byte(nb[i]) for i in range(L - 3)) & 0xFF
    A, B, C = nb[L - 3], nb[L - 2], nb[L - 1]

    # recompute header letters
    letters = [
        _to_letter((S * b0) & 0xFF, True),
        _to_letter((A * b0) & 0xFF, False),
        _to_letter((B * b1) & 0xFF, True),
        _to_letter((C * b1) & 0xFF, False),
    ]
    if "".join(letters) != h[:4]:
        return False

    if f"{(~((b0 + b1) & 0xFF)) & 0xFF:02X}" != h[4:6]:
        return False

    exp_g1 = f"{(S * b0 - (b1 >> 4)) & 0xFF:02X}{(A * b1 - (b0 >> 4)) & 0xFF:02X}"
    exp_g2 = f"{(b0 * B + (b0 >> 4)) & 0xFF:02X}{(b1 * C + (b1 >> 4)) & 0xFF:02X}"

    return (g1.upper() == exp_g1 and
            g2.upper() == exp_g2)

# quick demo (your example name)
if __name__ == "__main__":
    user = "alim"
    s = make_serial(user)
    print(user, "→", s)
    print("passes check:", verify(user, s))
