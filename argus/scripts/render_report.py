#!/usr/bin/env python3
"""Validate Argus findings JSON and render it as a markdown or self-contained HTML report.

No network calls, no dependencies. See references/report-format.md for the fields.
"""
import argparse
import datetime
import html
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
SOURCE_TYPES = ("primary", "secondary", "snippet")
SLOW_SPEED = 2  # channels scoring this low or lower on speed cannot take a weeks 1-2 validation slot
WEAK_FIT = 2  # a weeks 1-2 channel scoring this low or lower on icp_fit gets a note: the audience may be wrong

KNOWN = {
    "root": {"product_name", "research_mode", "product_url", "accessed_on", "language", "market", "summary",
             "biggest_uncertainty", "snapshot", "audit_findings", "icps", "evidence", "assumptions", "limits",
             "disconfirming", "channels", "budget_plan",
             "weeks", "copy", "experiments", "risks", "kill_criteria", "next_action"},
    "snapshot": {"problem", "promise", "stage", "pricing", "cta", "differentiation"},
    "icp": {"name", "primary", "job_to_be_done", "trigger", "alternatives", "objections"},
    "evidence": {"claim", "status", "confidence", "source_url", "source_type", "accessed_on", "note"},
    "channel": {"name", "scores", "rationale", "effort", "rule", "promotion_allowed", "basis"},
    "week": {"week", "objective", "actions", "signal", "gate"},
    "copy": {"positioning", "hooks", "launch_post", "reply_draft", "outreach_draft"},
    "experiment": {"hypothesis", "channel", "test", "kpi", "decision_gate", "budget_usd", "budget", "within_48h"},
}

# Almond eye used by the HTML report header (same mark as assets/build_logo.py).
EYE_ROWS = [(5, 9), (3, 11), (1, 13), (0, 14), (0, 14), (0, 14), (1, 13), (3, 11), (5, 9)]

SNAPSHOT_KEYS = ("problem", "promise", "stage", "pricing", "cta", "differentiation")

# Free-text fields that must be strings (null is the same as absent). A list or object here would print as a Python repr.
TEXT_FIELDS = {
    "icp": ("job_to_be_done", "trigger", "alternatives", "objections"),
    "channel": ("rationale", "effort", "rule"),
    "week": ("signal", "gate"),
    "copy": ("positioning", "launch_post", "reply_draft", "outreach_draft"),
    "experiment": ("channel", "test", "kpi", "decision_gate"),
    "snapshot": SNAPSHOT_KEYS,
}

STRINGS = {
    "en": {
        "title": "Argus", "mode": "Mode", "market": "Market", "accessed": "Accessed on", "product_url": "Product URL",
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
        "role_later": "Later", "role_slow": "Background (slow payoff)", "role_participate": "Participate only, no promotion",
        "role_verify": "Read the rules first",
        "audit": "Fixes on your own pages", "assumptions": "Assumptions", "limits": "What was not checked", "budget": "Budget plan",
        "assumption": "assumption",
        "legend": "Score /100 is a weighted sum. In brackets, the seven 1–5 inputs in this order: ICP fit·Intent·Reach·Speed·Cost·Ease·Safety. A comparison aid, not a forecast.",
        "hyp_scores": "Every score here rests on assumptions. Read them as a rough ordering of hypotheses, not as measured fit.",
        "sprint": "30-day sprint", "week": "Week", "signal": "Signal", "gate": "Stop/go gate",
        "copy": "Copy drafts", "positioning": "Positioning", "hooks": "Hooks",
        "launch_post": "Launch post", "reply": "Reply draft", "outreach": "Outreach draft (one to one)",
        "experiments": "Experiments", "ex_channel": "Channel", "ex_test": "Test", "ex_kpi": "KPI",
        "ex_gate": "Gate", "ex_budget": "Budget ceiling", "ex_48h": "can start within 48h",
        "risks": "Risks", "next": "Next action",
        "footer": "Drafts only. Nothing was posted or sent. Re-read each community's current rules before posting.",
    },
    "tr": {
        "title": "Argus", "mode": "Mod", "market": "Pazar", "accessed": "Erişim tarihi", "product_url": "Ürün URL'si",
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
        "role_later": "Sonra", "role_slow": "Arka planda (yavaş dönüş)", "role_participate": "Sadece katıl, tanıtım yok",
        "role_verify": "Önce kuralları oku",
        "audit": "Kendi sayfalarında düzeltilecekler", "assumptions": "Varsayımlar", "limits": "Kontrol edilemeyenler", "budget": "Bütçe planı",
        "assumption": "varsayım",
        "legend": "Skor /100 ağırlıklı toplamdır. Parantez içinde yedi girdi (her biri 1–5) şu sırayla: ICP uyumu·Niyet·Erişim·Hız·Maliyet·Kolaylık·Güvenlik. Karşılaştırma aracıdır, tahmin değildir.",
        "hyp_scores": "Buradaki her skor varsayıma dayanır. Ölçülmüş uyum değil, hipotezlerin kaba bir sıralaması olarak oku.",
        "sprint": "30 günlük sprint", "week": "Hafta", "signal": "Sinyal", "gate": "Dur/devam kapısı",
        "copy": "Metin taslakları", "positioning": "Konumlandırma", "hooks": "Kancalar",
        "launch_post": "Lansman gönderisi", "reply": "Yanıt taslağı", "outreach": "Birebir mesaj taslağı",
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


def _text_fields(obj, kind, label, problems):
    for key in TEXT_FIELDS[kind]:
        if obj.get(key) is not None and not isinstance(obj[key], str):
            problems.append(f"{label}.{key} must be a string (join several items with '; ')")


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
    if "product_url" in data and not _url(data["product_url"]):
        problems.append("product_url must be an http(s) URL")
    if mode == "live" and not _url(data.get("product_url")):
        problems.append("research_mode live requires product_url, the http(s) URL the user gave. "
                        "No URL from the user means no research: use hypothesis-only")
    if "language" in data and data["language"] not in LANGS:
        problems.append("language must be one of: " + ", ".join(LANGS))
    if "accessed_on" in data and not _date(data["accessed_on"]):
        problems.append("accessed_on must be a YYYY-MM-DD date")
    for key in ("market", "summary", "biggest_uncertainty", "next_action"):
        if key in data and not isinstance(data[key], str):
            problems.append(f"{key} must be a string")
    for key in ("risks", "kill_criteria", "disconfirming", "assumptions", "limits", "budget_plan", "audit_findings"):
        if not all(isinstance(x, str) for x in _items(data, key, problems)):
            problems.append(f"{key} must contain only strings")
    if "snapshot" in data and not isinstance(data["snapshot"], dict):
        problems.append("snapshot must be an object")
    elif "snapshot" in data:
        _text_fields(data["snapshot"], "snapshot", "snapshot", problems)

    evidence = _items(data, "evidence", problems)
    if mode == "hypothesis-only" and evidence:
        problems.append("Hypothesis-only reports must have an empty evidence ledger "
                        "(put what the user told you under assumptions)")
    elif mode == "live":
        for index, item in _dict_items(data, "evidence", problems):
            label = f"evidence[{index}]"
            if not _text(item.get("claim")):
                problems.append(f"{label}.claim is required")
            if item.get("status") not in STATUSES:
                problems.append(f"{label}.status must be one of: " + ", ".join(STATUSES))
            if item.get("confidence") not in CONFIDENCES:
                problems.append(f"{label}.confidence must be one of: " + ", ".join(CONFIDENCES))
            if "source_type" in item and item["source_type"] not in SOURCE_TYPES:
                problems.append(f"{label}.source_type must be one of: " + ", ".join(SOURCE_TYPES))
            if "note" in item and not isinstance(item["note"], str):
                problems.append(f"{label}.note must be a string")
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
        if "promotion_allowed" in channel and not (isinstance(channel["promotion_allowed"], bool) or channel["promotion_allowed"] == "unknown"):
            problems.append(f'{label}.promotion_allowed must be true, false or "unknown"')
        if "basis" in channel and channel["basis"] not in BASES:
            problems.append(f"{label}.basis must be one of: " + ", ".join(BASES))
        _text_fields(channel, "channel", label, problems)

    for index, week in _dict_items(data, "weeks", problems):
        label = f"weeks[{index}]"
        if not _is_int(week.get("week")):
            problems.append(f"{label}.week must be an integer")
        if not _text(week.get("objective")):
            problems.append(f"{label}.objective is required")
        actions = week.get("actions", [])
        if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
            problems.append(f"{label}.actions must be a list of strings")
        _text_fields(week, "week", label, problems)

    for index, icp in _dict_items(data, "icps", problems):
        if not _text(icp.get("name")):
            problems.append(f"icps[{index}].name is required")
        if "primary" in icp and not isinstance(icp["primary"], bool):
            problems.append(f"icps[{index}].primary must be true or false")
        _text_fields(icp, "icp", f"icps[{index}]", problems)

    for index, exp in _dict_items(data, "experiments", problems):
        label = f"experiments[{index}]"
        if not _text(exp.get("hypothesis")):
            problems.append(f"{label}.hypothesis is required")
        if "within_48h" in exp and not isinstance(exp["within_48h"], bool):
            problems.append(f"{label}.within_48h must be true or false")
        budget = exp.get("budget_usd")
        if "budget_usd" in exp and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget < 0):
            problems.append(f"{label}.budget_usd must be a non-negative number")
        if "budget" in exp and not _text(exp["budget"]):
            problems.append(f"{label}.budget must be a non-empty string such as \"500 TL\"")
        _text_fields(exp, "experiment", label, problems)

    copy = data.get("copy", {})
    if not isinstance(copy, dict):
        problems.append("copy must be an object")
    else:
        if not isinstance(copy.get("hooks", []), list) or not all(isinstance(h, str) for h in copy.get("hooks", [])):
            problems.append("copy.hooks must be a list of strings")
        _text_fields(copy, "copy", "copy", problems)

    if problems:
        raise ValueError("Invalid findings:\n" + "\n".join("- " + p for p in problems))


def _budget(exp):
    """Free-text `budget` (any currency) wins over `budget_usd`."""
    return exp["budget"].strip() if "budget" in exp else f'${exp["budget_usd"]:g}'


def _ranked(data):
    ranked = [(score(c["scores"]), c) for c in data.get("channels", [])]
    return sorted(ranked, key=lambda pair: pair[0], reverse=True)


def _eligible(ranked):
    return [pair for pair in ranked if pair[1].get("promotion_allowed", True) is True]


def _roles(ranked):
    """Map id(channel) -> sprint role.

    Channels that forbid promotion get no sprint role; channels whose rules are unknown must be read first. Slow channels (speed <= SLOW_SPEED)
    never take a weeks 1-2 validation slot, whatever their score.
    """
    roles = {}
    for _, channel in ranked:
        allowed = channel.get("promotion_allowed", True)
        if allowed is False:
            roles[id(channel)] = "participate"
        elif allowed != True:  # noqa: E712  ("unknown": rules unread or unreadable)
            roles[id(channel)] = "verify"
    fast = []
    for _, channel in _eligible(ranked):
        if channel["scores"]["speed"] <= SLOW_SPEED:
            roles[id(channel)] = "slow"
        else:
            fast.append(channel)
    for position, channel in enumerate(fast):
        roles[id(channel)] = "validate" if position < 2 else "checkpoint" if position == 2 else "later"
    return roles


def lint(data):
    """Return quality-gate warnings for a structurally valid report."""
    warnings = []
    mode = data["research_mode"]
    channels = data.get("channels", [])
    if not 2 <= len(channels) <= 8:
        warnings.append(f"Expected 2-8 scored channels, found {len(channels)}")
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


def notes(data):
    """Information worth showing that does not block --strict.

    These cannot always be cleared (blocked pages, no evidence yet), so they are not warnings.
    """
    out = []
    ranked = _ranked(data)
    eligible = _eligible(ranked)
    if len(eligible) < 2:
        out.append("Fewer than 2 channels allow promotion, so there is nothing to validate in weeks 1-2")
    elif sum(1 for _, c in eligible if c["scores"]["speed"] > SLOW_SPEED) < 2:
        out.append("Fewer than 2 promotable channels can show a signal within weeks (speed > 2)")
    roles = _roles(ranked)
    for _, channel in ranked:
        fit = channel["scores"]["icp_fit"]
        if roles.get(id(channel)) == "validate" and fit <= WEAK_FIT:
            out.append(f'"{channel["name"]}" has a weeks 1-2 slot but icp_fit is {fit}: '
                       "check that its audience is your primary ICP")
    if data["research_mode"] == "live":  # offline, every rule is unknown by definition
        for channel in data.get("channels", []):
            if channel.get("promotion_allowed") == "unknown":
                out.append(f'Promotion rules unknown for "{channel["name"]}": read them before posting there')
        if any(c.get("basis") == "assumption" for _, c in eligible[:2]):
            out.append("A top-two channel is scored on assumptions; verify it before committing")
    return out


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
    if data.get("product_url"):
        out[-1] += '  '
        out.append(f'**{t["product_url"]}:** <{data["product_url"]}>')
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

    if data.get("audit_findings"):
        out += ['', f'## {t["audit"]}'] + [f'- {inline(x)}' for x in data["audit_findings"]]

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
        if item.get("source_type"):
            url += f' ({item["source_type"]})'
        claim = cell(item["claim"]) + (f' *({cell(item["note"])})*' if item.get("note") else '')
        out.append('| ' + ' | '.join([claim, cell(item["status"]), cell(item["confidence"]),
                                      url, cell(item.get("accessed_on", "—"))]) + ' |')
    if not data.get("evidence"):
        out.append(f'| {t["no_evidence"]} | {t["unverified"]} | — | — | — |')

    for key, field_name in (("assumptions", "assumptions"), ("limits", "limits")):
        if data.get(field_name):
            out += ['', f'**{t[key]}**'] + [f'- {inline(x)}' for x in data[field_name]]

    if data.get("disconfirming") or data.get("kill_criteria"):
        out += ['', f'## {t["against"]}']
        out += [f'- {inline(x)}' for x in data.get("disconfirming", [])]
        if data.get("kill_criteria"):
            out += ['', f'**{t["kill"]}**']
            out += [f'- {inline(x)}' for x in data["kill_criteria"]]

    ranked = _ranked(data)
    roles = _roles(ranked)
    out += ['', f'## {t["channels"]}', '| ' + ' | '.join(t["ch_cols"]) + ' |', '|---|---:|---|---|---|---|']
    for points, channel in ranked:
        parts = '·'.join(str(channel["scores"][k]) for k in WEIGHTS)
        role = t["role_" + roles.get(id(channel), "participate")]
        rationale = cell(channel.get("rationale", ""))
        if channel.get("basis") == "assumption" and mode == "live":
            rationale = f'[{t["assumption"]}] {rationale}'.strip()
        out.append(f'| {cell(channel["name"])} | {points} ({parts}) | {role} | {rationale} | '
                   f'{cell(channel.get("effort", ""))} | {cell(channel.get("rule", ""))} |')
    if ranked:
        out += ['', f'*{t["legend"]}*']
        if mode == "hypothesis-only":
            out += ['', f'*{t["hyp_scores"]}*']

    if data.get("budget_plan"):
        out += ['', f'## {t["budget"]}'] + [f'- {inline(x)}' for x in data["budget_plan"]]

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
    if copy.get("outreach_draft"):
        out += ['', f'**{t["outreach"]}**', ''] + quote(copy["outreach_draft"], t["na"])

    out += ['', f'## {t["experiments"]}']
    for number, exp in enumerate(data.get("experiments", []), 1):
        out.append(f'{number}. **{inline(exp["hypothesis"])}**')
        for key, field in (("ex_channel", "channel"), ("ex_test", "test"), ("ex_kpi", "kpi"), ("ex_gate", "decision_gate")):
            if exp.get(field):
                out.append(f'   - {t[key]}: {inline(exp[field])}')
        if "budget" in exp or "budget_usd" in exp:
            out.append(f'   - {t["ex_budget"]}: {_budget(exp)}')
        if exp.get("within_48h"):
            out.append(f'   - ⏱ {t["ex_48h"]}')

    out += ['', f'## {t["risks"]}'] + [f'- {inline(r)}' for r in data.get("risks", [])]
    out += ['', f'**{t["next"]}:** {inline(data.get("next_action") or t["na"])}', '', '---', f'*{t["footer"]}*', '']
    return '\n'.join(out)


CSS = """
:root{--bg:#151713;--panel:#1d201a;--line:#2e3328;--fg:#ecefe6;--mute:#9aa18f;--accent:#c1ff00;--ink:#151713;--warn:#ffb020}
@media (prefers-color-scheme:light){:root{--bg:#f6f7f1;--panel:#fff;--line:#dfe3d3;--fg:#171a12;--mute:#5d6553;--accent:#4f7000;--ink:#fff;--warn:#a85d00}}
@media print{:root{--bg:#fff;--panel:#fff;--line:#cfd4c2;--fg:#111;--mute:#555;--accent:#3d5700;--ink:#fff;--warn:#8a4b00}nav,.noprint{display:none}.card,tr,blockquote{break-inside:avoid}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:40px 24px 64px}
.mono,nav a,.label,th,.badge,.chip{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
header{display:flex;gap:20px;align-items:center;margin-bottom:8px}
.eye{color:var(--accent);flex:none;filter:drop-shadow(2px 2px 0 color-mix(in srgb,var(--accent) 35%,transparent))}
.brand{font:700 13px/1 ui-monospace,Menlo,monospace;letter-spacing:.3em;color:var(--accent)}
h1{margin:6px 0 0;font-size:clamp(28px,5vw,44px);line-height:1.1;letter-spacing:-.02em}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0}
.chip{border:1px solid var(--line);background:var(--panel);padding:4px 10px;font-size:12px;color:var(--mute)}
.chip b{color:var(--fg);font-weight:600}
nav{display:flex;flex-wrap:wrap;gap:6px 16px;margin:28px 0 8px;padding:12px 0;border-block:1px solid var(--line)}
nav a{color:var(--mute);text-decoration:none;font-size:12px}nav a:hover{color:var(--accent)}
h2{display:flex;align-items:center;gap:12px;margin:44px 0 16px;font-size:22px;letter-spacing:-.01em}
h2::before{content:"";width:12px;height:12px;background:var(--accent);flex:none}
h3{margin:0 0 8px;font-size:17px}
.banner{margin:24px 0 0;padding:12px 16px;border:1px solid var(--warn);color:var(--warn);background:color-mix(in srgb,var(--warn) 8%,transparent)}
.verdict{font-size:19px;line-height:1.5;padding:22px 24px;background:var(--panel);border:1px solid var(--line);border-left:6px solid var(--accent);margin:0}
.callout{margin-top:14px;padding:12px 16px;border:1px dashed var(--line);color:var(--mute)}.callout b{color:var(--fg)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);padding:16px 18px}
.label{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin-bottom:2px}
dl{margin:0}dd{margin:0 0 10px}dt{margin:0}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:14px}
th{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);padding:10px 12px;border-bottom:1px solid var(--line)}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
.scroll{overflow-x:auto}
.bar{display:block;height:8px;background:var(--line);margin:6px 0 4px;min-width:90px}.bar i{display:block;height:100%;background:var(--accent)}
.score{font:700 20px/1 ui-monospace,Menlo,monospace}.dims{font:11px ui-monospace,Menlo,monospace;color:var(--mute)}
.badge{display:inline-block;padding:2px 8px;font-size:11px;border:1px solid var(--line);color:var(--mute);white-space:nowrap}
.badge.validate{background:var(--accent);color:var(--ink);border-color:var(--accent);font-weight:700}
.badge.checkpoint{border-color:var(--accent);color:var(--accent)}
.badge.slow{border-style:dashed}
.badge.verify{border-color:var(--warn);color:var(--warn);border-style:dashed}
.badge.participate{border-color:var(--warn);color:var(--warn)}
.badge.fast{background:var(--accent);color:var(--ink);border-color:var(--accent)}
tr.blocked td{opacity:.75}
.tag{color:var(--warn);font-size:12px}
.legend{margin:10px 0 0;color:var(--mute);font-size:13px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(min(100%,380px),1fr))}
.week .num{font:700 12px ui-monospace,Menlo,monospace;color:var(--accent);letter-spacing:.1em}
.week ul,ul.plain{margin:8px 0;padding-left:20px}
.gate{margin-top:10px;padding:8px 10px;border-left:3px solid var(--accent);background:color-mix(in srgb,var(--accent) 8%,transparent);font-size:14px}
.hooks{counter-reset:h;list-style:none;padding:0;margin:0;display:grid;gap:10px}
.hooks li{counter-increment:h;background:var(--panel);border:1px solid var(--line);padding:14px 18px 14px 56px;position:relative;font-size:17px}
.hooks li::before{content:counter(h);position:absolute;left:16px;top:12px;font:700 22px ui-monospace,Menlo,monospace;color:var(--accent)}
blockquote{margin:6px 0 18px;padding:14px 18px;background:var(--panel);border:1px solid var(--line);border-left:6px solid var(--line);white-space:pre-wrap}
.exp h3{display:flex;gap:10px;align-items:flex-start}.exp h3 span.n{font:700 18px ui-monospace,Menlo,monospace;color:var(--accent)}
.next{margin-top:36px;padding:22px 24px;background:var(--accent);color:var(--ink)}.next .label{color:inherit;opacity:.7}.next p{margin:4px 0 0;font-size:19px;font-weight:600}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);color:var(--mute);font-size:13px}
a{color:var(--accent)}
td.src{min-width:210px;font-size:13px;overflow-wrap:anywhere}td.date{white-space:nowrap}
"""


def _eye_svg(width=60):
    rects = ''.join(f'<rect x="{a}" y="{r}" width="{b - a + 1}" height="1"/>' for r, (a, b) in enumerate(EYE_ROWS))
    return (f'<svg class="eye" viewBox="0 0 15 9" width="{width}" height="{width * 9 / 15:g}" aria-hidden="true" '
            f'shape-rendering="crispEdges"><g fill="currentColor">{rects}</g>'
            '<rect x="6" y="3" width="3" height="3" fill="var(--bg)"/>'
            '<rect x="6" y="3" width="1" height="1" fill="currentColor"/></svg>')


def render_html(data, lang=None):
    """Self-contained HTML report: inline CSS, no scripts, no external requests."""
    validate(data)
    lang = lang or data.get("language", "en")
    if lang not in STRINGS:
        raise ValueError("language must be one of: " + ", ".join(LANGS))
    t = STRINGS[lang]
    mode = data["research_mode"]

    def e(value):
        return html.escape(" ".join(str(value).split()), quote=True)

    def block(value):
        text = str(value).strip() if value else ""
        return html.escape(text, quote=True) if text else e(t["na"])

    def field(label, value):
        return f'<dt class="label">{e(label)}</dt><dd>{e(value)}</dd>'

    def section(key, title, body):
        return f'<section id="{key}"><h2>{e(title)}</h2>{body}</section>'

    sections = []
    nav = []

    def add(key, title, body):
        nav.append(f'<a href="#{key}">{e(title)}</a>')
        sections.append(section(key, title, body))

    snapshot = data.get("snapshot", {})
    verdict = f'<p class="verdict">{e(data.get("summary") or t["na"])}</p>'
    if data.get("biggest_uncertainty"):
        verdict += f'<p class="callout"><b>{e(t["uncertainty"])}:</b> {e(data["biggest_uncertainty"])}</p>'
    add("verdict", t["verdict"], verdict)

    if any(snapshot.get(k) for k in SNAPSHOT_KEYS):
        items = ''.join(f'<div class="card"><dl>{field(t[k], snapshot[k])}</dl></div>' for k in SNAPSHOT_KEYS if snapshot.get(k))
        add("snapshot", t["snapshot"], f'<div class="grid">{items}</div>')

    if data.get("audit_findings"):
        add("audit", t["audit"], '<div class="card"><ul class="plain">' + ''.join(f'<li>{e(x)}</li>' for x in data["audit_findings"]) + '</ul></div>')

    if data.get("icps"):
        cards = []
        for icp in data["icps"]:
            tag = t["primary"] if icp.get("primary") else t["secondary"]
            rows = ''.join(field(t[k], icp[f]) for k, f in (("jtbd", "job_to_be_done"), ("trigger", "trigger"),
                           ("alternatives", "alternatives"), ("objections", "objections")) if icp.get(f))
            badge = f'<span class="badge {"validate" if icp.get("primary") else ""}">{e(tag)}</span>'
            cards.append(f'<article class="card"><h3>{e(icp["name"])} {badge}</h3><dl>{rows}</dl></article>')
        add("icps", t["icps"], f'<div class="grid">{"".join(cards)}</div>')

    rows = []
    for item in data.get("evidence", []):
        shown = re.sub(r"^https?://(www\.)?", "", item["source_url"]).rstrip("/") if item.get("source_url") else ""
        source = (f'<a href="{e(item["source_url"])}" rel="noopener noreferrer nofollow">{e(shown)}</a>'
                  if item.get("source_url") else '—')
        if item.get("source_type"):
            source += f' <span class="badge">{e(item["source_type"])}</span>'
        note = f'<div class="dims">{e(item["note"])}</div>' if item.get("note") else ''
        rows.append(f'<tr><td>{e(item["claim"])}{note}</td><td><span class="badge">{e(item["status"])}</span></td>'
                    f'<td>{e(item["confidence"])}</td><td class="src">{source}</td><td class="date">{e(item.get("accessed_on", "—"))}</td></tr>')
    if not rows:
        rows.append(f'<tr><td>{e(t["no_evidence"])}</td><td><span class="badge">{e(t["unverified"])}</span></td><td>—</td><td>—</td><td>—</td></tr>')
    head = ''.join(f'<th>{e(c)}</th>' for c in t["ev_cols"])
    add("evidence", t["evidence"], f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

    for key in ("assumptions", "limits"):
        if data.get(key):
            sections[-1] += (f'<h3 style="margin-top:20px">{e(t[key])}</h3><div class="card"><ul class="plain">'
                             + ''.join(f'<li>{e(x)}</li>' for x in data[key]) + '</ul></div>')

    if data.get("disconfirming") or data.get("kill_criteria"):
        body = ''
        if data.get("disconfirming"):
            body += '<div class="card"><ul class="plain">' + ''.join(f'<li>{e(x)}</li>' for x in data["disconfirming"]) + '</ul></div>'
        if data.get("kill_criteria"):
            body += (f'<div class="card"><span class="label">{e(t["kill"])}</span><ul class="plain">'
                     + ''.join(f'<li>{e(x)}</li>' for x in data["kill_criteria"]) + '</ul></div>')
        add("against", t["against"], f'<div class="grid">{body}</div>')

    ranked = _ranked(data)
    roles = _roles(ranked)
    if ranked:
        head = ''.join(f'<th>{e(c)}</th>' for c in t["ch_cols"])
        rows = []
        for points, channel in ranked:
            role = roles.get(id(channel), "participate")
            dims = '·'.join(str(channel["scores"][k]) for k in WEIGHTS)
            tag = f'<span class="tag">[{e(t["assumption"])}]</span> ' if channel.get("basis") == "assumption" and mode == "live" else ''
            rows.append(
                f'<tr class="{"blocked" if role in ("participate", "verify") else ""}"><td><b>{e(channel["name"])}</b></td>'
                f'<td><span class="score">{points}</span><span class="bar"><i style="width:{points}%"></i></span>'
                f'<span class="dims">{dims}</span></td>'
                f'<td><span class="badge {role}">{e(t["role_" + role])}</span></td>'
                f'<td>{tag}{e(channel.get("rationale", ""))}</td><td>{e(channel.get("effort", ""))}</td>'
                f'<td>{e(channel.get("rule", ""))}</td></tr>')
        add("channels", t["channels"], f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="legend">{e(t["legend"])}</p>'
            + (f'<p class="legend">{e(t["hyp_scores"])}</p>' if mode == "hypothesis-only" else ''))

    if data.get("budget_plan"):
        add("budget", t["budget"], '<div class="card"><ul class="plain">' + ''.join(f'<li>{e(x)}</li>' for x in data["budget_plan"]) + '</ul></div>')

    weeks = []
    for week in data.get("weeks", []):
        actions = ''.join(f'<li>{e(a)}</li>' for a in week.get("actions", []))
        signal = f'<p><span class="label">{e(t["signal"])}</span>{e(week["signal"])}</p>' if week.get("signal") else ''
        gate = f'<div class="gate"><span class="label">{e(t["gate"])}</span>{e(week["gate"])}</div>' if week.get("gate") else ''
        weeks.append(f'<article class="card week"><span class="num">{e(t["week"]).upper()} {week["week"]}</span>'
                     f'<h3>{e(week["objective"])}</h3><ul>{actions}</ul>{signal}{gate}</article>')
    add("sprint", t["sprint"], f'<div class="grid two">{"".join(weeks)}</div>')

    copy = data.get("copy", {})
    body = f'<span class="label">{e(t["positioning"])}</span><p class="verdict">{e(copy.get("positioning") or t["na"])}</p>'
    body += f'<h3 style="margin-top:22px">{e(t["hooks"])}</h3><ol class="hooks">' + ''.join(f'<li>{e(h)}</li>' for h in copy.get("hooks", [])) + '</ol>'
    body += f'<h3 style="margin-top:22px">{e(t["launch_post"])}</h3><blockquote>{block(copy.get("launch_post"))}</blockquote>'
    body += f'<h3>{e(t["reply"])}</h3><blockquote>{block(copy.get("reply_draft"))}</blockquote>'
    if copy.get("outreach_draft"):
        body += f'<h3>{e(t["outreach"])}</h3><blockquote>{block(copy["outreach_draft"])}</blockquote>'
    add("copy", t["copy"], body)

    cards = []
    for number, exp in enumerate(data.get("experiments", []), 1):
        fast = f'<span class="badge fast">⏱ {e(t["ex_48h"])}</span>' if exp.get("within_48h") else ''
        rows = ''.join(field(t[key], exp[f]) for key, f in (("ex_channel", "channel"), ("ex_test", "test"),
                       ("ex_kpi", "kpi"), ("ex_gate", "decision_gate")) if exp.get(f))
        if "budget" in exp or "budget_usd" in exp:
            rows += field(t["ex_budget"], _budget(exp))
        cards.append(f'<article class="card exp"><h3><span class="n">{number:02d}</span>{e(exp["hypothesis"])}</h3>{fast}<dl style="margin-top:10px">{rows}</dl></article>')
    add("experiments", t["experiments"], f'<div class="grid two">{"".join(cards)}</div>')

    if data.get("risks"):
        add("risks", t["risks"], '<div class="card"><ul class="plain">' + ''.join(f'<li>{e(r)}</li>' for r in data["risks"]) + '</ul></div>')

    chips = f'<span class="chip">{e(t["mode"])}: <b>{e(t["mode_" + mode])}</b></span>'
    chips += f'<span class="chip">{e(t["market"])}: <b>{e(data.get("market") or t["na"])}</b></span>'
    if data.get("product_url"):
        chips += (f'<span class="chip">{e(t["product_url"])}: <b><a href="{e(data["product_url"])}" '
                  f'rel="noopener noreferrer nofollow">{e(data["product_url"])}</a></b></span>')
    if data.get("accessed_on"):
        chips += f'<span class="chip">{e(t["accessed"])}: <b>{e(data["accessed_on"])}</b></span>'
    banner = f'<div class="banner">⚠ {e(t["banner"])}</div>' if mode == "hypothesis-only" else ''
    title = f'{t["title"]} — {data["product_name"]}'
    nxt = f'<div class="next"><span class="label">{e(t["next"])}</span><p>{e(data.get("next_action") or t["na"])}</p></div>'
    return (
        f'<!doctype html>\n<html lang="{lang}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:">'
        f'<meta name="generator" content="Argus"><title>{e(title)}</title><style>{CSS}</style></head><body><main>'
        f'<header>{_eye_svg()}<div><div class="brand">{e(t["title"]).upper()}</div><h1>{e(data["product_name"])}</h1></div></header>'
        f'<div class="chips">{chips}</div>{banner}<nav>{"".join(nav)}</nav>{"".join(sections)}{nxt}'
        f'<footer>{e(t["footer"])}</footer></main></body></html>\n'
    )


def _load(path):
    raw = sys.stdin.read() if path == '-' else Path(path).read_text(encoding='utf-8')
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('input', nargs='?', help='Findings JSON path, or - for stdin')
    parser.add_argument('-o', '--output', type=Path, help='Output markdown path; stdout by default')
    parser.add_argument('--format', choices=('md', 'html'), help='Output format (default: html if -o ends in .html, else md)')
    parser.add_argument('--html', dest='format', action='store_const', const='html', help='Shortcut for --format html')
    parser.add_argument('--lang', choices=LANGS, help='Heading language (overrides "language" in the JSON)')
    parser.add_argument('--check', action='store_true', help='Validate and lint only; render nothing')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--template', action='store_true', help='Print a findings JSON skeleton and exit')
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # reports contain "—", "⚠", "⏱"; legacy Windows consoles are not UTF-8
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    if args.template:
        print(json.dumps(TEMPLATE, indent=2, ensure_ascii=False))
        return 0
    if not args.input:
        parser.error('input is required unless --template is used')
    try:
        data = _load(args.input)
        validate(data)
        warnings = lint(data)
        for note in notes(data):
            print(f'note: {note}', file=sys.stderr)
        for warning in warnings:
            print(f'warning: {warning}', file=sys.stderr)
        if args.strict and warnings:
            print(f'Error: {len(warnings)} warning(s) in --strict mode', file=sys.stderr)
            return 1
        if args.check:
            print('OK' if not warnings else f'OK with {len(warnings)} warning(s)')
            return 0
        fmt = args.format or ('html' if args.output and args.output.suffix.lower() in ('.html', '.htm') else 'md')
        report = (render_html if fmt == 'html' else render)(data, args.lang)
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
