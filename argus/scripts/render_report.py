#!/usr/bin/env python3
"""Validate Argus findings JSON and render it as a markdown report.

No network calls, no dependencies. See references/report-format.md for the fields.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Integer weight points; they sum to 20, so the score is out of 100 with no float rounding.
WEIGHTS = {"icp_fit": 5, "intent": 4, "reachability": 3, "speed": 3, "cost": 2, "effort": 2, "risk": 1}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MODES = ("live", "hypothesis-only")
LANGS = ("en", "tr")
STATUSES = ("verified", "inference", "hypothesis")
CONFIDENCES = ("high", "medium", "low")
BASES = ("evidence", "assumption")

KNOWN = {
    "root": {"product_name", "research_mode", "accessed_on", "language", "market", "summary",
             "biggest_uncertainty", "snapshot", "icps", "evidence", "disconfirming", "channels",
             "weeks", "copy", "experiments", "risks", "kill_criteria", "next_action"},
    "snapshot": {"problem", "promise", "stage", "pricing", "cta", "differentiation"},
    "icp": {"name", "primary", "job_to_be_done", "trigger", "alternatives", "objections"},
    "evidence": {"claim", "status", "confidence", "source_url", "accessed_on"},
    "channel": {"name", "scores", "rationale", "effort", "rule", "promotion_allowed", "basis"},
    "week": {"week", "objective", "actions", "signal", "gate"},
    "copy": {"positioning", "hooks", "launch_post", "reply_draft"},
    "experiment": {"hypothesis", "channel", "test", "kpi", "decision_gate", "budget_usd", "within_48h"},
}

SNAPSHOT_KEYS = ("problem", "promise", "stage", "pricing", "cta", "differentiation")

STRINGS = {
    "en": {
        "title": "Argus", "mode": "Mode", "market": "Market", "accessed": "Accessed on",
        "mode_live": "live (web research)", "mode_hypothesis-only": "hypothesis-only",
        "banner": "Nothing in this report is verified. Treat every claim as a hypothesis and check it before acting.",
        "na": "Not provided", "verdict": "Verdict", "uncertainty": "Biggest uncertainty",
        "snapshot": "Product snapshot", "problem": "Problem", "promise": "Promise", "stage": "Stage",
        "pricing": "Pricing", "cta": "Call to action", "differentiation": "Differentiation",
        "icps": "Ideal customers", "primary": "primary", "secondary": "secondary",
        "jtbd": "Job to be done", "trigger": "Trigger", "alternatives": "Alternatives", "objections": "Objections",
        "evidence": "Evidence ledger", "ev_cols": ("Claim", "Status", "Confidence", "Source", "Accessed"),
        "no_evidence": "No verified live evidence in this report", "unverified": "unverified",
        "against": "Against the plan", "kill": "Kill criteria",
        "channels": "Channel ranking", "ch_cols": ("Channel", "Score /100", "Role", "Rationale", "Effort", "Rule / caveat"),
        "role_validate": "Validate now (weeks 1–2)", "role_checkpoint": "After checkpoint",
        "role_later": "Later", "role_participate": "Participate only, no promotion",
        "assumption": "assumption",
        "legend": "Score = ICP fit·Intent·Reach·Speed·Cost·Ease·Safety (1–5 each, weighted). A comparison aid, not a forecast.",
        "sprint": "30-day sprint", "week": "Week", "signal": "Signal", "gate": "Stop/go gate",
        "copy": "Copy drafts", "positioning": "Positioning", "hooks": "Hooks",
        "launch_post": "Launch post", "reply": "Reply draft",
        "experiments": "Experiments", "ex_channel": "Channel", "ex_test": "Test", "ex_kpi": "KPI",
        "ex_gate": "Gate", "ex_budget": "Budget ceiling", "ex_48h": "can start within 48h",
        "risks": "Risks", "next": "Next action",
        "footer": "Drafts only. Nothing was posted or sent. Re-read each community's current rules before posting.",
    },
    "tr": {
        "title": "Argus", "mode": "Mod", "market": "Pazar", "accessed": "Erişim tarihi",
        "mode_live": "canlı (web araştırması)", "mode_hypothesis-only": "yalnızca hipotez",
        "banner": "Bu raporda hiçbir şey doğrulanmadı. Her iddiayı hipotez say ve harekete geçmeden önce kontrol et.",
        "na": "Belirtilmedi", "verdict": "Karar", "uncertainty": "En büyük belirsizlik",
        "snapshot": "Ürün özeti", "problem": "Problem", "promise": "Vaat", "stage": "Aşama",
        "pricing": "Fiyatlandırma", "cta": "Eylem çağrısı", "differentiation": "Farklılaşma",
        "icps": "İdeal müşteriler", "primary": "birincil", "secondary": "ikincil",
        "jtbd": "Yapılacak iş", "trigger": "Tetikleyici", "alternatives": "Alternatifler", "objections": "İtirazlar",
        "evidence": "Kanıt defteri", "ev_cols": ("İddia", "Durum", "Güven", "Kaynak", "Erişim"),
        "no_evidence": "Bu raporda doğrulanmış canlı kanıt yok", "unverified": "doğrulanmadı",
        "against": "Plana karşı", "kill": "Durdurma kriterleri",
        "channels": "Kanal sıralaması", "ch_cols": ("Kanal", "Skor /100", "Rol", "Gerekçe", "Efor", "Kural / dikkat"),
        "role_validate": "Şimdi doğrula (hafta 1–2)", "role_checkpoint": "Kontrol noktasından sonra",
        "role_later": "Sonra", "role_participate": "Sadece katıl, tanıtım yok",
        "assumption": "varsayım",
        "legend": "Skor = ICP uyumu·Niyet·Erişim·Hız·Maliyet·Kolaylık·Güvenlik (her biri 1–5, ağırlıklı). Karşılaştırma aracıdır, tahmin değildir.",
        "sprint": "30 günlük sprint", "week": "Hafta", "signal": "Sinyal", "gate": "Dur/devam kapısı",
        "copy": "Metin taslakları", "positioning": "Konumlandırma", "hooks": "Kancalar",
        "launch_post": "Lansman gönderisi", "reply": "Yanıt taslağı",
        "experiments": "Deneyler", "ex_channel": "Kanal", "ex_test": "Test", "ex_kpi": "KPI",
        "ex_gate": "Kapı", "ex_budget": "Bütçe tavanı", "ex_48h": "48 saat içinde başlayabilir",
        "risks": "Riskler", "next": "Sonraki adım",
        "footer": "Yalnızca taslaktır. Hiçbir şey paylaşılmadı veya gönderilmedi. Paylaşmadan önce her topluluğun güncel kurallarını yeniden oku.",
    },
}

TEMPLATE = {
    "product_name": "Your product",
    "research_mode": "hypothesis-only",
    "language": "en",
    "market": "TODO: who and where",
    "summary": "TODO: 2-3 sentence verdict",
    "biggest_uncertainty": "TODO",
    "snapshot": {"problem": "TODO", "promise": "TODO", "stage": "TODO", "pricing": "TODO", "cta": "TODO", "differentiation": "TODO"},
    "icps": [{"name": "TODO primary ICP", "primary": True, "job_to_be_done": "TODO", "trigger": "TODO",
              "alternatives": "TODO", "objections": "TODO"}],
    "evidence": [],
    "disconfirming": ["TODO: evidence or open question against the plan"],
    "channels": [{"name": "TODO channel", "scores": {k: 3 for k in WEIGHTS}, "rationale": "TODO",
                  "effort": "TODO", "rule": "TODO: check current rules", "promotion_allowed": True, "basis": "assumption"}],
    "weeks": [{"week": n, "objective": "TODO", "actions": ["TODO"], "signal": "TODO", "gate": "TODO"} for n in range(1, 5)],
    "copy": {"positioning": "TODO", "hooks": ["TODO pain", "TODO outcome", "TODO contrast"],
             "launch_post": "TODO", "reply_draft": "TODO"},
    "experiments": [{"hypothesis": "TODO", "channel": "TODO", "test": "TODO", "kpi": "TODO",
                     "decision_gate": "Proposed: TODO", "within_48h": True}],
    "risks": ["TODO"],
    "kill_criteria": ["TODO"],
    "next_action": "TODO: something doable in 48 hours",
}


def score(values):
    """Weighted channel score out of 100. Every dimension must be an integer 1..5."""
    if not isinstance(values, dict) or set(values) != set(WEIGHTS):
        raise ValueError("Each channel requires exactly these scoring dimensions: " + ", ".join(WEIGHTS))
    for key, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"Invalid score for {key}: expected integer 1..5")
    return sum(WEIGHTS[key] * values[key] for key in WEIGHTS)


def _text(value):
    return isinstance(value, str) and value.strip() != ""


def _date(value):
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _url(value):
    if not isinstance(value, str) or any(c.isspace() or c in "<>" for c in value):
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _items(data, key, problems):
    value = data.get(key, [])
    if not isinstance(value, list):
        problems.append(f"{key} must be a list")
        return []
    return value


def _dict_items(data, key, problems):
    out = []
    for index, item in enumerate(_items(data, key, problems), 1):
        if isinstance(item, dict):
            out.append((index, item))
        else:
            problems.append(f"{key}[{index}] must be an object")
    return out


def validate(data):
    """Raise ValueError listing every structural problem found."""
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object")
    problems = []
    if not _text(data.get("product_name")):
        problems.append("product_name is required")
    mode = data.get("research_mode")
    if mode not in MODES:
        problems.append("research_mode must be live or hypothesis-only")
    if "language" in data and data["language"] not in LANGS:
        problems.append("language must be one of: " + ", ".join(LANGS))
    if "accessed_on" in data and not _date(data["accessed_on"]):
        problems.append("accessed_on must be a YYYY-MM-DD date")
    for key in ("market", "summary", "biggest_uncertainty", "next_action"):
        if key in data and not isinstance(data[key], str):
            problems.append(f"{key} must be a string")
    for key in ("risks", "kill_criteria", "disconfirming"):
        if not all(isinstance(x, str) for x in _items(data, key, problems)):
            problems.append(f"{key} must contain only strings")
    if "snapshot" in data and not isinstance(data["snapshot"], dict):
        problems.append("snapshot must be an object")

    evidence = _items(data, "evidence", problems)
    if mode == "hypothesis-only" and evidence:
        problems.append("Hypothesis-only reports must not contain a verified evidence ledger")
    elif mode == "live":
        for index, item in _dict_items(data, "evidence", problems):
            label = f"evidence[{index}]"
            if not _text(item.get("claim")):
                problems.append(f"{label}.claim is required")
            if item.get("status") not in STATUSES:
                problems.append(f"{label}.status must be one of: " + ", ".join(STATUSES))
            if item.get("confidence") not in CONFIDENCES:
                problems.append(f"{label}.confidence must be one of: " + ", ".join(CONFIDENCES))
            if "source_url" in item and not _url(item["source_url"]):
                problems.append(f"{label}.source_url must be an http(s) URL")
            if "accessed_on" in item and not _date(item["accessed_on"]):
                problems.append(f"{label}.accessed_on must be a YYYY-MM-DD date")
            if item.get("status") == "verified" and not (_url(item.get("source_url")) and _date(item.get("accessed_on"))):
                problems.append(f"{label} is verified but lacks a valid source_url and accessed_on")

    for index, channel in _dict_items(data, "channels", problems):
        label = f"channels[{index}]"
        if not _text(channel.get("name")):
            problems.append(f"{label}.name is required")
        try:
            score(channel.get("scores"))
        except ValueError as exc:
            problems.append(f"{label}: {exc}")
        if "promotion_allowed" in channel and not isinstance(channel["promotion_allowed"], bool):
            problems.append(f"{label}.promotion_allowed must be true or false")
        if "basis" in channel and channel["basis"] not in BASES:
            problems.append(f"{label}.basis must be one of: " + ", ".join(BASES))

    for index, week in _dict_items(data, "weeks", problems):
        label = f"weeks[{index}]"
        if not _is_int(week.get("week")):
            problems.append(f"{label}.week must be an integer")
        if not _text(week.get("objective")):
            problems.append(f"{label}.objective is required")
        actions = week.get("actions", [])
        if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
            problems.append(f"{label}.actions must be a list of strings")

    for index, icp in _dict_items(data, "icps", problems):
        if not _text(icp.get("name")):
            problems.append(f"icps[{index}].name is required")
        if "primary" in icp and not isinstance(icp["primary"], bool):
            problems.append(f"icps[{index}].primary must be true or false")

    for index, exp in _dict_items(data, "experiments", problems):
        label = f"experiments[{index}]"
        if not _text(exp.get("hypothesis")):
            problems.append(f"{label}.hypothesis is required")
        if "within_48h" in exp and not isinstance(exp["within_48h"], bool):
            problems.append(f"{label}.within_48h must be true or false")
        budget = exp.get("budget_usd")
        if "budget_usd" in exp and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget < 0):
            problems.append(f"{label}.budget_usd must be a non-negative number")

    copy = data.get("copy", {})
    if not isinstance(copy, dict):
        problems.append("copy must be an object")
    elif not isinstance(copy.get("hooks", []), list) or not all(isinstance(h, str) for h in copy.get("hooks", [])):
        problems.append("copy.hooks must be a list of strings")

    if problems:
        raise ValueError("Invalid findings:\n" + "\n".join("- " + p for p in problems))


def _ranked(data):
    ranked = [(score(c["scores"]), c) for c in data.get("channels", [])]
    return sorted(ranked, key=lambda pair: pair[0], reverse=True)


def _eligible(ranked):
    return [pair for pair in ranked if pair[1].get("promotion_allowed", True)]


def lint(data):
    """Return quality-gate warnings for a structurally valid report."""
    warnings = []
    mode = data["research_mode"]
    channels = data.get("channels", [])
    if not 3 <= len(channels) <= 8:
        warnings.append(f"Expected 3-8 scored channels, found {len(channels)}")
    eligible = _eligible(_ranked(data))
    if len(eligible) < 2:
        warnings.append("Fewer than 2 channels allow promotion, so there is nothing to validate in weeks 1-2")
    weeks = data.get("weeks", [])
    if len(weeks) != 4:
        warnings.append(f"Expected a 4-week sprint, found {len(weeks)} weeks")
    for week in weeks:
        if not _text(week.get("gate")):
            warnings.append(f"Week {week['week']} has no stop/go gate")
    hooks = data.get("copy", {}).get("hooks", [])
    if len(hooks) != 3:
        warnings.append(f"Expected 3 hooks, found {len(hooks)}")
    experiments = data.get("experiments", [])
    if len(experiments) != 5:
        warnings.append(f"Expected 5 experiments, found {len(experiments)}")
    if not any(e.get("within_48h") for e in experiments):
        warnings.append("No experiment is marked within_48h")
    if not data.get("disconfirming"):
        warnings.append("No disconfirming evidence or open questions listed")
    if not data.get("kill_criteria"):
        warnings.append("No kill criteria defined")
    if not _text(data.get("next_action")):
        warnings.append("No next_action given")
    if mode == "live":
        if not data.get("evidence"):
            warnings.append("Live mode but the evidence ledger is empty")
        if "accessed_on" not in data:
            warnings.append("Live mode but accessed_on is missing")
        if any(c.get("basis") == "assumption" for _, c in eligible[:2]):
            warnings.append("A top-two channel is scored on assumptions; verify it before committing")

    def unknown(label, obj, kind):
        extra = sorted(set(obj) - KNOWN[kind])
        if extra:
            warnings.append(f"Unknown field(s) in {label} (typo?): " + ", ".join(extra))

    unknown("report", data, "root")
    for kind, key in (("icp", "icps"), ("evidence", "evidence"), ("channel", "channels"),
                      ("week", "weeks"), ("experiment", "experiments")):
        for index, item in enumerate(data.get(key, []), 1):
            unknown(f"{key}[{index}]", item, kind)
    for kind, key in (("snapshot", "snapshot"), ("copy", "copy")):
        if isinstance(data.get(key), dict):
            unknown(key, data[key], kind)
    return warnings


def _esc(value):
    """Neutralize raw HTML that could ride in on untrusted research text."""
    return str(value).replace("<", "&lt;").replace(">", "&gt;")


def inline(value):
    """One line of text, safe inside a list item or a heading."""
    return _esc(" ".join(str(value).split()))


def cell(value):
    """Text safe inside a markdown table cell."""
    return inline(value).replace("|", "\\|")


def quote(value, fallback):
    text = str(value).strip() if value else ""
    if not text:
        return [f"> {fallback}"]
    return [("> " + _esc(line)).rstrip() for line in text.splitlines()]


def render(data, lang=None):
    validate(data)
    lang = lang or data.get("language", "en")
    if lang not in STRINGS:
        raise ValueError("language must be one of: " + ", ".join(LANGS))
    t = STRINGS[lang]
    mode = data["research_mode"]
    out = [f'# {t["title"]} — {inline(data["product_name"])}', '',
           f'**{t["mode"]}:** {t["mode_" + mode]}  ',
           f'**{t["market"]}:** {inline(data.get("market") or t["na"])}']
    if data.get("accessed_on"):
        out[-1] += '  '
        out.append(f'**{t["accessed"]}:** {data["accessed_on"]}')
    if mode == "hypothesis-only":
        out += ['', f'> ⚠️ {t["banner"]}']
    out += ['', f'## {t["verdict"]}', inline(data.get("summary") or t["na"])]
    if data.get("biggest_uncertainty"):
        out += ['', f'**{t["uncertainty"]}:** {inline(data["biggest_uncertainty"])}']

    snapshot = data.get("snapshot", {})
    if any(snapshot.get(k) for k in SNAPSHOT_KEYS):
        out += ['', f'## {t["snapshot"]}']
        out += [f'- **{t[k]}:** {inline(snapshot[k])}' for k in SNAPSHOT_KEYS if snapshot.get(k)]

    if data.get("icps"):
        out += ['', f'## {t["icps"]}']
        for icp in data["icps"]:
            tag = t["primary"] if icp.get("primary") else t["secondary"]
            out += ['', f'### {inline(icp["name"])} ({tag})']
            out += [f'- **{t[k]}:** {inline(icp[f])}' for k, f in
                    (("jtbd", "job_to_be_done"), ("trigger", "trigger"), ("alternatives", "alternatives"),
                     ("objections", "objections")) if icp.get(f)]

    out += ['', f'## {t["evidence"]}', '| ' + ' | '.join(t["ev_cols"]) + ' |', '|---|---|---|---|---|']
    for item in data.get("evidence", []):
        url = f'<{item["source_url"]}>' if item.get("source_url") else '—'
        out.append('| ' + ' | '.join([cell(item["claim"]), cell(item["status"]), cell(item["confidence"]),
                                      url, cell(item.get("accessed_on", "—"))]) + ' |')
    if not data.get("evidence"):
        out.append(f'| {t["no_evidence"]} | {t["unverified"]} | — | — | — |')

    if data.get("disconfirming") or data.get("kill_criteria"):
        out += ['', f'## {t["against"]}']
        out += [f'- {inline(x)}' for x in data.get("disconfirming", [])]
        if data.get("kill_criteria"):
            out += ['', f'**{t["kill"]}**']
            out += [f'- {inline(x)}' for x in data["kill_criteria"]]

    ranked = _ranked(data)
    roles = {}
    for position, (_, channel) in enumerate(_eligible(ranked)):
        roles[id(channel)] = "validate" if position < 2 else "checkpoint" if position == 2 else "later"
    out += ['', f'## {t["channels"]}', '| ' + ' | '.join(t["ch_cols"]) + ' |', '|---|---:|---|---|---|---|']
    for points, channel in ranked:
        parts = '·'.join(str(channel["scores"][k]) for k in WEIGHTS)
        role = t["role_" + roles.get(id(channel), "participate")]
        rationale = cell(channel.get("rationale", ""))
        if channel.get("basis") == "assumption":
            rationale = f'[{t["assumption"]}] {rationale}'.strip()
        out.append(f'| {cell(channel["name"])} | {points} ({parts}) | {role} | {rationale} | '
                   f'{cell(channel.get("effort", ""))} | {cell(channel.get("rule", ""))} |')
    if ranked:
        out += ['', f'*{t["legend"]}*']

    out += ['', f'## {t["sprint"]}']
    for week in data.get("weeks", []):
        out += ['', f'### {t["week"]} {week["week"]} — {inline(week["objective"])}']
        out += [f'- {inline(a)}' for a in week.get("actions", [])]
        if week.get("signal"):
            out.append(f'- **{t["signal"]}:** {inline(week["signal"])}')
        if week.get("gate"):
            out.append(f'- **{t["gate"]}:** {inline(week["gate"])}')

    copy = data.get("copy", {})
    out += ['', f'## {t["copy"]}', f'**{t["positioning"]}:** {inline(copy.get("positioning") or t["na"])}', '',
            f'**{t["hooks"]}**']
    out += [f'- {inline(h)}' for h in copy.get("hooks", [])]
    out += ['', f'**{t["launch_post"]}**', ''] + quote(copy.get("launch_post"), t["na"])
    out += ['', f'**{t["reply"]}**', ''] + quote(copy.get("reply_draft"), t["na"])

    out += ['', f'## {t["experiments"]}']
    for number, exp in enumerate(data.get("experiments", []), 1):
        out.append(f'{number}. **{inline(exp["hypothesis"])}**')
        for key, field in (("ex_channel", "channel"), ("ex_test", "test"), ("ex_kpi", "kpi"), ("ex_gate", "decision_gate")):
            if exp.get(field):
                out.append(f'   - {t[key]}: {inline(exp[field])}')
        if "budget_usd" in exp:
            out.append(f'   - {t["ex_budget"]}: ${exp["budget_usd"]:g}')
        if exp.get("within_48h"):
            out.append(f'   - ⏱ {t["ex_48h"]}')

    out += ['', f'## {t["risks"]}'] + [f'- {inline(r)}' for r in data.get("risks", [])]
    out += ['', f'**{t["next"]}:** {inline(data.get("next_action") or t["na"])}', '', '---', f'*{t["footer"]}*', '']
    return '\n'.join(out)


def _load(path):
    raw = sys.stdin.read() if path == '-' else Path(path).read_text(encoding='utf-8')
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('input', nargs='?', help='Findings JSON path, or - for stdin')
    parser.add_argument('-o', '--output', type=Path, help='Output markdown path; stdout by default')
    parser.add_argument('--lang', choices=LANGS, help='Heading language (overrides "language" in the JSON)')
    parser.add_argument('--check', action='store_true', help='Validate and lint only; render nothing')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--template', action='store_true', help='Print a findings JSON skeleton and exit')
    args = parser.parse_args(argv)
    if args.template:
        print(json.dumps(TEMPLATE, indent=2, ensure_ascii=False))
        return 0
    if not args.input:
        parser.error('input is required unless --template is used')
    try:
        data = _load(args.input)
        validate(data)
        warnings = lint(data)
        for warning in warnings:
            print(f'warning: {warning}', file=sys.stderr)
        if args.strict and warnings:
            print(f'Error: {len(warnings)} warning(s) in --strict mode', file=sys.stderr)
            return 1
        if args.check:
            print('OK' if not warnings else f'OK with {len(warnings)} warning(s)')
            return 0
        report = render(data, args.lang)
        if args.output:
            args.output.write_text(report, encoding='utf-8')
            print(f'Wrote {args.output}')
        else:
            print(report)
    except (ValueError, KeyError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
