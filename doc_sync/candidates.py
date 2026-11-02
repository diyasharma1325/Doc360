"""Stage 2: given a change note, return the shortlist of article IDs to
assess — checking tag_map.json first (a free, instant lookup for a
feature area that's already hand-seeded), and returning [] when there's
no confident match. pipeline.py treats [] as "no cached mapping" and
falls through to a live kb_search.py scan instead of failing — a feature
area no longer has to be manually seeded before the pipeline can run
against it (this used to raise LookupError here instead, which is
exactly what blocked a manual-entry run on 2026-10-29: the typed
feature_area didn't exactly match tag_map's one seeded key).

Fuzzy-matches the feature_area against existing tag_map keys when there's
no exact hit, so a minor typo or case difference doesn't silently miss a
mapping that's actually there. Deliberately conservative: only a
near-exact match (>=90% similar — a typo or case difference, not a
different-but-similar feature) is auto-used, and that substitution is
always printed so it's visible, not silent. Anything less confident is
treated as no mapping at all — rather than guessing which feature area
was meant — and falls back to a live search instead of blocking the run.
"""
import difflib

import tag_map

AUTO_CORRECT_THRESHOLD = 0.9
SUGGEST_THRESHOLD = 0.6


def find_candidates(change_note):
    feature_area = change_note.feature_area
    ids = tag_map.lookup(feature_area)
    if ids:
        return ids

    known = sorted(tag_map.load().keys())
    close = difflib.get_close_matches(feature_area, known, n=3, cutoff=SUGGEST_THRESHOLD)

    if close:
        best = close[0]
        ratio = difflib.SequenceMatcher(None, feature_area.lower(), best.lower()).ratio()
        if ratio >= AUTO_CORRECT_THRESHOLD:
            print(f"    (no exact tag_map match for feature_area={feature_area!r} — "
                  f"using close match {best!r}, {ratio:.0%} similar)")
            return tag_map.lookup(best)
        print(f"    (no tag_map entry for feature_area={feature_area!r} — closest is {best!r} "
              f"at {ratio:.0%}, not confident enough to use as a typo fix; falling back to a live KB search)")
        return []

    return []
