#!/usr/bin/env python3
"""
content_health.py
Módulo 15 — Saúde do Conteúdo.
Detecta: content decay, canibalização de keywords, thin content e topical gaps.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400  # 24h


def _cache_path(site: str, report: str) -> Path:
    key = hashlib.md5(f"{site}:{report}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"content-{key}.json"


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


def _build_gsc_service():
    from scripts.gsc_fetcher import _build_service
    return _build_service()


# ──────────────────────────────────────────
# 15a — Content Decay
# ──────────────────────────────────────────

def detect_decay(site: str, use_cache: bool = True) -> dict:
    """
    Compara 3 períodos de 28d para detectar queda contínua de tráfego por página.
    Queda contínua em 2+ períodos = decay confirmado.
    """
    cache_path = _cache_path(site, "decay")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    def fetch_period(days_ago_start: int) -> dict:
        end   = date.today() - timedelta(days=days_ago_start + 3)
        start = end - timedelta(days=28)
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            import tempfile, json as _json

            cred_env = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
            SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
            if os.path.isfile(cred_env):
                creds = service_account.Credentials.from_service_account_file(cred_env, scopes=SCOPES)
            else:
                cred_dict = _json.loads(cred_env)
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                _json.dump(cred_dict, tmp); tmp.close()
                creds = service_account.Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

            svc = build("searchconsole", "v1", credentials=creds)
            body = {
                "startDate":  start.isoformat(),
                "endDate":    end.isoformat(),
                "dimensions": ["page"],
                "rowLimit":   1000,
            }
            resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
            return {r["keys"][0]: int(r.get("clicks", 0)) for r in resp.get("rows", [])}
        except Exception as e:
            return {}

    p3 = fetch_period(56)   # mais antigo
    p2 = fetch_period(28)
    p1 = fetch_period(0)    # mais recente

    decaying = []
    for url in p1:
        c1 = p1.get(url, 0)
        c2 = p2.get(url, 0)
        c3 = p3.get(url, 0)

        if c3 == 0 or c2 == 0:
            continue

        # Queda contínua: p3 > p2 > p1 com queda > 20% no total
        if c3 > c2 > c1 and c3 > 0:
            total_drop = round((c3 - c1) / c3 * 100, 1)
            if total_drop >= 20 and c3 >= 30:  # mínimo 30 clicks no pico
                # Causa provável heurística
                if total_drop >= 60:
                    cause = "Fortemente superado por concorrentes ou conteúdo desatualizado"
                elif total_drop >= 40:
                    cause = "Provável desatualização ou canibalização"
                else:
                    cause = "Queda gradual — monitorar"

                decaying.append({
                    "url":            url,
                    "clicks_p3":      c3,
                    "clicks_p2":      c2,
                    "clicks_p1":      c1,
                    "drop_pct":       total_drop,
                    "cause_probable": cause,
                    "priority":       "🔴 CRÍTICO" if total_drop >= 50 else "🟡 ALTO",
                })

    decaying.sort(key=lambda x: -x["drop_pct"])

    result = {
        "site":          site,
        "pages_in_decay": decaying[:20],
        "total_decay":   len(decaying),
        "status":        "ok",
    }
    _save_cache(cache_path, result)
    return result


# ──────────────────────────────────────────
# 15b — Canibalização
# ──────────────────────────────────────────

def detect_cannibalization(site: str, use_cache: bool = True) -> dict:
    """
    Detecta múltiplas URLs ranqueando para a mesma keyword.
    Canibalização = 2+ páginas com posição <= 30 para mesma query.
    """
    cache_path = _cache_path(site, "cannibalization")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    try:
        import tempfile, json as _json
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        cred_env = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
        SCOPES   = ["https://www.googleapis.com/auth/webmasters.readonly"]
        if os.path.isfile(cred_env):
            creds = service_account.Credentials.from_service_account_file(cred_env, scopes=SCOPES)
        else:
            cred_dict = _json.loads(cred_env)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _json.dump(cred_dict, tmp); tmp.close()
            creds = service_account.Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

        svc = build("searchconsole", "v1", credentials=creds)
        end   = date.today() - timedelta(days=3)
        start = end - timedelta(days=30)
        body = {
            "startDate":  start.isoformat(),
            "endDate":    end.isoformat(),
            "dimensions": ["query", "page"],
            "rowLimit":   5000,
        }
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        rows = resp.get("rows", [])

    except Exception as e:
        return {"site": site, "status": "error", "message": str(e), "groups": []}

    # Agrupar por query
    query_map = defaultdict(list)
    for row in rows:
        keys     = row.get("keys", [])
        if len(keys) < 2:
            continue
        query, page = keys[0], keys[1]
        position    = row.get("position", 100)
        clicks      = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))

        if position <= 30 and impressions >= 10:
            query_map[query].append({
                "url":         page,
                "position":    round(position, 1),
                "clicks":      clicks,
                "impressions": impressions,
            })

    # Filtrar grupos com canibalização (2+ páginas)
    cannibal_groups = []
    for query, pages in query_map.items():
        if len(pages) >= 2:
            pages.sort(key=lambda p: p["position"])
            total_clicks = sum(p["clicks"] for p in pages)

            # Ação sugerida
            if len(pages) >= 3:
                action = "Consolidar: redirecionar páginas secundárias para a principal"
            else:
                action = "Diferenciar intenção ou consolidar com redirect 301"

            cannibal_groups.append({
                "keyword": query,
                "pages":   pages,
                "total_clicks": total_clicks,
                "action":  action,
            })

    cannibal_groups.sort(key=lambda g: -g["total_clicks"])

    result = {
        "site":             site,
        "groups":           cannibal_groups[:20],
        "total_groups":     len(cannibal_groups),
        "status":           "ok",
    }
    _save_cache(cache_path, result)
    return result


# ──────────────────────────────────────────
# 15c — Thin Content
# ──────────────────────────────────────────

def detect_thin_content(site: str, use_cache: bool = True) -> dict:
    """
    Identifica páginas indexadas com pouco conteúdo.
    Usa GSC para encontrar URLs com impressões e amostragem via requests.
    """
    cache_path = _cache_path(site, "thin")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    import requests
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "nav", "footer", "header"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style", "nav", "footer", "header"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                stripped = data.strip()
                if stripped:
                    self.text.append(stripped)

        def word_count(self) -> int:
            return len(" ".join(self.text).split())

    # Buscar páginas via GSC
    thin_pages = []
    try:
        import tempfile, json as _json
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        cred_env = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
        SCOPES   = ["https://www.googleapis.com/auth/webmasters.readonly"]
        if os.path.isfile(cred_env):
            creds = service_account.Credentials.from_service_account_file(cred_env, scopes=SCOPES)
        else:
            cred_dict = _json.loads(cred_env)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _json.dump(cred_dict, tmp); tmp.close()
            creds = service_account.Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

        svc = build("searchconsole", "v1", credentials=creds)
        end   = date.today() - timedelta(days=3)
        start = end - timedelta(days=30)
        body  = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                 "dimensions": ["page"], "rowLimit": 200}
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        pages = [
            {"url": r["keys"][0], "impressions": int(r.get("impressions", 0))}
            for r in resp.get("rows", [])
        ]
    except Exception:
        pages = []

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOIntelBot/1.0)"}

    for page in pages[:80]:  # analisar até 80 páginas
        url = page["url"]
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code != 200:
                continue
            extractor = TextExtractor()
            extractor.feed(r.text[:100000])
            word_count = extractor.word_count()

            if word_count < 300:
                if word_count < 100:
                    action = "noindex ou consolidar"
                    sev    = "🟡 ALTO"
                else:
                    action = "expandir conteúdo (mínimo 600 palavras)"
                    sev    = "🟢 MÉDIO"

                thin_pages.append({
                    "url":         url,
                    "word_count":  word_count,
                    "impressions": page["impressions"],
                    "action":      action,
                    "severity":    sev,
                })
        except Exception:
            continue

    thin_pages.sort(key=lambda p: -p["impressions"])

    result = {
        "site":       site,
        "thin_pages": thin_pages[:20],
        "total_thin": len(thin_pages),
        "status":     "ok",
    }
    _save_cache(cache_path, result)
    return result


# ──────────────────────────────────────────
# 15d — Topical Authority Map
# ──────────────────────────────────────────

def build_topical_map(site: str, niche: str, competitors: list[str] = None,
                      use_cache: bool = True) -> dict:
    """
    Mapeia subtópicos do nicho que você cobre vs concorrentes.
    Usa Tavily para mapear o nicho + GSC para verificar cobertura.
    """
    cache_path = _cache_path(site, f"topical-{niche}")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    from scripts.tavily_fetcher import search

    # Descobrir subtópicos via busca
    subtopics_raw = []
    queries = [
        f"{niche} guia completo tópicos",
        f"o que saber sobre {niche}",
        f"{niche} perguntas frequentes",
    ]
    for q in queries:
        data = search(q, max_results=5, use_cache=use_cache)
        for r in data.get("results", []):
            content = r.get("content", "")
            # Extrair possíveis subtópicos de headings/bullets no conteúdo
            import re
            headings = re.findall(r'(?:^|\n)#{1,3}\s+(.+)', content)
            subtopics_raw.extend(h.strip() for h in headings if len(h.strip()) > 5)

    # Deduplicar e limitar
    seen = set()
    subtopics = []
    for st in subtopics_raw:
        key = st.lower()[:40]
        if key not in seen and len(subtopics) < 15:
            seen.add(key)
            subtopics.append(st)

    # Verificar cobertura do site (via GSC)
    your_queries = set()
    try:
        import tempfile, json as _json
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        cred_env = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
        SCOPES   = ["https://www.googleapis.com/auth/webmasters.readonly"]
        if os.path.isfile(cred_env):
            creds = service_account.Credentials.from_service_account_file(cred_env, scopes=SCOPES)
        else:
            cred_dict = _json.loads(cred_env)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            _json.dump(cred_dict, tmp); tmp.close()
            creds = service_account.Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

        svc = build("searchconsole", "v1", credentials=creds)
        end   = date.today() - timedelta(days=3)
        start = end - timedelta(days=90)
        body  = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                 "dimensions": ["query"], "rowLimit": 1000}
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        your_queries = {r["keys"][0].lower() for r in resp.get("rows", [])}
    except Exception:
        pass

    # Construir mapa
    topical_map = []
    for st in subtopics:
        st_lower = st.lower()
        words    = set(st_lower.split())

        # Verificar cobertura sua
        coverage_your = "❌ Ausente"
        for q in your_queries:
            if len(words & set(q.split())) >= 2:
                coverage_your = "✅ Forte"
                break
        if coverage_your == "❌ Ausente":
            for q in your_queries:
                if any(w in q for w in words if len(w) > 4):
                    coverage_your = "⚠️ Fraco"
                    break

        # Verificar cobertura dos concorrentes (via Tavily)
        coverage_rivals = {}
        if competitors:
            for comp in competitors[:3]:
                comp_data = search(
                    f'site:{comp} {st}',
                    max_results=3,
                    search_depth="basic",
                    use_cache=use_cache
                )
                coverage_rivals[comp] = "✅ Forte" if comp_data.get("results") else "❌ Ausente"

        # Prioridade
        if coverage_your == "❌ Ausente":
            if all(v == "❌ Ausente" for v in coverage_rivals.values()):
                priority = "🏆 Primeiro a cobrir"
            else:
                priority = "🔴 Urgente"
        elif coverage_your == "⚠️ Fraco":
            priority = "🟡 Melhorar"
        else:
            priority = "🟢 Manter"

        topical_map.append({
            "subtopic":       st,
            "your_coverage":  coverage_your,
            "rival_coverage": coverage_rivals,
            "priority":       priority,
        })

    result = {
        "site":         site,
        "niche":        niche,
        "topical_map":  topical_map,
        "status":       "ok",
    }
    _save_cache(cache_path, result)
    return result


# ──────────────────────────────────────────
# Análise completa (Módulo 15)
# ──────────────────────────────────────────

def full_analysis(site: str, niche: str = "", competitors: list[str] = None,
                  use_cache: bool = True) -> dict:
    decay   = detect_decay(site, use_cache)
    cannibal = detect_cannibalization(site, use_cache)
    thin    = detect_thin_content(site, use_cache)

    topical = {}
    if niche:
        topical = build_topical_map(site, niche, competitors, use_cache)

    # Score de saúde
    decay_penalty   = min(40, len(decay.get("pages_in_decay", [])) * 4)
    cannibal_penalty = min(30, len(cannibal.get("groups", [])) * 5)
    thin_penalty    = min(20, len(thin.get("thin_pages", [])) * 2)
    score = max(0, 100 - decay_penalty - cannibal_penalty - thin_penalty)

    return {
        "site":           site,
        "health_score":   score,
        "decay":          decay,
        "cannibalization": cannibal,
        "thin_content":   thin,
        "topical_map":    topical,
        "status":         "ok",
    }


def to_markdown(data: dict) -> str:
    score = data.get("health_score", 0)
    lines = ["## MÓDULO 15 — SAÚDE DO CONTEÚDO", "",
             f"### Score de Saúde: {score}/100", ""]

    # Decay
    decay_pages = data.get("decay", {}).get("pages_in_decay", [])
    if decay_pages:
        lines += [
            "### Content Decay — Páginas em Queda (fonte: GSC)", "",
            "| URL | Clicks (antigo) | Clicks (recente) | Queda | Causa Provável |",
            "|---|---|---|---|---|",
        ]
        for p in decay_pages[:8]:
            lines.append(
                f"| {p['url'][:55]} | {p['clicks_p3']} | {p['clicks_p1']} | "
                f"-{p['drop_pct']}% {p['priority']} | {p['cause_probable'][:50]} |"
            )
        lines.append("")
    else:
        lines += ["### Content Decay", "", "✅ Nenhuma página em queda contínua detectada.", ""]

    # Canibalização
    groups = data.get("cannibalization", {}).get("groups", [])
    if groups:
        lines += ["### Canibalização de Keywords (fonte: GSC)", ""]
        for g in groups[:5]:
            lines.append(f"🔴 CRÍTICO — \"{g['keyword']}\" ({len(g['pages'])} páginas competindo)")
            for p in g["pages"]:
                lines.append(f"  → {p['url'][:60]} — pos. {p['position']}, {p['clicks']} clicks")
            lines.append(f"  **Ação:** {g['action']}")
            lines.append("")
    else:
        lines += ["### Canibalização de Keywords", "", "✅ Nenhuma canibalização significativa detectada.", ""]

    # Thin content
    thin_pages = data.get("thin_content", {}).get("thin_pages", [])
    if thin_pages:
        lines += [
            "### Thin Content — Páginas com Conteúdo Insuficiente", "",
            "| URL | Palavras Est. | Impressões/mês | Ação |",
            "|---|---|---|---|",
        ]
        for p in thin_pages[:10]:
            lines.append(
                f"| {p['url'][:55]} | {p['word_count']} | "
                f"{p['impressions']} | {p['severity']} {p['action']} |"
            )
        lines.append("")
    else:
        lines += ["### Thin Content", "", "✅ Nenhuma página thin crítica detectada.", ""]

    # Topical map
    topical = data.get("topical_map", {})
    topical_items = topical.get("topical_map", [])
    if topical_items:
        niche = topical.get("niche", "")
        lines += [f"### Topical Authority Map — {niche}", "",
                  "| Subtópico | Você | Prioridade |",
                  "|---|---|---|"]
        for item in topical_items:
            rivals = " | ".join(
                f"{comp}: {cov}"
                for comp, cov in item.get("rival_coverage", {}).items()
            )
            lines.append(
                f"| {item['subtopic'][:45]} | {item['your_coverage']} | {item['priority']} |"
            )
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Content Health Analyzer")
    parser.add_argument("--site",        required=True)
    parser.add_argument("--niche",       default="")
    parser.add_argument("--competitors", default="", help="Domínios separados por vírgula")
    parser.add_argument("--report",      default="full",
                        choices=["full","decay","cannibalization","thin","topical"])
    parser.add_argument("--no-cache",    action="store_true")
    parser.add_argument("--md",          action="store_true")
    args = parser.parse_args()

    use_cache   = not args.no_cache
    competitors = args.competitors.split(",") if args.competitors else []

    if args.report == "full":
        data = full_analysis(args.site, args.niche, competitors, use_cache)
        print(to_markdown(data) if args.md else json.dumps(data, ensure_ascii=False, indent=2))
    elif args.report == "decay":
        print(json.dumps(detect_decay(args.site, use_cache), ensure_ascii=False, indent=2))
    elif args.report == "cannibalization":
        print(json.dumps(detect_cannibalization(args.site, use_cache), ensure_ascii=False, indent=2))
    elif args.report == "thin":
        print(json.dumps(detect_thin_content(args.site, use_cache), ensure_ascii=False, indent=2))
    elif args.report == "topical":
        print(json.dumps(build_topical_map(args.site, args.niche, competitors, use_cache), ensure_ascii=False, indent=2))
