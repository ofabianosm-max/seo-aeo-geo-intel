#!/usr/bin/env python3
"""
backlink_fetcher.py
Módulo 14 — Backlinks (opcional).
Suporta Ahrefs API e Semrush API. Usa o que estiver configurado.
Se nenhum estiver configurado, retorna status skipped.
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400 * 2   # 48h — dados de backlink mudam devagar


def _cache_path(site: str, source: str) -> Path:
    key = hashlib.md5(f"{site}:{source}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"backlinks-{key}.json"


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


# ──────────────────────────────────────────
# Ahrefs
# ──────────────────────────────────────────

def _fetch_ahrefs(site: str) -> dict:
    key = os.getenv("AHREFS_API_KEY", "")
    if not key:
        return {"status": "skipped", "reason": "AHREFS_API_KEY não configurada"}

    BASE = "https://apiv2.ahrefs.com"

    def _get(endpoint: str, params: dict) -> dict:
        try:
            r = requests.get(
                BASE,
                params={"from": endpoint, "target": site, "token": key,
                        "output": "json", "mode": "domain", **params},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()
            return {"error": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    # Métricas gerais
    metrics = _get("ahrefs_rank", {})
    domain_rating = metrics.get("domain_rating", {}).get("domain_rating")

    backlinks_data = _get("backlinks_stats", {})
    stats = backlinks_data.get("stats", {})

    # Top referring domains
    ref_domains = _get("refdomains", {"limit": 50, "order_by": "dofollow_linked_domains:desc"})
    domains_list = ref_domains.get("refdomains", [])

    return {
        "source":             "ahrefs",
        "domain_rating":      domain_rating,
        "backlinks_total":    stats.get("all", 0),
        "backlinks_dofollow": stats.get("dofollow", 0),
        "backlinks_nofollow": stats.get("nofollow", 0),
        "referring_domains":  stats.get("refdomains", 0),
        "top_ref_domains":    [
            {
                "domain":     d.get("refdomains", ""),
                "dr":         d.get("domain_rating", 0),
                "links":      d.get("backlinks", 0),
                "dofollow":   d.get("dofollow", True),
            }
            for d in domains_list[:20]
        ],
        "status": "ok",
    }


# ──────────────────────────────────────────
# Semrush
# ──────────────────────────────────────────

def _fetch_semrush(site: str) -> dict:
    key = os.getenv("SEMRUSH_API_KEY", "")
    if not key:
        return {"status": "skipped", "reason": "SEMRUSH_API_KEY não configurada"}

    BASE = "https://api.semrush.com"

    def _get(report_type: str, params: dict = {}) -> str:
        try:
            r = requests.get(
                BASE,
                params={"type": report_type, "key": key,
                        "target": site, "target_type": "root_domain",
                        "export_columns": params.get("columns", ""), **params},
                timeout=15,
            )
            return r.text if r.status_code == 200 else ""
        except Exception:
            return ""

    # Authority Score e backlinks gerais
    overview_raw = _get("backlinks_overview",
                        {"columns": "ascore,total,domains_num,follows_num,nofollows_num"})

    result = {
        "source":             "semrush",
        "authority_score":    None,
        "backlinks_total":    None,
        "referring_domains":  None,
        "backlinks_dofollow": None,
        "backlinks_nofollow": None,
        "status":             "ok",
    }

    if overview_raw and "ERROR" not in overview_raw:
        lines = overview_raw.strip().splitlines()
        if len(lines) >= 2:
            vals = lines[1].split(";")
            try:
                result["authority_score"]    = int(vals[0]) if vals[0] else None
                result["backlinks_total"]    = int(vals[1]) if vals[1] else None
                result["referring_domains"]  = int(vals[2]) if vals[2] else None
                result["backlinks_dofollow"] = int(vals[3]) if vals[3] else None
                result["backlinks_nofollow"] = int(vals[4]) if vals[4] else None
            except (IndexError, ValueError):
                pass

    # Top referring domains
    ref_raw = _get("backlinks_refdomains",
                   {"columns": "domain_ascore,source_url,external_num,internal_num",
                    "display_limit": "20", "display_sort": "domain_ascore_desc"})

    domains_list = []
    if ref_raw and "ERROR" not in ref_raw:
        lines = ref_raw.strip().splitlines()
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) >= 2:
                try:
                    domains_list.append({
                        "domain": parts[1].split("/")[0],
                        "as":     int(parts[0]) if parts[0] else 0,
                    })
                except Exception:
                    pass

    result["top_ref_domains"] = domains_list[:20]
    return result


# ──────────────────────────────────────────
# Link Gap
# ──────────────────────────────────────────

def _link_gap_ahrefs(site: str, competitors: list[str]) -> list[dict]:
    key = os.getenv("AHREFS_API_KEY", "")
    if not key or not competitors:
        return []

    try:
        r = requests.get(
            "https://apiv2.ahrefs.com",
            params={
                "from":    "linked_domains",
                "target":  site,
                "token":   key,
                "output":  "json",
                "mode":    "domain",
                "limit":   50,
            },
            timeout=15,
        )
        if r.status_code != 200:
            return []

        your_domains = {d.get("linked_domain", "") for d in r.json().get("linked_domains", [])}
        gaps = []

        for comp in competitors[:3]:
            r2 = requests.get(
                "https://apiv2.ahrefs.com",
                params={"from": "linked_domains", "target": comp, "token": key,
                        "output": "json", "mode": "domain", "limit": 50},
                timeout=15,
            )
            if r2.status_code != 200:
                continue

            comp_domains = r2.json().get("linked_domains", [])
            for d in comp_domains:
                domain = d.get("linked_domain", "")
                if domain and domain not in your_domains:
                    gaps.append({
                        "domain":   domain,
                        "dr":       d.get("domain_rating", 0),
                        "links_to": comp,
                        "opportunity": "🔴 Alta" if d.get("domain_rating", 0) >= 50 else "🟡 Média",
                    })

        gaps.sort(key=lambda g: -g["dr"])
        return gaps[:20]

    except Exception:
        return []


# ──────────────────────────────────────────
# Fetch principal
# ──────────────────────────────────────────

def fetch(site: str, competitors: list[str] = None, use_cache: bool = True) -> dict:
    """Tenta Ahrefs primeiro, depois Semrush."""
    ahrefs_key  = os.getenv("AHREFS_API_KEY", "")
    semrush_key = os.getenv("SEMRUSH_API_KEY", "")

    if not ahrefs_key and not semrush_key:
        return {
            "site":   site,
            "status": "skipped",
            "reason": "AHREFS_API_KEY e SEMRUSH_API_KEY não configuradas — Módulo 14 desativado",
        }

    source = "ahrefs" if ahrefs_key else "semrush"
    cache_path = _cache_path(site, source)

    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    if ahrefs_key:
        data = _fetch_ahrefs(site)
        if data.get("status") == "ok" and competitors:
            data["link_gap"] = _link_gap_ahrefs(site, competitors)
    else:
        data = _fetch_semrush(site)
        data["link_gap"] = []  # Semrush link gap requer endpoints específicos

    data["site"] = site
    _save_cache(cache_path, data)
    return data


def to_markdown(data: dict) -> str:
    if data.get("status") == "skipped":
        return (
            "## MÓDULO 14 — BACKLINKS\n\n"
            f"> ⏭️ Pulado — {data.get('reason', 'API não configurada')}\n"
        )

    site   = data.get("site", "")
    source = data.get("source", "").upper()
    lines  = [f"## MÓDULO 14 — BACKLINKS (fonte: {source})", ""]

    # Métricas gerais
    lines += ["### Perfil de Backlinks", "",
              "| Métrica | Valor |",
              "|---|---|"]

    if data.get("domain_rating") is not None:
        lines.append(f"| Domain Rating (Ahrefs) | {data['domain_rating']}/100 |")
    if data.get("authority_score") is not None:
        lines.append(f"| Authority Score (Semrush) | {data['authority_score']}/100 |")

    lines.append(f"| Backlinks totais | {data.get('backlinks_total', 'N/D')} |")
    lines.append(f"| Domínios de referência | {data.get('referring_domains', 'N/D')} |")
    lines.append(f"| Dofollow | {data.get('backlinks_dofollow', 'N/D')} |")
    lines.append(f"| Nofollow | {data.get('backlinks_nofollow', 'N/D')} |")
    lines.append("")

    # Top ref domains
    top_domains = data.get("top_ref_domains", [])
    if top_domains:
        lines += ["### Top Domínios que Apontam para o Site", "",
                  "| Domínio | DR/AS | Links |",
                  "|---|---|---|"]
        for d in top_domains[:10]:
            dr   = d.get("dr", d.get("as", "N/D"))
            lks  = d.get("links", "N/D")
            lines.append(f"| {d.get('domain','?')} | {dr} | {lks} |")
        lines.append("")

    # Link gap
    gaps = data.get("link_gap", [])
    if gaps:
        lines += [
            "### Link Gap — Oportunidades de Link Building", "",
            "| Domínio | DR | Linka para | Oportunidade |",
            "|---|---|---|---|",
        ]
        for g in gaps[:10]:
            lines.append(
                f"| {g['domain']} | {g['dr']} | "
                f"{g['links_to']} | {g['opportunity']} |"
            )
        lines.append("")
        lines.append(
            "🎯 **Ação:** Contate os domínios de oportunidade Alta e proponha "
            "guest post, parceria ou menção. São sites que já reconhecem valor no seu nicho."
        )
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backlink Fetcher")
    parser.add_argument("--site",        required=True)
    parser.add_argument("--competitors", default="")
    parser.add_argument("--no-cache",    action="store_true")
    parser.add_argument("--md",          action="store_true")
    args = parser.parse_args()

    competitors = args.competitors.split(",") if args.competitors else []
    data = fetch(args.site, competitors, use_cache=not args.no_cache)
    print(to_markdown(data) if args.md else json.dumps(data, ensure_ascii=False, indent=2))
