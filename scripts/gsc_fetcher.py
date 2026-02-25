#!/usr/bin/env python3
"""
gsc_fetcher.py
Coleta dados reais do Google Search Console:
- Performance (clicks, impressões, CTR, posição)
- Cobertura de indexação
- Sitemaps
- Inspeção de URLs individuais
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400  # 24h


def _cache_path(site: str, report: str, params: str = "") -> Path:
    key = hashlib.md5(f"{site}:{report}:{params}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"gsc-{key}.json"


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


def _build_service():
    """Cria o cliente autenticado do GSC."""
    cred_env = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
    if not cred_env:
        raise EnvironmentError("GSC_SERVICE_ACCOUNT_JSON não configurado.")

    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    import tempfile

    SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

    # Pode ser path de arquivo ou conteúdo JSON inline
    if os.path.isfile(cred_env):
        creds = service_account.Credentials.from_service_account_file(cred_env, scopes=SCOPES)
    else:
        cred_dict = json.loads(cred_env)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(cred_dict, tmp)
        tmp.close()
        creds = service_account.Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

    return build("searchconsole", "v1", credentials=creds)


def list_sites() -> list[dict]:
    """Lista todas as propriedades verificadas no GSC."""
    try:
        service = _build_service()
        resp = service.sites().list().execute()
        return resp.get("siteEntry", [])
    except Exception as e:
        return [{"error": str(e)}]


def fetch_performance(
    site: str,
    days: int = 30,
    dimensions: list[str] = None,
    row_limit: int = 500,
    use_cache: bool = True,
) -> dict:
    """
    Busca dados de performance do GSC.
    dimensions: ["query", "page", "device", "country", "date"]
    """
    if dimensions is None:
        dimensions = ["query"]

    end_date   = date.today() - timedelta(days=3)   # GSC tem delay de ~3 dias
    start_date = end_date - timedelta(days=days)

    cache_key  = f"{days}d:{'_'.join(dimensions)}:{row_limit}"
    cache_path = _cache_path(site, "performance", cache_key)

    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    try:
        service = _build_service()
        body = {
            "startDate":  start_date.isoformat(),
            "endDate":    end_date.isoformat(),
            "dimensions": dimensions,
            "rowLimit":   row_limit,
        }
        resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
        rows = resp.get("rows", [])

        result = {
            "site":       site,
            "start_date": start_date.isoformat(),
            "end_date":   end_date.isoformat(),
            "dimensions": dimensions,
            "total_rows": len(rows),
            "rows":       rows,
            "status":     "ok",
        }
        _save_cache(cache_path, result)
        return result

    except Exception as e:
        return {"status": "error", "message": str(e), "site": site}


def fetch_top_queries(site: str, days: int = 30, limit: int = 100) -> dict:
    """Top queries por clicks."""
    data = fetch_performance(site, days, ["query"], limit)
    if data.get("status") != "ok":
        return data

    rows = data["rows"]
    rows.sort(key=lambda r: r.get("clicks", 0), reverse=True)

    result = {
        "site":    site,
        "period":  f"{days}d",
        "queries": [],
        "status":  "ok",
    }

    for row in rows[:limit]:
        keys = row.get("keys", [])
        result["queries"].append({
            "query":       keys[0] if keys else "",
            "clicks":      int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })

    return result


def fetch_opportunity_queries(site: str, days: int = 30) -> dict:
    """
    Keywords na zona de oportunidade:
    - Posições 8-20 (quick wins para top 10)
    - CTR < 2% mas impressões altas (latent demand)
    """
    data = fetch_performance(site, days, ["query"], 1000)
    if data.get("status") != "ok":
        return data

    rows = data["rows"]
    opportunities = []
    latent = []

    for row in rows:
        keys       = row.get("keys", [])
        impressions = int(row.get("impressions", 0))
        clicks     = int(row.get("clicks", 0))
        ctr        = row.get("ctr", 0) * 100
        position   = row.get("position", 0)
        query      = keys[0] if keys else ""

        if 8 <= position <= 20 and impressions >= 50:
            opportunities.append({
                "query":       query,
                "position":    round(position, 1),
                "impressions": impressions,
                "clicks":      clicks,
                "ctr":         round(ctr, 2),
            })

        if ctr < 2.0 and impressions >= 200 and position <= 30:
            latent.append({
                "query":       query,
                "position":    round(position, 1),
                "impressions": impressions,
                "clicks":      clicks,
                "ctr":         round(ctr, 2),
            })

    opportunities.sort(key=lambda r: r["impressions"], reverse=True)
    latent.sort(key=lambda r: r["impressions"], reverse=True)

    return {
        "site":             site,
        "period":           f"{days}d",
        "opportunity_zone": opportunities[:50],  # pos 8-20
        "latent_demand":    latent[:30],          # alto impressão, baixo CTR
        "status":           "ok",
    }


def fetch_position_changes(site: str) -> dict:
    """
    Compara períodos para detectar quedas e ganhos.
    Período atual vs período anterior (ambos de 28 dias).
    """
    def _get_period(days_ago_start: int, days_ago_end: int, limit: int = 500):
        end   = date.today() - timedelta(days=days_ago_end + 3)
        start = end - timedelta(days=28)
        try:
            service = _build_service()
            body = {
                "startDate":  start.isoformat(),
                "endDate":    end.isoformat(),
                "dimensions": ["query"],
                "rowLimit":   limit,
            }
            resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
            rows = resp.get("rows", [])
            return {r["keys"][0]: r for r in rows if r.get("keys")}
        except Exception:
            return {}

    current  = _get_period(0, 0)
    previous = _get_period(28, 28)

    changes = {"drops": [], "gains": [], "new_queries": []}

    for query, curr in current.items():
        curr_pos = curr.get("position", 100)
        curr_clicks = int(curr.get("clicks", 0))
        curr_imp = int(curr.get("impressions", 0))

        if query in previous:
            prev_pos = previous[query].get("position", 100)
            delta = curr_pos - prev_pos  # positivo = caiu, negativo = subiu

            if delta >= 3 and curr_imp >= 20:  # caiu 3+ posições
                changes["drops"].append({
                    "query":         query,
                    "position_prev": round(prev_pos, 1),
                    "position_curr": round(curr_pos, 1),
                    "delta":         round(delta, 1),
                    "clicks_lost_est": max(0, int(curr_clicks * delta * 0.05)),
                    "impressions":   curr_imp,
                })
            elif delta <= -3 and curr_imp >= 20:  # subiu 3+ posições
                changes["gains"].append({
                    "query":         query,
                    "position_prev": round(prev_pos, 1),
                    "position_curr": round(curr_pos, 1),
                    "delta":         round(abs(delta), 1),
                    "impressions":   curr_imp,
                })
        else:
            if curr_imp >= 50:  # nova keyword com volume relevante
                changes["new_queries"].append({
                    "query":       query,
                    "position":    round(curr_pos, 1),
                    "impressions": curr_imp,
                    "clicks":      curr_clicks,
                })

    changes["drops"].sort(key=lambda r: r["impressions"], reverse=True)
    changes["gains"].sort(key=lambda r: r["impressions"], reverse=True)
    changes["new_queries"].sort(key=lambda r: r["impressions"], reverse=True)

    return {"site": site, "status": "ok", **changes}


def fetch_top_pages(site: str, days: int = 30, limit: int = 50) -> dict:
    """Top páginas por tráfego."""
    data = fetch_performance(site, days, ["page"], limit * 2)
    if data.get("status") != "ok":
        return data

    rows = data["rows"]
    rows.sort(key=lambda r: r.get("clicks", 0), reverse=True)

    pages = []
    for row in rows[:limit]:
        keys = row.get("keys", [])
        pages.append({
            "url":         keys[0] if keys else "",
            "clicks":      int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })

    return {"site": site, "period": f"{days}d", "pages": pages, "status": "ok"}


def fetch_coverage(site: str, use_cache: bool = True) -> dict:
    """
    Dados de cobertura de indexação (URL Inspection API).
    Nota: o endpoint de coverage só retorna contagens, não URLs individuais.
    """
    cache_path = _cache_path(site, "coverage")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    try:
        service = _build_service()
        # Coverage via Search Console API v1
        resp = service.urlcrawlerrorstotals().list(
            siteUrl=site,
            category="notFound",
            platform="web"
        ).execute()

        result = {"site": site, "status": "ok", "raw": resp}
        _save_cache(cache_path, result)
        return result

    except Exception as e:
        # Coverage detalhada requer GSC web UI — via API é limitado
        return {
            "site":   site,
            "status": "partial",
            "note":   "Dados de cobertura completos disponíveis no GSC web. "
                      "Consulte: Search Console > Indexação > Páginas",
            "message": str(e),
        }


def fetch_sitemaps(site: str) -> dict:
    """Lista sitemaps enviados ao GSC."""
    try:
        service = _build_service()
        resp = service.sitemaps().list(siteUrl=site).execute()
        sitemaps = resp.get("sitemap", [])

        result = {
            "site":     site,
            "sitemaps": [],
            "status":   "ok",
        }

        for sm in sitemaps:
            result["sitemaps"].append({
                "path":         sm.get("path", ""),
                "last_submitted": sm.get("lastSubmitted", ""),
                "last_downloaded": sm.get("lastDownloaded", ""),
                "is_pending":   sm.get("isPending", False),
                "is_sitemaps_index": sm.get("isSitemapsIndex", False),
                "contents":     sm.get("contents", []),
                "errors":       sm.get("errors", 0),
                "warnings":     sm.get("warnings", 0),
            })

        return result

    except Exception as e:
        return {"site": site, "status": "error", "message": str(e)}


def fetch_device_breakdown(site: str, days: int = 30) -> dict:
    """Performance por dispositivo (mobile vs desktop vs tablet)."""
    data = fetch_performance(site, days, ["device"], 10)
    if data.get("status") != "ok":
        return data

    breakdown = {}
    for row in data.get("rows", []):
        device = row.get("keys", ["unknown"])[0].lower()
        breakdown[device] = {
            "clicks":      int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        }

    return {"site": site, "period": f"{days}d", "devices": breakdown, "status": "ok"}


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Google Search Console fetcher")
    parser.add_argument("--site",    required=True, help="URL da propriedade GSC (ex: https://seunegocio.com.br/)")
    parser.add_argument("--report",  default="top_queries",
                        choices=["top_queries","top_pages","opportunities","changes",
                                 "coverage","sitemaps","devices","list_sites"])
    parser.add_argument("--days",    type=int, default=30)
    parser.add_argument("--limit",   type=int, default=50)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    use_cache = not args.no_cache

    if args.report == "list_sites":
        print(json.dumps(list_sites(), ensure_ascii=False, indent=2))
    elif args.report == "top_queries":
        print(json.dumps(fetch_top_queries(args.site, args.days, args.limit), ensure_ascii=False, indent=2))
    elif args.report == "top_pages":
        print(json.dumps(fetch_top_pages(args.site, args.days, args.limit), ensure_ascii=False, indent=2))
    elif args.report == "opportunities":
        print(json.dumps(fetch_opportunity_queries(args.site, args.days), ensure_ascii=False, indent=2))
    elif args.report == "changes":
        print(json.dumps(fetch_position_changes(args.site), ensure_ascii=False, indent=2))
    elif args.report == "coverage":
        print(json.dumps(fetch_coverage(args.site, use_cache), ensure_ascii=False, indent=2))
    elif args.report == "sitemaps":
        print(json.dumps(fetch_sitemaps(args.site), ensure_ascii=False, indent=2))
    elif args.report == "devices":
        print(json.dumps(fetch_device_breakdown(args.site, args.days), ensure_ascii=False, indent=2))
