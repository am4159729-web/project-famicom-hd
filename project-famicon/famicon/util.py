import math


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def sign(v):
    return (v > 0) - (v < 0)


def overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def wrap_text(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    return lines + ([cur] if cur else [])
