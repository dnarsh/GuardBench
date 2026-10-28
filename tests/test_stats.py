import pytest

from guardbench.scoring import h1_verdict, newcombe_diff, wilson


def test_newcombe_matches_the_published_worked_example():
    # Newcombe (1998), Statistics in Medicine 17:873, table II row 1: 56/70 vs 48/80,
    # method 10 (hybrid score): difference 0.2000, interval 0.0524 to 0.3339.
    d, lo, hi = newcombe_diff(56, 70, 48, 80)
    assert round(d, 4) == 0.2
    assert round(lo, 4) == 0.0524
    assert round(hi, 4) == 0.3339


def test_newcombe_matches_a_hand_computed_value():
    # 15/20 vs 5/20: Wilson(15/20) = [0.5313, 0.8881]; Wilson(5/20) = [0.1119, 0.4687]
    # d = 0.5; L = 0.5 - sqrt((0.75-0.5313)^2 + (0.4687-0.25)^2) = 0.5 - 0.3093 = 0.1907
    # U = 0.5 + sqrt((0.8881-0.75)^2 + (0.25-0.1119)^2) = 0.5 + 0.1953 = 0.6953
    d, lo, hi = newcombe_diff(15, 20, 5, 20)
    assert d == pytest.approx(0.5)
    assert lo == pytest.approx(0.1907, abs=5e-4)
    assert hi == pytest.approx(0.6953, abs=5e-4)


def test_newcombe_is_antisymmetric_and_centred_for_equal_groups():
    d, lo, hi = newcombe_diff(9, 30, 9, 30)
    assert d == 0 and lo == pytest.approx(-hi)
    a, b = newcombe_diff(20, 60, 10, 40), newcombe_diff(10, 40, 20, 60)
    assert a[0] == pytest.approx(-b[0]) and a[1] == pytest.approx(-b[2]) and a[2] == pytest.approx(-b[1])


def test_newcombe_stays_inside_minus_one_and_one_at_the_extremes():
    d, lo, hi = newcombe_diff(30, 30, 0, 30)
    assert d == 1 and -1 <= lo < 1 and hi == pytest.approx(1)


def test_newcombe_rejects_empty_groups():
    with pytest.raises(ValueError):
        newcombe_diff(0, 0, 1, 2)


def test_h1_verdict_follows_the_preregistered_rule():
    # upper bound < 0.75 supports; lower bound >= 0.75 refutes; otherwise inconclusive
    assert h1_verdict(30, 100) == "supported"
    assert h1_verdict(95, 100) == "refuted"
    assert h1_verdict(7, 10) == "inconclusive"
    assert wilson(60, 100)[1] < 0.75 and h1_verdict(60, 100) == "supported"
    assert h1_verdict(0, 0) == "inconclusive"
