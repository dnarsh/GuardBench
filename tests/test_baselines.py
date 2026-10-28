import pytest

from guardbench.baselines import make_random, random_hit_probability
from guardbench.patch import new_side_lines

from test_validate import BUG


def test_random_hit_probability_is_hit_lines_over_shown_lines():
    shown = new_side_lines(BUG)
    n_hit = sum(1 for f, ln in shown if f == "mod.py" and 3 - 3 <= ln <= 3 + 3)
    assert random_hit_probability(BUG, "mod.py", 3, 3) == pytest.approx(n_hit / len(shown))
    assert random_hit_probability(BUG, "other.py", 3, 3) == 0.0
    assert random_hit_probability("", "mod.py", 3, 3) == 0.0


def test_random_baseline_frequency_matches_the_probability():
    p = random_hit_probability(BUG, "mod.py", 3, 3)
    from guardbench.matcher import is_hit
    hits = sum(is_hit(make_random(s)(BUG)[0], "mod.py", 3, 3) for s in range(400))
    assert abs(hits / 400 - p) < 0.1
