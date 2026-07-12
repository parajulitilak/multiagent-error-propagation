"""Controlled fault injection.

We corrupt ONE intermediate output with a known, scripted perturbation, then
let the rest of the pipeline run untouched. Because the fault is planted by
us, ground truth about where the failure started is known; this is what
turns 'agents sometimes fail' into a causal measurement.

Each injector returns (corrupted_text, meta) where meta records exactly what
changed, so every downstream error can be attributed.
"""
from __future__ import annotations

import random
import re

# Word-level arithmetic flips: applied to plans/solutions in math tasks.
_OP_FLIPS = {
    "add": "subtract", "subtract": "add",
    "plus": "minus", "minus": "plus",
    "multiply": "divide", "divide": "multiply",
    "more": "fewer", "fewer": "more",
    "increase": "decrease", "decrease": "increase",
    "sum": "difference", "difference": "sum",
    "total": "difference",
}

# Quantities: plain integers/decimals plus comma-grouped forms like 1,234.
# The trailing guard rejects word characters and decimal continuations but
# allows a sentence-final period ('the total is 6.').
_NUM_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?!\w)(?!\.\d)")


def _is_label(text: str, m: re.Match) -> bool:
    """True for list/step labels: 'Step 1:', 'Part 3)', or a line-start '2.'.

    Only labels are excluded; a real quantity that happens to end a sentence
    ('the total is 6.') stays eligible.
    """
    before = text[: m.start()]
    if re.search(r"(?:step|part|stage|question|q)\s*$", before, flags=re.IGNORECASE):
        return True
    nxt = text[m.end(): m.end() + 1]
    line_prefix = before.rsplit("\n", 1)[-1]
    return bool(re.fullmatch(r"\s*", line_prefix)) and bool(re.match(r"[.):]", nxt or ""))


def number_swap(text: str, rng: random.Random):
    """Replace one quantity with a plausible wrong value.

    Values above 5 are scaled by one of 0.4 / 0.6 / 1.4 / 1.7; values of 5 or
    below get +1..3 (scaling them would too often round back to the original).
    Comma-grouped quantities ('$1,234') are treated as one number and the
    grouping is preserved in the corrupted text. List/step labels are
    excluded: corrupting them changes no quantity, which would dilute the
    injection with harmless perturbations and bias propagation rates downward.
    """
    nums = [m for m in _NUM_RE.finditer(text) if not _is_label(text, m)]
    if not nums:
        return text, {"type": "number_swap", "applied": False}
    m = rng.choice(nums)
    raw = m.group(1)
    old = float(raw.replace(",", ""))
    if old <= 5:
        new = old + rng.choice([1, 2, 3])
    else:
        factor = rng.choice([0.4, 0.6, 1.4, 1.7])
        new = round(old * factor)
        if new == old:
            new = old + 1
    new_str = str(int(new)) if float(new).is_integer() else str(new)
    if "," in raw and float(new).is_integer():
        new_str = f"{int(new):,}"
    corrupted = text[: m.start(1)] + new_str + text[m.end(1):]
    meta = {
        "type": "number_swap", "applied": True,
        "old": raw.replace(",", ""), "new": new_str.replace(",", ""),
        "pos": m.start(1),
    }
    return corrupted, meta


def operation_flip(text: str, rng: random.Random):
    """Flip one arithmetic operation word to its opposite."""
    candidates = []
    for word, repl in _OP_FLIPS.items():
        for m in re.finditer(rf"\b{word}\b", text, flags=re.IGNORECASE):
            candidates.append((m, repl))
    if not candidates:
        return text, {"type": "operation_flip", "applied": False}
    m, repl = rng.choice(candidates)
    corrupted = text[: m.start()] + repl + text[m.end():]
    meta = {
        "type": "operation_flip", "applied": True,
        "old": m.group(0), "new": repl, "pos": m.start(),
    }
    return corrupted, meta


INJECTORS = {"number_swap": number_swap, "operation_flip": operation_flip}


def make_injector(types: list[str], seed: int):
    """Return injector fn cycling over requested types; falls back if one
    perturbation type finds nothing to corrupt in a given text."""
    base_rng = random.Random(seed)

    def injector(text: str, rng: random.Random | None = None):
        r = rng or base_rng
        order = types[:]
        r.shuffle(order)
        for t in order:
            corrupted, meta = INJECTORS[t](text, r)
            if meta.get("applied"):
                return corrupted, meta
        return text, {"type": "none_applicable", "applied": False}

    return injector
