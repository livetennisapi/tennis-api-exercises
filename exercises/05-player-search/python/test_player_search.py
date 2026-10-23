"""Offline tests for exercise 5. They replay recorded responses from fixtures/."""

import importlib.util
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_exercise():
    if os.environ.get("SOLUTION") == "1":
        path = HERE.parent / "solutions" / "python" / "solution.py"
    else:
        path = HERE / "starter.py"
    spec = importlib.util.spec_from_file_location("ex05_player_search", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))["response"]


class FakeGet:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append((url, {name.lower(): value for name, value in headers.items()}))
        reply = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return ex.Response(reply["status"], dict(reply["headers"]), json.dumps(reply["body"]))


def players(name):
    return fixture(name)["body"]["data"]


def test_search_url_uses_search_parameter():
    url = ex.search_url("Jannik Sinner")
    assert url.startswith(ex.BASE_URL + "/players?")
    assert "search=Jannik%20Sinner" in url
    assert "name=" not in url
    assert "limit=10" in url


def test_search_players_returns_players_and_total():
    get = FakeGet(fixture("players_search_williams"))
    result = ex.search_players("williams", "abc123", get)
    assert len(result["players"]) == 10
    assert result["total"] == 64
    assert get.calls[0][1]["authorization"] == "Bearer abc123"


def test_blank_search_makes_no_request():
    get = FakeGet(fixture("players_search_none"))
    with pytest.raises(ValueError):
        ex.search_players("   ", "abc123", get)
    assert get.calls == []


def test_zero_results():
    with pytest.raises(ex.PlayerNotFound):
        ex.pick_player(players("players_search_none"), 0)


def test_one_result():
    assert ex.pick_player(players("players_search_one"), 1)["id"] == 34


def test_many_results_drop_doubles_teams():
    with pytest.raises(ex.AmbiguousPlayer) as error:
        ex.pick_player(players("players_search_sinner"), 10)
    assert error.value.candidates == ["Jannik Sinner", "Sinner"]


def test_many_results_including_teams():
    with pytest.raises(ex.AmbiguousPlayer) as error:
        ex.pick_player(players("players_search_sinner"), 10, singles_only=False)
    assert len(error.value.candidates) == 5
    assert error.value.candidates[0] == "Jannik Sinner"


def test_ambiguous_message_names_the_total():
    with pytest.raises(ex.AmbiguousPlayer) as error:
        ex.pick_player(players("players_search_williams"), 64)
    assert "64" in str(error.value)
    assert error.value.candidates[0] == "Venus Williams"


def test_get_player_detail():
    get = FakeGet(fixture("player_34"))
    player = ex.get_player(34, "abc123", get)
    assert player["name"] == "Jannik Sinner"
    assert get.calls[0][0] == ex.BASE_URL + "/players/34"
    assert get.calls[0][1].get("authorization") == "Bearer abc123"


def test_get_player_404():
    get = FakeGet(fixture("error_404_player"))
    with pytest.raises(ex.PlayerNotFound):
        ex.get_player(999999999, "abc123", get)


def test_describe_player():
    assert ex.describe_player(fixture("player_34")["body"]) == "Jannik Sinner (ITA), ATP rank 1, 10950 points"


def test_describe_unranked_player():
    player = {"name": "Sinner / Sonego", "country": None, "ranking": None, "tour": "atp"}
    assert ex.describe_player(player) == "Sinner / Sonego, unranked"


def test_describe_player_without_tour():
    player = {"name": "A Player", "country": "fra", "ranking": 250, "ranking_points": None, "tour": None}
    assert ex.describe_player(player) == "A Player (FRA), rank 250"


def test_find_player_end_to_end():
    get = FakeGet(fixture("players_search_one"), fixture("player_34"))
    player = ex.find_player("Jannik Sinner", "abc123", get)
    assert player["id"] == 34
    assert [url for url, _ in get.calls] == [ex.search_url("Jannik Sinner"), ex.BASE_URL + "/players/34"]
    assert [headers.get("authorization") for _, headers in get.calls] == ["Bearer abc123"] * 2


@pytest.mark.parametrize(
    "name, encoded",
    [("Gaël Monfils", "search=Ga%C3%ABl%20Monfils"), ("Tom & Jerry", "search=Tom%20%26%20Jerry")],
)
def test_search_url_encodes_everything(name, encoded):
    assert encoded in ex.search_url(name)


def test_find_player_never_guesses():
    get = FakeGet(fixture("players_search_sinner"))
    with pytest.raises(ex.AmbiguousPlayer):
        ex.find_player("sinner", "abc123", get)
    assert len(get.calls) == 1


def test_search_players_rejects_a_bad_status():
    get = FakeGet(fixture("error_401_bad_key"))
    with pytest.raises(RuntimeError) as error:
        ex.search_players("sinner", "bad", get)
    assert not isinstance(error.value, NotImplementedError)
    assert "401" in str(error.value)


def test_get_player_401_is_not_a_missing_player():
    get = FakeGet(fixture("error_401_bad_key"))
    with pytest.raises(RuntimeError) as error:
        ex.get_player(34, "bad", get)
    assert not isinstance(error.value, NotImplementedError)
    assert "401" in str(error.value)


def one_singles_nine_teams():
    rows = players("players_search_sinner")
    teams = [p for p in rows if p["is_doubles_team"]]
    return [rows[0]] + teams + [dict(teams[0], id=99999, name="Extra / Sinner")]


def test_incomplete_page_is_not_a_single_match():
    rows = one_singles_nine_teams()
    assert len(rows) == 10
    with pytest.raises(ex.AmbiguousPlayer) as error:
        ex.pick_player(rows, 11)
    assert "11" in str(error.value)


def test_incomplete_page_of_teams_is_not_not_found():
    teams = [p for p in one_singles_nine_teams() if p["is_doubles_team"]]
    with pytest.raises(ex.AmbiguousPlayer):
        ex.pick_player(teams, 20)


def test_complete_page_of_teams_is_not_found():
    teams = [p for p in one_singles_nine_teams() if p["is_doubles_team"]]
    with pytest.raises(ex.PlayerNotFound):
        ex.pick_player(teams, len(teams))


def test_a_retained_rank_is_not_current():
    cooper = next(p for p in players("players_search_williams") if p["name"] == "Cooper Williams")
    assert cooper["ranking_status"] == "unranked" and cooper["ranking"] == 604
    assert ex.describe_player(cooper) == "Cooper Williams (USA), unranked"
