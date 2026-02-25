#!/usr/bin/env python3
"""
tavily_fetcher.py
Wrapper para a Tavily API — busca e extração de conteúdo web.
Usado em todos os módulos de inteligência competitiva.
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL_SEARCH  = 86400 * 3   # 72h para buscas
CACHE_TTL_EXTRACT = 86400 * 3   # 72h para extrações


def _cache_path(mode: str, key_str: str) -> Path:
    key = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return CACHE_DIR / f"tavily-{mode}-{key}.json"


def _load_cache(path: Path, ttl: int) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(seconds=ttl):
            return data
    except Exception:
        pass
    return None


def _save_cache(path: Path, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_client():
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY não configurada.")
    from tavily import TavilyClient
    return TavilyClient(api_key=api_key)


# ──────────────────────────────────────────
# Busca
# ──────────────────────────────────────────

def search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    include_domains: list[str] = None,
    exclude_domains: list[str] = None,
    use_cache: bool = True,
) -> dict:
    """Busca na web via Tavily."""
    cache_key  = f"{query}:{max_results}:{search_depth}:{include_domains}:{exclude_domains}"
    cache_path = _cache_path("search", cache_key)

    if use_cache:
        cached = _load_cache(cache_path, CACHE_TTL_SEARCH)
        if cached:
            cached["_from_cache"] = True
            return cached

    try:
        client = _get_client()
        params = {
            "query":        query,
            "max_results":  max_results,
            "search_depth": search_depth,
            "include_raw_content": True,
        }
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains

        resp   = client.search(**params)
        result = {
            "query":   query,
            "results": resp.get("results", []),
            "status":  "ok",
        }
        _save_cache(cache_path, result)
        return result

    except Exception as e:
        return {"query": query, "status": "error", "message": str(e), "results": []}


def extract(url: str, use_cache: bool = True) -> dict:
    """Extrai conteúdo completo de uma URL via Tavily."""
    cache_path = _cache_path("extract", url)

    if use_cache:
        cached = _load_cache(cache_path, CACHE_TTL_EXTRACT)
        if cached:
            cached["_from_cache"] = True
            return cached

    try:
        client = _get_client()
        resp   = client.extract(urls=[url])
        results = resp.get("results", [])

        result = {
            "url":     url,
            "content": results[0].get("raw_content", "") if results else "",
            "status":  "ok" if results else "empty",
        }
        _save_cache(cache_path, result)
        return result

    except Exception as e:
        return {"url": url, "status": "error", "message": str(e), "content": ""}


def extract_multiple(urls: list[str], use_cache: bool = True) -> list[dict]:
    """Extrai múltiplas URLs."""
    results = []
    for url in urls:
        results.append(extract(url, use_cache))
    return results


# ──────────────────────────────────────────
# Módulos especializados
# ──────────────────────────────────────────

def search_complaints(competitor: str, use_cache: bool = True) -> dict:
    """
    Módulo 5 — Detetive de Reclamações.
    Busca reclamações e reviews negativos de um concorrente.
    """
    queries = [
        f'site:reclameaqui.com.br "{competitor}"',
        f'"{competitor}" reclamação problema ruim',
        f'"{competitor}" avaliação "não recomendo" OR "péssimo" OR "golpe"',
        f'"{competitor}" review "1 estrela" OR "2 estrelas"',
        f'site:twitter.com "{competitor}" reclamação OR problema OR decepcionante',
    ]

    all_results = []
    for q in queries:
        data = search(q, max_results=5, use_cache=use_cache)
        all_results.extend(data.get("results", []))

    # Categorizar reclamações por padrão
    categories = {
        "prazo_entrega":  ["atrasou","demorou","prazo","meses","semanas","não entregou","prometeu"],
        "suporte":        ["não responde","sumiu","impossível","sem resposta","abandonou","ignorou"],
        "qualidade":      ["mal feito","não funciona","bugado","horrível","lixo","péssimo"],
        "preco":          ["cobrou a mais","preço absurdo","cobrou sem","enganou","golpe","fraude"],
        "resultado":      ["zero resultado","não adiantou","não aparece","não gerou"],
        "transparencia":  ["escondia","não avisou","letra miúda","enganoso"],
        "pos_venda":      ["depois que pagou","sumiu","sem manutenção","abandonou"],
    }

    categorized = {cat: [] for cat in categories}
    snippets = []

    for r in all_results:
        content = (r.get("content", "") + " " + r.get("title", "")).lower()
        snippet = r.get("content", "")[:300]

        if len(snippet) > 50:
            snippets.append({
                "source": r.get("url", ""),
                "title":  r.get("title", ""),
                "snippet": snippet,
            })

        for cat, keywords in categories.items():
            if any(kw in content for kw in keywords):
                categorized[cat].append(r.get("url", ""))

    # Score de reputação inverso (mais reclamações = pior score)
    total_matches = sum(len(v) for v in categorized.values())
    reputation_score = max(0, min(100, 100 - (total_matches * 8)))

    # Top categoria
    top_category = max(categorized, key=lambda c: len(categorized[c])) if total_matches > 0 else None

    return {
        "competitor":       competitor,
        "reputation_score": reputation_score,
        "total_complaints": total_matches,
        "top_category":     top_category,
        "categories":       {k: len(v) for k, v in categorized.items()},
        "snippets":         snippets[:5],
        "status":           "ok",
    }


def search_tech_stack(url: str, use_cache: bool = True) -> dict:
    """
    Módulo 7 — Raio-X Tecnológico.
    Detecta a stack tecnológica de um site via análise de conteúdo.
    """
    content_data = extract(url, use_cache)
    content = content_data.get("content", "").lower()

    # Também busca headers via requests
    headers_data = {}
    try:
        import requests
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        headers_data = dict(r.headers)
        content += " " + r.text.lower()[:5000]
    except Exception:
        pass

    SIGNATURES = {
        # CMS / Builders (negativos para posicionamento premium)
        "wordpress":   ["wp-content","wp-includes","wordpress","wp-json"],
        "elementor":   ["elementor","et_pb_"],
        "divi":        ["et_pb_","divi"],
        "wix":         ["wix.com","wixstatic","wix-code"],
        "shopify":     ["cdn.shopify","myshopify","shopify.theme"],
        "webflow":     ["webflow.io","webflow","data-wf-"],
        "squarespace": ["squarespace.com","static1.squarespace"],
        "framer":      ["framer.com","framerusercontent"],
        "ghost":       ["ghost.io","ghost-theme"],
        "joomla":      ["joomla","option=com_"],

        # Frameworks modernos (positivos)
        "nextjs":      ["__next_data__","_next/static","next.js"],
        "nuxtjs":      ["__nuxt","_nuxt/"],
        "gatsby":      ["gatsby","___gatsby"],
        "astro":       ["astro-island","astro-root"],
        "react":       ["react","reactdom","__react"],
        "vue":         ["__vue__","vue.min.js"],
        "svelte":      ["svelte","__svelte"],
        "angular":     ["ng-version","angular"],

        # CDN / Hospedagem
        "cloudflare":  ["cf-ray","cloudflare","__cf_bm"],
        "vercel":      ["x-vercel","vercel.app"],
        "netlify":     ["netlify","x-nf-"],
        "aws":         ["amazonaws","cloudfront","x-amz"],
        "azure":       ["azurewebsites","azure"],
        "fastly":      ["x-served-by","fastly"],

        # Analytics / Marketing
        "google_ads":  ["gtag","google_conversion","adsbygoogle"],
        "meta_pixel":  ["fbq(","facebook.net/en_us/fbevents"],
        "hotjar":      ["hotjar.com","_hjsettings"],
        "rdstation":   ["rdstation","rd.js"],
        "hubspot":     ["hubspot","hs-scripts"],
        "tiktok_pixel":["tiktok","ttq."],
        "clarity":     ["microsoft clarity","clarity.ms"],
    }

    detected = {}
    for tech, signs in SIGNATURES.items():
        if any(sign in content for sign in signs):
            detected[tech] = True

    # Classificar stack
    has_legacy  = any(t in detected for t in ["wordpress","wix","squarespace","joomla"])
    has_modern  = any(t in detected for t in ["nextjs","nuxtjs","gatsby","astro","svelte"])
    has_cdn     = any(t in detected for t in ["cloudflare","vercel","netlify","fastly"])
    has_react   = any(t in detected for t in ["react","vue","angular"])

    if has_modern and has_cdn:
        classification = "🏆 Elite"
    elif has_modern or (has_react and has_cdn):
        classification = "✅ Moderna"
    elif has_legacy and has_cdn:
        classification = "🟡 Mediana"
    elif has_legacy:
        classification = "🔴 Legada"
    else:
        classification = "❓ Indeterminado"

    return {
        "url":            url,
        "detected":       detected,
        "has_legacy_cms": has_legacy,
        "has_modern_fw":  has_modern,
        "has_cdn":        has_cdn,
        "classification": classification,
        "ad_platforms":   [t for t in ["google_ads","meta_pixel","tiktok_pixel","hotjar","rdstation","hubspot"] if t in detected],
        "status":         "ok" if content else "empty",
    }


def search_lead_magnets(niche: str, competitors: list[str] = None, use_cache: bool = True) -> dict:
    """
    Módulo 6 — Espião de Iscas.
    Mapeia lead magnets oferecidos no nicho.
    """
    queries = [
        f"{niche} ebook grátis download",
        f"{niche} guia gratuito pdf",
        f"{niche} checklist template gratuito",
        f"{niche} aula gratuita masterclass",
        f"{niche} ferramenta calculadora grátis",
        f"{niche} auditoria diagnóstico gratuito",
    ]

    if competitors:
        for comp in competitors[:3]:
            queries.append(f'site:{comp} grátis OR gratuito OR download OR ebook OR template')

    magnets = []
    for q in queries:
        data = search(q, max_results=5, use_cache=use_cache)
        for r in data.get("results", []):
            title   = r.get("title", "")
            url_r   = r.get("url", "")
            content = r.get("content", "")[:200]

            magnet_type = "desconhecido"
            content_low = (title + content).lower()
            if any(w in content_low for w in ["ebook","pdf","livro"]):
                magnet_type = "ebook/pdf"
            elif any(w in content_low for w in ["checklist","lista"]):
                magnet_type = "checklist"
            elif any(w in content_low for w in ["calculadora","ferramenta","tool"]):
                magnet_type = "ferramenta"
            elif any(w in content_low for w in ["aula","masterclass","webinar","curso"]):
                magnet_type = "aula gratuita"
            elif any(w in content_low for w in ["auditoria","diagnóstico","análise"]):
                magnet_type = "auditoria/diagnóstico"
            elif any(w in content_low for w in ["template","modelo"]):
                magnet_type = "template"

            if title and url_r:
                magnets.append({
                    "title":  title,
                    "url":    url_r,
                    "type":   magnet_type,
                    "snippet": content,
                })

    # Deduplicar por URL
    seen = set()
    unique = []
    for m in magnets:
        if m["url"] not in seen:
            seen.add(m["url"])
            unique.append(m)

    return {
        "niche":   niche,
        "magnets": unique[:20],
        "status":  "ok",
    }


def search_prices(competitors: list[str], niche: str, use_cache: bool = True) -> dict:
    """
    Módulo 8 — Benchmark de Preços.
    Busca preços publicados pelos concorrentes.
    """
    results = {}
    price_pattern = re.compile(r'R\$\s*[\d.,]+', re.IGNORECASE)

    for comp in competitors:
        comp_data = {"prices_found": [], "pages_checked": [], "status": "ok"}

        # Tentar páginas típicas de preços
        price_pages = [
            f"https://{comp}/precos",
            f"https://{comp}/planos",
            f"https://{comp}/pricing",
            f"https://{comp}/servicos",
        ]

        for page_url in price_pages:
            extracted = extract(page_url, use_cache)
            if extracted.get("status") == "ok" and extracted.get("content"):
                content = extracted["content"]
                found   = price_pattern.findall(content)
                if found:
                    comp_data["prices_found"].extend(found[:10])
                    comp_data["pages_checked"].append(page_url)

        # Busca adicional se não encontrou
        if not comp_data["prices_found"]:
            search_data = search(
                f'site:{comp} preço OR plano OR R$ {niche}',
                max_results=3,
                use_cache=use_cache
            )
            for r in search_data.get("results", []):
                found = price_pattern.findall(r.get("content", ""))
                comp_data["prices_found"].extend(found[:5])

        # Limpar duplicatas e ordenar
        prices_clean = list(set(comp_data["prices_found"]))
        # Converter para float para ordenar
        def parse_price(p):
            return float(re.sub(r'[^\d,]', '', p).replace(',', '.') or 0)
        prices_clean.sort(key=parse_price)
        comp_data["prices_found"] = prices_clean[:15]

        results[comp] = comp_data

    return {"niche": niche, "competitors": results, "status": "ok"}


def search_positioning(competitor: str, use_cache: bool = True) -> dict:
    """
    Módulo 10 — Análise de Posicionamento.
    Extrai narrativa da homepage: promessa, inimigo, prova, CTA.
    """
    data = extract(f"https://{competitor}", use_cache)
    content = data.get("content", "")

    # Extrai primeiros parágrafos (onde ficam headline e proposta)
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    top_content = '\n'.join(lines[:30])

    # Busca adicional sobre o posicionamento
    search_data = search(
        f'site:{competitor} "sobre" OR "quem somos" OR "nossa missão" OR "diferencial"',
        max_results=3,
        use_cache=use_cache
    )

    return {
        "competitor":    competitor,
        "homepage_top":  top_content[:1500],
        "about_pages":   [r.get("url") for r in search_data.get("results", [])],
        "content_length": len(content),
        "status":        "ok" if content else "empty",
    }


def search_new_entrants(keywords: list[str], known_domains: list[str], use_cache: bool = True) -> dict:
    """
    Módulo 9 — Radar de Novos Entrantes.
    Detecta novos domínios ranqueando para keywords do nicho.
    """
    new_players = []
    known_set   = set(known_domains)

    for kw in keywords[:5]:  # limitar para economizar créditos
        data = search(kw, max_results=10, search_depth="basic", use_cache=use_cache)
        for r in data.get("results", []):
            url  = r.get("url", "")
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
            except Exception:
                continue

            if domain and domain not in known_set:
                new_players.append({
                    "domain":   domain,
                    "url":      url,
                    "title":    r.get("title", ""),
                    "snippet":  r.get("content", "")[:200],
                    "keyword":  kw,
                })
                known_set.add(domain)

    return {
        "keywords_checked": keywords[:5],
        "new_players":      new_players[:20],
        "status":           "ok",
    }


def search_channels(competitor: str, use_cache: bool = True) -> dict:
    """
    Módulo 11 — Mapa de Canais e Anúncios.
    Detecta em quais canais o concorrente anuncia e cria conteúdo.
    """
    # Detectar pixels via tech stack
    tech = search_tech_stack(f"https://{competitor}", use_cache)
    ad_platforms = tech.get("ad_platforms", [])

    # Verificar presença orgânica em canais
    channels = {}
    channel_queries = {
        "youtube":  f'site:youtube.com "{competitor}" OR canal',
        "instagram": f'site:instagram.com "{competitor}"',
        "linkedin": f'site:linkedin.com/company "{competitor}"',
        "tiktok":   f'site:tiktok.com "{competitor}"',
        "facebook": f'site:facebook.com "{competitor}"',
    }

    for channel, q in channel_queries.items():
        data = search(q, max_results=3, search_depth="basic", use_cache=use_cache)
        channels[channel] = len(data.get("results", [])) > 0

    # Detectar anúncios Google (presença no SERP pago)
    search_data = search(
        f'{competitor}',
        max_results=10,
        search_depth="basic",
        use_cache=use_cache
    )
    # Heurística: se aparece no topo com formato de anúncio
    channels["google_ads"] = "google_ads" in ad_platforms

    return {
        "competitor":    competitor,
        "paid_platforms": ad_platforms,
        "organic_channels": channels,
        "status":        "ok",
    }


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tavily fetcher")
    parser.add_argument("--mode", required=True,
                        choices=["search","extract","complaints","tech","magnets",
                                 "prices","positioning","radar","channels"])
    parser.add_argument("--query",       help="Query de busca")
    parser.add_argument("--url",         help="URL para extrair")
    parser.add_argument("--competitor",  help="Domínio do concorrente")
    parser.add_argument("--competitors", help="Lista de domínios separados por vírgula")
    parser.add_argument("--niche",       help="Nicho/segmento")
    parser.add_argument("--keywords",    help="Keywords separadas por vírgula")
    parser.add_argument("--known",       help="Domínios conhecidos separados por vírgula")
    parser.add_argument("--no-cache",    action="store_true")
    args = parser.parse_args()

    use_cache   = not args.no_cache
    competitors = args.competitors.split(",") if args.competitors else []
    keywords    = args.keywords.split(",")    if args.keywords    else []
    known       = args.known.split(",")       if args.known       else []

    if args.mode == "search":
        print(json.dumps(search(args.query, use_cache=use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "extract":
        print(json.dumps(extract(args.url, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "complaints":
        print(json.dumps(search_complaints(args.competitor, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "tech":
        url = args.url or f"https://{args.competitor}"
        print(json.dumps(search_tech_stack(url, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "magnets":
        print(json.dumps(search_lead_magnets(args.niche, competitors, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "prices":
        print(json.dumps(search_prices(competitors, args.niche, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "positioning":
        print(json.dumps(search_positioning(args.competitor, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "radar":
        print(json.dumps(search_new_entrants(keywords, known, use_cache), ensure_ascii=False, indent=2))
    elif args.mode == "channels":
        print(json.dumps(search_channels(args.competitor, use_cache), ensure_ascii=False, indent=2))
