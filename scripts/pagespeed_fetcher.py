#!/usr/bin/env python3
"""
pagespeed_fetcher.py
Coleta dados reais de performance via Google PageSpeed Insights API.
Retorna Lab Data, Field Data (CrUX), oportunidades e diagnósticos.
"""

import os
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_BASE  = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 3600  # PageSpeed sem cache longo — 1h é suficiente


# ──────────────────────────────────────────
# Thresholds oficiais do Google (Core Web Vitals)
# ──────────────────────────────────────────
CWV_THRESHOLDS = {
    "lcp":  {"good": 2.5,   "poor": 4.0},    # segundos
    "cls":  {"good": 0.1,   "poor": 0.25},   # score
    "fid":  {"good": 0.1,   "poor": 0.3},    # segundos
    "inp":  {"good": 0.2,   "poor": 0.5},    # segundos
    "ttfb": {"good": 0.8,   "poor": 1.8},    # segundos
    "fcp":  {"good": 1.8,   "poor": 3.0},    # segundos
    "tbt":  {"good": 0.2,   "poor": 0.6},    # segundos
}


def _cwv_status(metric: str, value: float) -> str:
    if metric not in CWV_THRESHOLDS:
        return "N/D"
    t = CWV_THRESHOLDS[metric]
    if value <= t["good"]:
        return "✅ Bom"
    if value <= t["poor"]:
        return "⚠️ Melhorar"
    return "🔴 Ruim"


def _cache_path(url: str, strategy: str) -> Path:
    key = hashlib.md5(f"{url}:{strategy}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"pagespeed-{key}.json"


def _load_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(seconds=CACHE_TTL):
            return data
    except Exception:
        pass
    return None


def _save_cache(path: Path, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_response(raw: dict, strategy: str) -> dict:
    """Extrai métricas relevantes da resposta raw da API."""
    result = {
        "strategy": strategy,
        "url": raw.get("id", ""),
        "scores": {},
        "lab_data": {},
        "field_data": {},
        "opportunities": [],
        "diagnostics": [],
        "page_weight": {},
        "status": "ok",
    }

    # ── Scores Lighthouse (0-100)
    categories = raw.get("lighthouseResult", {}).get("categories", {})
    score_map = {
        "performance":    "performance",
        "accessibility":  "accessibility",
        "best-practices": "best_practices",
        "seo":            "seo",
    }
    for api_key, out_key in score_map.items():
        cat = categories.get(api_key, {})
        score = cat.get("score")
        result["scores"][out_key] = int(score * 100) if score is not None else None

    # ── Lab Data (Lighthouse audits)
    audits = raw.get("lighthouseResult", {}).get("audits", {})

    lab_metrics = {
        "lcp":          ("largest-contentful-paint",  "numericValue", 1000),
        "cls":          ("cumulative-layout-shift",    "numericValue", 1),
        "tbt":          ("total-blocking-time",        "numericValue", 1000),
        "fcp":          ("first-contentful-paint",     "numericValue", 1000),
        "speed_index":  ("speed-index",                "numericValue", 1000),
        "tti":          ("interactive",                "numericValue", 1000),
    }

    for metric_key, (audit_id, field, divisor) in lab_metrics.items():
        audit = audits.get(audit_id, {})
        value = audit.get(field)
        if value is not None:
            converted = round(value / divisor, 3)
            result["lab_data"][metric_key] = {
                "value":        converted,
                "display":      audit.get("displayValue", ""),
                "status":       _cwv_status(metric_key, converted),
                "score":        audit.get("score"),
            }

    # ── Field Data (CrUX — usuários reais)
    crux = raw.get("loadingExperience", {})
    metrics_crux = crux.get("metrics", {})

    crux_map = {
        "lcp": "LARGEST_CONTENTFUL_PAINT_MS",
        "fid": "FIRST_INPUT_DELAY_MS",
        "cls": "CUMULATIVE_LAYOUT_SHIFT_SCORE",
        "inp": "INTERACTION_TO_NEXT_PAINT",
        "fcp": "FIRST_CONTENTFUL_PAINT_MS",
        "ttfb": "EXPERIMENTAL_TIME_TO_FIRST_BYTE",
    }

    for metric_key, crux_key in crux_map.items():
        crux_metric = metrics_crux.get(crux_key, {})
        if not crux_metric:
            continue

        category = crux_metric.get("category", "")
        p75 = crux_metric.get("percentile")

        status_map = {
            "FAST":    "✅ Bom",
            "AVERAGE": "⚠️ Melhorar",
            "SLOW":    "🔴 Ruim",
        }

        result["field_data"][metric_key] = {
            "status":   status_map.get(category, "N/D"),
            "category": category,
            "p75":      p75,
        }

    if not result["field_data"]:
        result["field_data"]["_note"] = "Dados de campo insuficientes (site com pouco tráfego)"

    # ── Oportunidades de melhoria (com saving estimado)
    opportunity_ids = [
        "render-blocking-resources",
        "unused-css-rules",
        "unused-javascript",
        "uses-optimized-images",
        "uses-webp-images",
        "uses-text-compression",
        "uses-responsive-images",
        "efficient-animated-content",
        "uses-long-cache-ttl",
        "eliminate-render-blocking-resources",
        "reduce-unused-javascript",
    ]

    for opp_id in opportunity_ids:
        audit = audits.get(opp_id, {})
        if not audit or audit.get("score", 1) == 1:
            continue
        savings_ms    = audit.get("details", {}).get("overallSavingsMs", 0)
        savings_bytes = audit.get("details", {}).get("overallSavingsBytes", 0)
        if savings_ms > 50 or savings_bytes > 5000:
            result["opportunities"].append({
                "id":           opp_id,
                "title":        audit.get("title", ""),
                "description":  audit.get("description", "")[:120],
                "savings_ms":   int(savings_ms),
                "savings_kb":   round(savings_bytes / 1024, 1),
                "score":        audit.get("score"),
            })

    # Ordenar por savings_ms desc
    result["opportunities"].sort(key=lambda x: x["savings_ms"], reverse=True)

    # ── Diagnósticos relevantes
    diagnostic_ids = [
        "mainthread-work-breakdown",
        "bootup-time",
        "uses-passive-event-listeners",
        "no-document-write",
        "dom-size",
        "critical-request-chains",
        "user-timings",
        "redirects",
        "uses-http2",
        "third-party-summary",
    ]

    for diag_id in diagnostic_ids:
        audit = audits.get(diag_id, {})
        if not audit or audit.get("score", 1) == 1:
            continue
        result["diagnostics"].append({
            "id":           diag_id,
            "title":        audit.get("title", ""),
            "display_value": audit.get("displayValue", ""),
            "score":        audit.get("score"),
        })

    # ── Peso da página
    resources = audits.get("resource-summary", {}).get("details", {}).get("items", [])
    for item in resources:
        label = item.get("label", "").lower().replace(" ", "_")
        size_bytes = item.get("transferSize", 0)
        if label and size_bytes:
            result["page_weight"][label] = round(size_bytes / 1024, 1)  # KB

    return result


def fetch(url: str, strategy: str = "mobile", use_cache: bool = True) -> dict:
    """
    Busca dados do PageSpeed para uma URL e estratégia.
    strategy: "mobile" | "desktop"
    """
    api_key = os.getenv("PAGESPEED_API_KEY", "")
    if not api_key:
        return {
            "status": "skipped",
            "reason": "PAGESPEED_API_KEY não configurada",
            "strategy": strategy,
            "url": url,
        }

    cache_path = _cache_path(url, strategy)
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    params = {
        "url":      url,
        "strategy": strategy,
        "key":      api_key,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }

    try:
        resp = requests.get(API_BASE, params=params, timeout=30)

        if resp.status_code == 429:
            return {"status": "rate_limited", "url": url, "strategy": strategy}

        if resp.status_code != 200:
            return {
                "status":      "error",
                "http_status": resp.status_code,
                "url":         url,
                "strategy":    strategy,
                "message":     resp.text[:200],
            }

        raw = resp.json()
        result = _parse_response(raw, strategy)
        _save_cache(cache_path, result)
        return result

    except requests.Timeout:
        return {"status": "timeout", "url": url, "strategy": strategy}
    except Exception as e:
        return {"status": "error", "url": url, "strategy": strategy, "message": str(e)}


def fetch_both(url: str, use_cache: bool = True) -> dict:
    """Busca mobile e desktop, com pausa para respeitar rate limit."""
    mobile  = fetch(url, "mobile",  use_cache)
    time.sleep(1)
    desktop = fetch(url, "desktop", use_cache)
    return {"url": url, "mobile": mobile, "desktop": desktop}


def fetch_multiple(urls: list[str], strategy: str = "mobile") -> list[dict]:
    """Busca múltiplas URLs com pausa entre requests."""
    results = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(1.5)
        results.append(fetch(url, strategy))
    return results


def to_markdown(data: dict) -> str:
    """Formata dados do PageSpeed como Markdown estruturado."""
    mobile  = data.get("mobile", {})
    desktop = data.get("desktop", {})
    url     = data.get("url", "")

    if mobile.get("status") == "skipped":
        return (
            "## PAGESPEED INSIGHTS\n\n"
            "> ⏭️ Módulo pulado — PAGESPEED_API_KEY não configurada.\n"
            "> Dados de performance serão estimados via Tavily.\n"
        )

    lines = ["## PAGESPEED INSIGHTS", ""]
    lines.append(f"*Fonte: PageSpeed Insights API — dados reais Google | URL: {url}*")
    lines.append("")

    # ── Scores
    lines.append("### Scores")
    lines.append("")
    lines.append("| Categoria | Mobile | Desktop |")
    lines.append("|---|---|---|")

    def fmt_score(s):
        if s is None: return "N/D"
        if s >= 90: return f"{s}/100 🏆"
        if s >= 75: return f"{s}/100 ✅"
        if s >= 50: return f"{s}/100 🟡"
        return f"{s}/100 🔴"

    score_labels = [
        ("performance",   "Performance"),
        ("accessibility", "Acessibilidade"),
        ("best_practices","Boas Práticas"),
        ("seo",           "SEO Básico"),
    ]
    for key, label in score_labels:
        m = fmt_score(mobile.get("scores", {}).get(key))
        d = fmt_score(desktop.get("scores", {}).get(key))
        lines.append(f"| {label} | {m} | {d} |")

    lines.append("")

    # ── Lab Data
    lines.append("### Core Web Vitals — Lab Data (Lighthouse)")
    lines.append("")
    lines.append("| Métrica | Mobile | Desktop | Status Mobile |")
    lines.append("|---|---|---|---|")

    metric_labels = [
        ("lcp",         "LCP"),
        ("cls",         "CLS"),
        ("tbt",         "TBT"),
        ("fcp",         "FCP"),
        ("speed_index", "Speed Index"),
    ]
    for key, label in metric_labels:
        m_data = mobile.get("lab_data", {}).get(key, {})
        d_data = desktop.get("lab_data", {}).get(key, {})
        m_val  = m_data.get("display", "N/D")
        d_val  = d_data.get("display", "N/D")
        status = m_data.get("status", "N/D")
        lines.append(f"| {label} | {m_val} | {d_val} | {status} |")

    lines.append("")

    # ── Field Data (CrUX)
    field = mobile.get("field_data", {})
    note  = field.get("_note")
    if note:
        lines.append(f"### Core Web Vitals — Field Data (Usuários Reais)")
        lines.append("")
        lines.append(f"> ⚠️ {note}")
    else:
        lines.append("### Core Web Vitals — Field Data (Usuários Reais / CrUX)")
        lines.append("")
        lines.append("| Métrica | Status | Percentil 75 |")
        lines.append("|---|---|---|")
        for key, label in [("lcp","LCP"),("cls","CLS"),("inp","INP"),("fcp","FCP"),("ttfb","TTFB")]:
            fd = field.get(key)
            if fd:
                p75 = fd.get("p75", "N/D")
                lines.append(f"| {label} | {fd['status']} | {p75} |")

    lines.append("")

    # ── Oportunidades
    opps = mobile.get("opportunities", [])
    lines.append("### Oportunidades de Melhoria")
    lines.append("")
    if not opps:
        lines.append("✅ Nenhuma oportunidade crítica identificada.")
    else:
        lines.append("| Oportunidade | Economia (ms) | Economia (KB) |")
        lines.append("|---|---|---|")
        for opp in opps[:8]:
            ms = f"{opp['savings_ms']}ms" if opp['savings_ms'] else "—"
            kb = f"{opp['savings_kb']}KB" if opp['savings_kb'] else "—"
            lines.append(f"| {opp['title']} | {ms} | {kb} |")

    lines.append("")

    # ── Peso da página
    weights = mobile.get("page_weight", {})
    if weights:
        lines.append("### Peso da Página (Mobile)")
        lines.append("")
        lines.append("| Recurso | Tamanho |")
        lines.append("|---|---|")
        label_map = {
            "total":       "Total",
            "script":      "JavaScript",
            "stylesheet":  "CSS",
            "image":       "Imagens",
            "font":        "Fontes",
            "document":    "HTML",
            "other":       "Outros",
        }
        for key, label in label_map.items():
            val = weights.get(key)
            if val:
                lines.append(f"| {label} | {val} KB |")

    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PageSpeed Insights fetcher")
    parser.add_argument("--url",      required=True, help="URL a testar")
    parser.add_argument("--strategy", default="both", choices=["mobile","desktop","both"])
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--json",     action="store_true", help="Output JSON bruto")
    args = parser.parse_args()

    use_cache = not args.no_cache

    if args.strategy == "both":
        data = fetch_both(args.url, use_cache)
    else:
        data = fetch(args.url, args.strategy, use_cache)
        data = {"url": args.url, args.strategy: data}

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(data))
