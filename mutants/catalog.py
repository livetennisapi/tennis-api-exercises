"""Wrong solutions that the tests must reject.

Each mutant is a small, plausible mistake applied to a reference solution:
a list of (find, replace) edits. `find` must occur exactly once, so a
mutant fails loudly if the solution changes under it. Most mistakes come
from the review of this repository and from "Common mistakes" in
TEACHERS.md.
"""

PY = "solutions/python/solution.py"
JS = "solutions/js/solution.mjs"


def m(exercise, lang, name, *edits):
    return {"exercise": exercise, "file": PY if lang == "py" else JS, "lang": lang, "name": name, "edits": list(edits)}


E1, E2, E3, E4 = "01-first-request", "02-read-a-score", "03-break-points", "04-filter-and-group"
E5, E6, E7, E8 = "05-player-search", "06-rate-limits-and-quota", "07-errors", "08-terminal-scoreboard"

MUTANTS = [
    # 01 first request
    m(E1, "py", "os.environ[...] raises KeyError", ('key = (env.get("LIVETENNISAPI_KEY") or "").strip()', 'key = env["LIVETENNISAPI_KEY"].strip()')),
    m(E1, "js", "no default for a missing variable", ("(env.LIVETENNISAPI_KEY ?? '').trim()", "env.LIVETENNISAPI_KEY.trim()")),
    m(E1, "py", "drops limit=200", ('get(f"{BASE_URL}/matches?status=live&limit=200"', 'get(f"{BASE_URL}/matches?status=live"')),
    m(E1, "js", "drops limit=200", ("`${BASE_URL}/matches?status=live&limit=200`", "`${BASE_URL}/matches?status=live`")),
    m(E1, "py", "counts the page, not meta.total", ("if isinstance(total, int):\n        return total", "if False:\n        return total")),
    m(E1, "js", "counts the page, not meta.total", ("if (Number.isInteger(total)) return total;", "")),
    m(E1, "py", "key in the URL", ('get(f"{BASE_URL}/matches?status=live&limit=200", auth_headers(key))', 'get(f"{BASE_URL}/matches?status=live&limit=200&token={key}", {"Accept": "application/json"})')),
    m(E1, "js", "key in the URL", ("fetchImpl(`${BASE_URL}/matches?status=live&limit=200`, {\n    headers: authHeaders(key),", "fetchImpl(`${BASE_URL}/matches?status=live&limit=200&token=${key}`, {\n    headers: {},")),
    # 02 read a score
    m(E2, "py", "winner from the last set", ("winner = 1 if sets[0] > sets[1] else 2", "winner = 1 if games[0][-1] > games[1][-1] else 2")),
    m(E2, "js", "winner from the last set", ("winner = sets[0] > sets[1] ? 1 : 2;", "winner = score.games[0].at(-1) > score.games[1].at(-1) ? 1 : 2;")),
    m(E2, "py", "three sets means match tiebreak", ("return (games[0][-1], games[1][-1]) != (6, 6)", "return len(games[0]) >= 3")),
    m(E2, "js", "three sets means match tiebreak", ("return !(games[0].at(-1) === 6 && games[1].at(-1) === 6);", "return games[0].length >= 3;")),
    m(E2, "py", "level score means ordinary tiebreak", ("return (games[0][-1], games[1][-1]) != (6, 6)", "return games[0][-1] != games[1][-1]")),
    m(E2, "js", "level score means ordinary tiebreak", ("return !(games[0].at(-1) === 6 && games[1].at(-1) === 6);", "return games[0].at(-1) !== games[1].at(-1);")),
    m(E2, "py", "games read as one list per set", ('parts = [f"{a}-{b}" for a, b in zip(first, second)]', 'parts = [f"{s[0]}-{s[1]}" for s in games]')),
    # 03 break points
    m(E3, "py", "deuce counts as a break point", ("if receiver_points == 3 and server_points <= 2:\n        return 3 - server_points", "if receiver_points == 3 and server_points <= 3:\n        return max(3 - server_points, 1)")),
    m(E3, "js", "deuce counts as a break point", ("if (receiverPoints === 3 && serverPoints <= 2) return 3 - serverPoints;", "if (receiverPoints === 3 && serverPoints <= 3) return Math.max(3 - serverPoints, 1);")),
    m(E3, "py", "server and receiver swapped", ("server_points = point_value(points[server - 1])\n    receiver_points = point_value(points[2 - server])", "server_points = point_value(points[2 - server])\n    receiver_points = point_value(points[server - 1])")),
    m(E3, "py", "tiebreak not skipped", ('if not score or score.get("is_tiebreak"):', "if not score:")),
    m(E3, "js", "numbers accepted as points", ("typeof text !== 'string' || ", "")),
    # 04 filter and group
    m(E4, "py", "no id tie-break", ('return ((match.get("tournament") or "").casefold(), match.get("id") or 0)', 'return ((match.get("tournament") or "").casefold(), 0)')),
    m(E4, "py", "case-sensitive group sort", ('return ((match.get("tournament") or "").casefold(), match.get("id") or 0)', 'return ((match.get("tournament") or ""), match.get("id") or 0)')),
    m(E4, "js", "case-sensitive group sort", ("const nameA = (a.tournament ?? '').toLowerCase();\n  const nameB = (b.tournament ?? '').toLowerCase();\n  if (nameA !== nameB)", "const nameA = a.tournament ?? '';\n  const nameB = b.tournament ?? '';\n  if (nameA !== nameB)")),
    m(E4, "js", "no id tie-break", ("return (a.id ?? 0) - (b.id ?? 0);", "return 0;")),
    m(E4, "py", "unknown draw counted as singles", ('return [match for match in matches if match.get("draw") == draw]', 'return [match for match in matches if (match.get("draw") or "singles") == draw]')),
    m(E4, "py", "case-sensitive count tie-break", ("key=lambda item: (-item[1], item[0].casefold())", "key=lambda item: (-item[1], item[0])")),
    # 05 player search
    m(E5, "py", "takes the first of many", ('chosen = pick_player(result["players"], result["total"])', 'chosen = next(p for p in result["players"] if not p.get("is_doubles_team"))')),
    m(E5, "js", "takes the first of many", ("const chosen = pickPlayer(players, total);", "const chosen = players.find((p) => !p.is_doubles_team);")),
    m(E5, "py", "an exact name wins", ('chosen = pick_player(result["players"], result["total"])', 'chosen = next((p for p in result["players"] if p["name"].lower() == name.strip().lower()), None) or pick_player(result["players"], result["total"])')),
    m(E5, "py", "replace(' ', '%20') instead of encoding", ("urllib.parse.quote(name)", 'name.replace(" ", "%20")')),
    m(E5, "js", "replaceAll(' ', '%20') instead of encoding", ("encodeURIComponent(name)", "name.replaceAll(' ', '%20')")),
    m(E5, "py", "uses ?name=", ("/players?search=", "/players?name=")),
    m(E5, "py", "search ignores the status", ('    if response.status != 200:\n        raise RuntimeError(f"GET /players answered HTTP {response.status}")\n', "")),
    m(E5, "js", "search ignores the status", ("  if (response.status !== 200) throw new Error(`GET /players answered HTTP ${response.status}`);\n", "")),
    m(E5, "py", "every error is a missing player", ("if response.status == 404:", "if response.status != 200:")),
    m(E5, "js", "every error is a missing player", ("if (response.status === 404)", "if (response.status !== 200)")),
    # 06 rate limits and quota
    m(E6, "py", "fixed-window limiter lets a burst through",
      ("while self.calls and self.calls[0] <= now - self.period:\n            self.calls.popleft()", "if self.calls and now // self.period != self.calls[-1] // self.period:\n            self.calls.clear()"),
      ("pause = self.calls[0] + self.period - now", "pause = (now // self.period + 1) * self.period - now")),
    m(E6, "js", "fixed-window limiter lets a burst through",
      ("while (this.calls.length && this.calls[0] <= now - this.period) this.calls.shift();", "if (this.calls.length && Math.floor(now / this.period) !== Math.floor(this.calls.at(-1) / this.period)) this.calls.length = 0;"),
      ("const pause = this.calls[0] + this.period - now;", "const pause = (Math.floor(now / this.period) + 1) * this.period - now;")),
    m(E6, "py", "no re-check after sleeping", ("while len(self.calls) >= self.max_calls:", "if len(self.calls) >= self.max_calls:")),
    m(E6, "js", "no re-check after sleeping", ("while (this.calls.length >= this.maxCalls) {", "if (this.calls.length >= this.maxCalls) {")),
    m(E6, "py", "abuse block retried", ('if body.get("error") == "abuse_throttled":', "if False:")),
    m(E6, "js", "abuse block retried", ("if (body.error === 'abuse_throttled') {", "if (false) {")),
    m(E6, "py", "daily quota guessed from Retry-After", ('if body.get("scope") == "day":', 'if float(response.headers.get("retry-after", 0)) > 3600:')),
    m(E6, "py", "get_with_retry ignores its cap", ('sleep(retry_delay(attempt, response.headers.get("retry-after"), cap=cap))', 'sleep(retry_delay(attempt, response.headers.get("retry-after")))')),
    m(E6, "js", "getWithRetry ignores its cap", ("retryDelay(attempt, response.headers.get('retry-after'), 1, cap)", "retryDelay(attempt, response.headers.get('retry-after'))")),
    m(E6, "py", "usage ignores the status", ('    if response.status != 200:\n        raise RuntimeError(f"GET /usage answered HTTP {response.status}")\n', "")),
    m(E6, "js", "Retry-After read with Number()", ("SECONDS.test(String(retryAfter))", "Number.isFinite(Number(retryAfter)) && Number(retryAfter) >= 0")),
    m(E6, "js", "headroom read with parseInt", ("return /^[0-9]+$/.test(value) ? Number(value) : null;", "return Number.isNaN(Number.parseInt(value, 10)) ? null : Number.parseInt(value, 10);")),
    # 07 errors
    m(E7, "py", "key leaks into every error", ("explain_error(response.status, body, path))", 'explain_error(response.status, body, path) + f" (sent key {key})")')),
    m(E7, "py", "key leaks into 401 errors", ("explain_error(response.status, body, path))", 'explain_error(response.status, body, path) + (f" key: {key}" if response.status == 401 else ""))')),
    m(E7, "js", "key leaks into every error", ("explainError(response.status, body, path));", "explainError(response.status, body, path) + ` (sent key ${key})`);")),
    m(E7, "py", "abuse block told to wait a minute", ('if code == "abuse_throttled":', "if False:")),
    m(E7, "js", "abuse block told to wait a minute", ("if (code === 'abuse_throttled') {", "if (false) {")),
    m(E7, "py", "crashes on a body that is not JSON", ("    try:\n        body = response.json()\n    except ValueError:\n        body = {}\n", "    body = response.json()\n")),
    m(E7, "js", "crashes on a body that is not JSON", ("  let body = {};\n  try {\n    body = await response.json();\n  } catch {\n    body = {};\n  }\n  if (response.status === 200) return body;", "  const body = await response.json();\n  if (response.status === 200) return body;")),
    # 08 terminal scoreboard
    m(E8, "py", "sleeps before checking the end", ("        if clock() - start + wait >= session_seconds:\n            break\n        sleep(wait)", "        sleep(wait)\n        if clock() - start >= session_seconds:\n            break")),
    m(E8, "js", "sleeps before checking the end", ("    if (clock() - start + wait >= sessionSeconds) break;\n    await sleep(wait);", "    await sleep(wait);\n    if (clock() - start >= sessionSeconds) break;")),
    m(E8, "py", "Retry-After alone", ('wait = max(interval, float(response.headers.get("retry-after", interval)))', 'wait = float(response.headers.get("retry-after", interval))')),
    m(E8, "js", "Retry-After alone", ("? Math.max(interval, retryAfter) : interval", "? retryAfter : interval")),
    m(E8, "py", "no request cap", ("while calls < usable:", "while True:")),
    m(E8, "js", "no request cap", ("while (calls < usable) {", "while (true) {")),
    m(E8, "py", "> instead of >=", ("if clock() - start + wait >= session_seconds:", "if clock() - start + wait > session_seconds:")),
    m(E8, "js", "> instead of >=", ("if (clock() - start + wait >= sessionSeconds) break;", "if (clock() - start + wait > sessionSeconds) break;")),
    m(E8, "py", "403 treated as a soft error", ("elif response.status in (401, 403):", "elif response.status == 401:")),
    m(E8, "js", "403 treated as a soft error", ("response.status === 401 || response.status === 403", "response.status === 401")),
    m(E8, "py", "stops on a server error", ('            out(f"HTTP {response.status}. Trying again at the next poll.")\n', '            out(f"HTTP {response.status}. Trying again at the next poll.")\n            break\n')),
    m(E8, "js", "stops on a server error", ("      out(`HTTP ${response.status}. Trying again at the next poll.`);\n", "      out(`HTTP ${response.status}. Trying again at the next poll.`);\n      break;\n")),
    m(E8, "py", "counts matches that are not live", ('live = [m for m in matches if m.get("status") == "live"]', "live = list(matches)")),
    m(E8, "js", "counts matches that are not live", ("const live = matches.filter((m) => m.status === 'live');", "const live = matches;")),
    m(E8, "py", "working leaves out the reserve", ('f"Daily budget {daily_budget} - reserve {reserve} = {usable} requests for polling. "', 'f"Daily budget {daily_budget} gives {usable} requests for polling. "')),
    m(E8, "py", "working leaves out the requests used", ('f"Check: {seconds} s / {interval} s = {needed} requests, which is at most {usable}."', '""')),
    m(E8, "js", "working leaves out the reserve", ("`Daily budget ${dailyBudget} - reserve ${reserve} = ${usable} requests for polling. `", "`Daily budget ${dailyBudget} gives ${usable} requests for polling. `")),
    m(E8, "py", "abuse block keeps polling", ('if body.get("error") == "abuse_throttled":', "if False:")),
    m(E8, "js", "abuse block keeps polling", ("if (body.error === 'abuse_throttled') {", "if (false) {")),
    m(E8, "py", "level match tiebreak shown as ordinary", ("(games[0][-1], games[1][-1]) != (6, 6)", "games[0][-1] != games[1][-1]")),
    m(E8, "js", "level match tiebreak shown as ordinary", ("!(games[0].at(-1) === 6 && games[1].at(-1) === 6)", "games[0].at(-1) !== games[1].at(-1)")),
]

# Added after the final review (one per finding)
MUTANTS += [
    m(E2, "py", "an unresolved match is announced as a win", ('        if match.get("outcome") in NO_RESULT:\n            return f"{sets_text}, no result"\n', "")),
    m(E2, "js", "an unresolved match is announced as a win", ("    if (NO_RESULT.includes(match.outcome)) return `${setsText}, no result`;\n", "")),
    m(E2, "py", "the winner field is ignored", ('winner = match.get("winner")', "winner = None")),
    m(E2, "js", "the winner field is ignored", ("let winner = match.winner;", "let winner = null;")),
    m(E2, "py", "brackets before pairing", ('parts[-1] = f"[{parts[-1]}]"', 'parts[-1] = f"[{first[-1]}-{second[-1]}]"')),
    m(E2, "js", "brackets before pairing", ("parts[parts.length - 1] = `[${parts.at(-1)}]`;", "parts[parts.length - 1] = `[${first.at(-1)}-${second.at(-1)}]`;")),
    m(E2, "py", "no guard for missing points", ("if not points or len(points) != 2:\n        return None", "if False:\n        return None")),
    m(E2, "js", "no guard for missing points", ("  if (!Array.isArray(points) || points.length !== 2) return null;\n", "")),
    m(E5, "py", "decides from an incomplete page", ("if total is not None and total > len(players):", "if False:")),
    m(E5, "js", "decides from an incomplete page", ("if (total !== null && total > players.length) {", "if (false) {")),
    m(E5, "py", "a retained rank shown as current", ('if ranking is None or player.get("ranking_status") == "unranked":', "if ranking is None:")),
    m(E5, "js", "a retained rank shown as current", ("if (player.ranking == null || player.ranking_status === 'unranked')", "if (player.ranking == null)")),
    m(E8, "py", "polls after a late wake-up", ("        if calls and clock() - start >= session_seconds:\n            break  # a sleep can wake late, so check the clock before every request\n", "")),
    m(E8, "js", "polls after a late wake-up", ("    if (calls && clock() - start >= sessionSeconds) break; // a sleep can wake late, so check before every request\n", "")),
    m(E8, "py", "ignores the caller's budget and reserve", ("    interval = poll_interval_seconds(session_minutes, daily_budget, reserve)\n    usable = daily_budget - reserve", "    interval = poll_interval_seconds(session_minutes)\n    usable = 90")),
    m(E8, "js", "ignores the caller's budget and reserve", ("  const interval = pollIntervalSeconds(sessionMinutes, { dailyBudget, reserve });\n  const usable = dailyBudget - reserve;", "  const interval = pollIntervalSeconds(sessionMinutes);\n  const usable = 90;")),
    m(E4, "py", "counting sorts the input in place", ("    counts: dict[str, int] = {}", '    matches.sort(key=lambda match: match.get("tournament") or "")\n    counts: dict[str, int] = {}')),
    m(E4, "js", "counting sorts the input in place", ("const counts = new Map();", "matches.sort((a, b) => (a.id ?? 0) - (b.id ?? 0));\n  const counts = new Map();")),
    m(E1, "py", "health ignores the body", ('return response.json().get("status") == "ok"', "return True")),
    m(E1, "js", "health ignores the body", ("return body.status === 'ok';", "return true;")),
    m(E7, "py", "drops the detail sentence", ("{detail or 'the API did not say why'}", "{'the API did not say why'}")),
    m(E7, "js", "drops the detail sentence", ("${safe.detail || 'the API did not say why'}", "the API did not say why")),
]

# Added after the second final review
MUTANTS += [
    m(E2, "py", "a walkover with no score row reads not started", ('if match.get("status") != "completed":\n            return "not started"', 'if True:\n            return "not started"')),
    m(E2, "js", "a walkover with no score row reads not started", ("if (match.status !== 'completed') return 'not started';", "return 'not started';")),
    m(E2, "py", "level sets announce player 2", ('            if sets[0] == sets[1]:\n                return f"{sets_text}, final"\n', "")),
    m(E2, "js", "level sets announce player 2", ("      if (sets[0] === sets[1]) return `${setsText}, final`;\n", "")),
    m(E8, "py", "ignores the caller's reserve", ("    interval = poll_interval_seconds(session_minutes, daily_budget, reserve)\n    usable = daily_budget - reserve", "    interval = poll_interval_seconds(session_minutes, daily_budget, 10)\n    usable = daily_budget - 10")),
    m(E8, "js", "ignores the caller's reserve", ("  const interval = pollIntervalSeconds(sessionMinutes, { dailyBudget, reserve });\n  const usable = dailyBudget - reserve;", "  const interval = pollIntervalSeconds(sessionMinutes, { dailyBudget, reserve: 10 });\n  const usable = dailyBudget - 10;")),
    m(E5, "py", "player detail sent without the key", ('get(f"{BASE_URL}/players/{int(player_id)}", auth_headers(key))', 'get(f"{BASE_URL}/players/{int(player_id)}", {"Accept": "application/json"})')),
    m(E5, "js", "player detail sent without the key", ("fetchImpl(`${BASE_URL}/players/${Number.parseInt(playerId, 10)}`, {\n    headers: authHeaders(key),", "fetchImpl(`${BASE_URL}/players/${Number.parseInt(playerId, 10)}`, {\n    headers: {},")),
    m(E6, "py", "max_attempts ignored", ("for attempt in range(max_attempts):", "for attempt in range(4):"), ("if attempt == max_attempts - 1:", "if attempt == 3:")),
    m(E6, "js", "maxAttempts ignored", ("attempt < maxAttempts;", "attempt < 4;"), ("if (attempt === maxAttempts - 1) break;", "if (attempt === 3) break;")),
]

# Added after the third final review
MUTANTS += [
    m(E4, "py", "WTA and juniors fall into other", ('TOUR_ORDER = ["atp", "wta", "challenger", "itf", "juniors"]', 'TOUR_ORDER = ["atp", "challenger", "itf"]')),
    m(E4, "js", "WTA and juniors fall into other", ("export const TOUR_ORDER = ['atp', 'wta', 'challenger', 'itf', 'juniors'];", "export const TOUR_ORDER = ['atp', 'challenger', 'itf'];")),
    m(E6, "py", "the retry drops the caller's headers", ("response = get(url, headers)", "response = get(url, headers if attempt == 0 else {})")),
    m(E6, "js", "the retry drops the caller's headers", ("const response = await fetchImpl(url, init);", "const response = await fetchImpl(url, attempt === 0 ? init : {});")),
]
