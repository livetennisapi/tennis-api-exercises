"""Offline tests for exercise 4, run against fixtures/matches_live.json."""

import copy
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_exercise():
    if os.environ.get("SOLUTION") == "1":
        path = HERE.parent / "solutions" / "python" / "solution.py"
    else:
        path = HERE / "starter.py"
    spec = importlib.util.spec_from_file_location("ex04_filter_and_group", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()
LIVE = json.loads((ROOT / "fixtures" / "matches_live.json").read_text(encoding="utf-8"))["response"]["body"]["data"]


def ids(matches):
    return [match["id"] for match in matches]


def test_filter_draw_counts():
    assert len(ex.filter_draw(LIVE, "singles")) == 19
    assert len(ex.filter_draw(LIVE, "doubles")) == 6


def test_null_draw_is_neither():
    singles = ex.filter_draw(LIVE, "singles")
    doubles = ex.filter_draw(LIVE, "doubles")
    unknown = [match for match in LIVE if match["draw"] is None]
    assert len(singles) + len(doubles) + len(unknown) == len(LIVE)
    assert not set(ids(unknown)) & set(ids(singles) + ids(doubles))


def test_group_keys_in_tour_order():
    groups = ex.group_by_tour(LIVE)
    assert list(groups) == ["atp", "challenger", "itf", "other"]


def test_group_sizes_add_up():
    groups = ex.group_by_tour(LIVE)
    assert {tour: len(group) for tour, group in groups.items()} == {"atp": 2, "challenger": 2, "itf": 21, "other": 4}


def test_groups_sorted_by_tournament_then_id():
    groups = ex.group_by_tour(LIVE)
    assert ids(groups["atp"]) == [208138, 207981]          # Brussels before Lyon
    assert ids(groups["challenger"]) == [208113, 207819]   # Florence before Lisbon
    assert ids(groups["other"]) == [209439, 209440, 209429, 209431]


def test_group_skips_non_live_and_does_not_mutate():
    slate = copy.deepcopy(LIVE)
    slate[0]["status"] = "completed"
    before = copy.deepcopy(slate)
    groups = ex.group_by_tour(slate)
    assert slate[0]["id"] not in [m["id"] for group in groups.values() for m in group]
    assert slate == before


def test_unknown_tour_goes_to_other():
    match = {"id": 1, "status": "live", "tour": "exhibition", "tournament": "Show"}
    assert list(ex.group_by_tour([match])) == ["other"]


def test_count_by_tournament():
    counts = ex.count_by_tournament(LIVE)
    assert counts[:2] == [("M15 Bol 2", 4), ("W15 Bol 2", 3)]
    assert [count for _, count in counts].count(2) == 4
    assert sum(count for _, count in counts) == len(LIVE)
    assert len(counts) == len({match["tournament"] for match in LIVE})


def test_count_ties_are_alphabetical():
    counts = ex.count_by_tournament(LIVE)
    keys = [(-count, name.casefold()) for name, count in counts]
    assert keys == sorted(keys)
    assert ("W35 Loule", 2) in counts


def test_empty_slate():
    assert ex.group_by_tour([]) == {}
    assert ex.count_by_tournament([]) == []


def test_itf_group_order():
    assert ids(ex.group_by_tour(LIVE)["itf"]) == [
        209438, 209420, 209382, 209377, 209393, 209394, 209414, 208275, 208222, 208208, 208242,
        208245, 209381, 209391, 209413, 208278, 208279, 208268, 208191, 208211, 208219,
    ]


def test_two_key_sort_ignores_case():
    # Built by hand: ids out of order inside one tournament, names in mixed case.
    slate = [
        {"id": 5, "status": "live", "tour": "atp", "tournament": "b open"},
        {"id": 1, "status": "live", "tour": "atp", "tournament": "Zed Cup"},
        {"id": 3, "status": "live", "tour": "atp", "tournament": "B Open"},
        {"id": 9, "status": "live", "tour": "atp", "tournament": "a cup"},
    ]
    assert ids(ex.group_by_tour(slate)["atp"]) == [9, 3, 5, 1]
    assert ex.count_by_tournament([
        {"id": 1, "tournament": "beta"}, {"id": 2, "tournament": "Alpha"}, {"id": 3, "tournament": "Gamma"},
    ]) == [("Alpha", 1), ("beta", 1), ("Gamma", 1)]


def test_no_function_changes_its_input():
    slate = list(reversed(copy.deepcopy(LIVE)))  # unsorted on purpose
    before = copy.deepcopy(slate)
    ex.count_by_tournament(slate)
    ex.filter_draw(slate, "singles")
    ex.group_by_tour(slate)
    assert slate == before


def test_every_tour_in_order():
    # Built by hand and shuffled: one or two live matches on every supported tour, plus one with no tour.
    slate = [
        {"id": 7, "status": "live", "tour": "juniors", "tournament": "Junior Open"},
        {"id": 2, "status": "live", "tour": "wta", "tournament": "Wuhan"},
        {"id": 5, "status": "live", "tour": None, "tournament": "Exhibition"},
        {"id": 4, "status": "live", "tour": "itf", "tournament": "M15 Bol 2"},
        {"id": 1, "status": "live", "tour": "atp", "tournament": "Basel"},
        {"id": 6, "status": "live", "tour": "wta", "tournament": "Beijing"},
        {"id": 3, "status": "live", "tour": "challenger", "tournament": "Lisbon"},
    ]
    groups = ex.group_by_tour(slate)
    assert list(groups) == ["atp", "wta", "challenger", "itf", "juniors", "other"]
    assert {tour: ids(group) for tour, group in groups.items()} == {
        "atp": [1], "wta": [6, 2], "challenger": [3], "itf": [4], "juniors": [7], "other": [5],
    }
