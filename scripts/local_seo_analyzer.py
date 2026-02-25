#!/usr/bin/env python3
"""
local_seo_analyzer.py
Módulo 16 — Local SEO (condicional).
Analisa Google Business Profile, consistência NAP e performance em keywords locais.
"""

import os
import re
import json
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400 * 2  # 48h


def _cache_path(business: str) -> Path:
    key = hashlib.md5(business.encode()).hexdigest()[:12]
    return CACHE_DIR / f"local-seo-{key}.json"


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
# Detecção de nicho local
# ──────────────────────────────────────────

LOCAL_NICHES = [
    "médico", "dentista", "advogado", "psicólogo", "fisioterapeuta",
    "restaurante", "lanchonete", "pizzaria", "café", "bar",
    "salão", "barbearia", "clínica", "hospital", "farmácia",
    "academia", "personal", "imobiliária", "corretor", "hotel",
    "pousada", "mecânica", "auto center", "loja", "mercado",
    "supermercado", "padaria", "contabilidade", "contador", "arquiteto",
    "veterinário", "pet shop", "escola", "curso presencial",
    "dentist", "doctor", "lawyer", "restaurant", "clinic",
]

CITY_PATTERNS = re.compile(
    r'\b(em|no|na|em)\s+[A-Z][a-záéíóú]+(\s+[A-Z][a-záéíóú]+)?\b',
    re.IGNORECASE
)


def is_local_niche(keywords: list[str], niche: str = "") -> bool:
    """Detecta se o nicho é local baseado nas keywords e/ou nome do nicho."""
    combined = " ".join(keywords + [niche]).lower()

    if any(term in combined for term in LOCAL_NICHES):
        return True
    if CITY_PATTERNS.search(combined):
        return True
    return False


# ──────────────────────────────────────────
# GBP via Tavily
# ──────────────────────────────────────────

def _fetch_gbp_data(business_name: str, city: str) -> dict:
    """
    Busca dados do GBP via Tavily (sem acesso à API oficial do GBP).
    Extrai rating, reviews, horários e outras infos do snippet do Google.
    """
    from scripts.tavily_fetcher import search

    # Busca direta no Google Maps
    queries = [
        f'"{business_name}" {city} site:google.com/maps',
        f'"{business_name}" {city} avaliações Google',
        f'"{business_name}" {city} horário endereço telefone',
    ]

    gbp = {
        "exists":               None,
        "name":                 business_name,
        "city":                 city,
        "rating":               None,
        "reviews_count":        None,
        "phone_found":          None,
        "address_found":        None,
        "website_linked":       None,
        "hours_found":          None,
        "recent_posts":         None,
        "unanswered_questions": None,
        "photos_estimated":     None,
        "raw_snippets":         [],
    }

    rating_pattern  = re.compile(r'(\d[.,]\d)\s*(?:estrelas?|stars?|\()', re.IGNORECASE)
    reviews_pattern = re.compile(r'(\d[\d.]*)\s*(?:avaliações?|reviews?|opiniões?)', re.IGNORECASE)
    phone_pattern   = re.compile(r'(?:\(?\d{2}\)?\s*)?(?:9\d{4}|\d{4})[-\s]?\d{4}')

    for q in queries:
        data = search(q, max_results=5)
        for r in data.get("results", []):
            snippet = (r.get("content", "") + " " + r.get("title", "")).lower()
            gbp["raw_snippets"].append(snippet[:300])

            # Rating
            m = rating_pattern.search(snippet)
            if m and gbp["rating"] is None:
                try:
                    gbp["rating"] = float(m.group(1).replace(",", "."))
                except Exception:
                    pass

            # Reviews
            m = reviews_pattern.search(snippet)
            if m and gbp["reviews_count"] is None:
                try:
                    gbp["reviews_count"] = int(m.group(1).replace(".", ""))
                except Exception:
                    pass

            # Telefone
            if phone_pattern.search(snippet):
                gbp["phone_found"] = True

            # Endereço (heurística)
            if any(w in snippet for w in ["rua", "av.", "avenida", "nº", "número", "cep"]):
                gbp["address_found"] = True

            # Horários
            if any(w in snippet for w in ["aberto", "fecha", "horário", "segunda", "domingo"]):
                gbp["hours_found"] = True

    gbp["exists"] = gbp["rating"] is not None or gbp["phone_found"] is not None

    return gbp


# ──────────────────────────────────────────
# NAP Consistency
# ──────────────────────────────────────────

def _check_nap_consistency(business_name: str, city: str) -> dict:
    """Verifica consistência do NAP em diretórios online."""
    from scripts.tavily_fetcher import search

    directories = [
        "guiamais.com.br", "telelistas.net", "yelp.com.br",
        "foursquare.com", "tripadvisor.com.br",
    ]

    issues = []
    found_in = []

    for directory in directories:
        data = search(
            f'site:{directory} "{business_name}" {city}',
            max_results=3,
            search_depth="basic"
        )
        if data.get("results"):
            found_in.append(directory)

    return {
        "directories_found": found_in,
        "directories_checked": directories,
        "nap_issues": issues,
        "coverage_score": round(len(found_in) / len(directories) * 100),
    }


# ──────────────────────────────────────────
# Local keywords via GSC
# ──────────────────────────────────────────

def _fetch_local_keywords(site: str, city: str) -> list[dict]:
    """Busca keywords locais ranqueadas via GSC."""
    try:
        import tempfile
        import json as _json
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

        svc  = build("searchconsole", "v1", credentials=creds)
        end  = date.today() - timedelta(days=3)
        start = end - timedelta(days=30)
        body = {
            "startDate":  start.isoformat(),
            "endDate":    end.isoformat(),
            "dimensions": ["query"],
            "rowLimit":   500,
        }
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        rows = resp.get("rows", [])

        city_lower = city.lower()
        local_kws  = []
        for row in rows:
            query = row.get("keys", [""])[0].lower()
            if city_lower in query or any(
                term in query for term in LOCAL_NICHES
            ):
                local_kws.append({
                    "keyword":     query,
                    "position":    round(row.get("position", 0), 1),
                    "impressions": int(row.get("impressions", 0)),
                    "clicks":      int(row.get("clicks", 0)),
                    "ctr":         round(row.get("ctr", 0) * 100, 2),
                })

        local_kws.sort(key=lambda k: -k["impressions"])
        return local_kws[:20]

    except Exception:
        return []


# ──────────────────────────────────────────
# Competitors no Local Pack
# ──────────────────────────────────────────

def _fetch_local_pack_competitors(niche: str, city: str) -> list[dict]:
    """Detecta competidores no Local Pack para o nicho + cidade."""
    from scripts.tavily_fetcher import search

    data = search(f"{niche} {city}", max_results=10, search_depth="advanced")
    competitors = []

    rating_pattern  = re.compile(r'(\d[.,]\d)\s*(?:estrelas?|stars?)', re.IGNORECASE)
    reviews_pattern = re.compile(r'(\d[\d.]*)\s*(?:avaliações?|reviews?)', re.IGNORECASE)

    for r in data.get("results", []):
        url     = r.get("url", "")
        title   = r.get("title", "")
        content = r.get("content", "")

        # Filtrar resultados que parecem ser listagens de negócios
        if not any(d in url for d in ["google.com/maps", "yelp", "foursquare", "tripadvisor"]):
            snippet = content[:500]
            rating  = None
            reviews = None

            m = rating_pattern.search(snippet)
            if m:
                try:
                    rating = float(m.group(1).replace(",", "."))
                except Exception:
                    pass

            m = reviews_pattern.search(snippet)
            if m:
                try:
                    reviews = int(m.group(1).replace(".", ""))
                except Exception:
                    pass

            if title:
                competitors.append({
                    "name":    title[:50],
                    "url":     url,
                    "rating":  rating,
                    "reviews": reviews,
                })

    return competitors[:5]


# ──────────────────────────────────────────
# Análise completa (Módulo 16)
# ──────────────────────────────────────────

def analyze(
    business_name: str,
    city: str,
    niche: str,
    site: str = "",
    use_cache: bool = True,
) -> dict:
    cache_path = _cache_path(f"{business_name}:{city}")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    gbp         = _fetch_gbp_data(business_name, city)
    nap         = _check_nap_consistency(business_name, city)
    local_kws   = _fetch_local_keywords(site, city) if site else []
    competitors = _fetch_local_pack_competitors(niche, city)

    # Issues
    issues = []
    if not gbp.get("exists"):
        issues.append({"severity": "🔴 CRÍTICO",
                       "message": "Perfil GBP não encontrado ou sem dados",
                       "action":  "Criar/reivindicar perfil em business.google.com"})
    if gbp.get("rating") and gbp["rating"] < 4.0:
        issues.append({"severity": "🔴 CRÍTICO",
                       "message": f"Rating baixo: {gbp['rating']}/5.0",
                       "action":  "Responder reviews negativos e solicitar mais reviews positivos"})
    if not gbp.get("hours_found"):
        issues.append({"severity": "🟡 ALTO",
                       "message": "Horários de funcionamento não encontrados no GBP",
                       "action":  "Atualizar horários no perfil GBP"})
    if nap["coverage_score"] < 50:
        issues.append({"severity": "🟢 MÉDIO",
                       "message": f"NAP em apenas {nap['coverage_score']}% dos diretórios verificados",
                       "action":  "Cadastrar em mais diretórios locais com NAP consistente"})

    # Score local
    score = 100
    for issue in issues:
        if "CRÍTICO" in issue["severity"]:
            score -= 25
        elif "ALTO" in issue["severity"]:
            score -= 12
        elif "MÉDIO" in issue["severity"]:
            score -= 6
    score = max(0, score)

    result = {
        "business_name": business_name,
        "city":          city,
        "niche":         niche,
        "local_score":   score,
        "gbp":           gbp,
        "nap":           nap,
        "local_keywords": local_kws,
        "local_competitors": competitors,
        "issues":        issues,
        "status":        "ok",
    }
    _save_cache(cache_path, result)
    return result


def to_markdown(data: dict) -> str:
    score    = data.get("local_score", 0)
    business = data.get("business_name", "")
    city     = data.get("city", "")
    lines    = ["## MÓDULO 16 — LOCAL SEO", "",
                f"### Score Local: {score}/100 | {business} — {city}", ""]

    issues = data.get("issues", [])
    if issues:
        lines += ["### Issues Identificados", ""]
        for issue in issues:
            lines.append(f"{issue['severity']} — {issue['message']}")
            lines.append(f"  → Ação: {issue['action']}")
        lines.append("")

    gbp = data.get("gbp", {})
    lines += ["### Google Business Profile (fonte: Tavily)", "",
              "| Item | Status |",
              "|---|---|",
              f"| Perfil encontrado | {'✅ Sim' if gbp.get('exists') else '🔴 Não encontrado'} |",
              f"| Rating | {gbp.get('rating', 'N/D')}/5.0 {'✅' if (gbp.get('rating') or 0) >= 4.3 else '⚠️' if (gbp.get('rating') or 0) >= 3.8 else '🔴'} |",
              f"| Total Reviews | {gbp.get('reviews_count', 'N/D')} |",
              f"| Telefone | {'✅ Encontrado' if gbp.get('phone_found') else '❌ Não encontrado'} |",
              f"| Endereço | {'✅ Encontrado' if gbp.get('address_found') else '❌ Não encontrado'} |",
              f"| Horários | {'✅ Encontrados' if gbp.get('hours_found') else '⚠️ Não encontrados'} |",
              ""]

    local_kws = data.get("local_keywords", [])
    if local_kws:
        lines += ["### Keywords Locais (fonte: GSC)", "",
                  "| Keyword | Posição | Impressões/mês | CTR |",
                  "|---|---|---|---|"]
        for kw in local_kws[:8]:
            lines.append(
                f"| {kw['keyword']} | {kw['position']} | "
                f"{kw['impressions']} | {kw['ctr']}% |"
            )
        lines.append("")

    competitors = data.get("local_competitors", [])
    if competitors:
        lines += ["### Concorrentes no Local Pack (fonte: Tavily)", "",
                  "| Nome | Rating | Reviews |",
                  "|---|---|---|"]
        for c in competitors[:5]:
            lines.append(
                f"| {c['name'][:40]} | "
                f"{c['rating'] or 'N/D'} | "
                f"{c['reviews'] or 'N/D'} |"
            )
        lines.append("")

    nap = data.get("nap", {})
    lines += [
        "### Presença em Diretórios (NAP)", "",
        f"Cobertura: {nap.get('coverage_score', 0)}% ({len(nap.get('directories_found', []))}/{len(nap.get('directories_checked', []))} diretórios)",
        "",
    ]
    if nap.get("directories_found"):
        lines.append(f"✅ Encontrado em: {', '.join(nap['directories_found'])}")
    not_found = [d for d in nap.get("directories_checked", [])
                 if d not in nap.get("directories_found", [])]
    if not_found:
        lines.append(f"❌ Ausente em: {', '.join(not_found)}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local SEO Analyzer")
    parser.add_argument("--business-name", required=True)
    parser.add_argument("--city",          required=True)
    parser.add_argument("--niche",         required=True)
    parser.add_argument("--site",          default="")
    parser.add_argument("--no-cache",      action="store_true")
    parser.add_argument("--md",            action="store_true")
    args = parser.parse_args()

    data = analyze(
        args.business_name, args.city, args.niche,
        args.site, use_cache=not args.no_cache
    )
    print(to_markdown(data) if args.md else json.dumps(data, ensure_ascii=False, indent=2))
