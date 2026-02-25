#!/usr/bin/env python3
"""
new_entrant_radar.py — Módulo 9
Detecta novos concorrentes que estão ranqueando para suas keywords,
com análise de risco baseada em tech stack, reviews e velocidade de crescimento.
Combina dados do GSC (suas keywords) com Tavily (quem mais está ranqueando).
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

# Score de risco baseado em sinais detectados
RISK_WEIGHTS = {
    "modern_stack":      20,   # Next.js, Nuxt, Gatsby
    "many_reviews":      15,   # > 20 reviews em pouco tempo
    "fast_ranking":      25,   # apareceu do nada nas top 20
    "funded_company":    20,   # sinais de investimento
    "strong_content":    15,   # blog ativo, conteúdo frequente
    "paid_ads_running":  10,   # Google Ads / Meta Ads ativos
    "social_active":     10,   # redes sociais ativas
}

MODERN_STACK_SIGNALS = [
    "__NEXT_DATA__", "_next/static", "nuxt", "gatsby", "svelte",
    "vercel.app", "netlify.app",
]

FUNDED_SIGNALS = [
    "série a", "série b", "rodada de investimento", "aporte",
    "captou", "levantou", "funding", "investimento",
    "backed by", "incubado", "acelerado",
]


def extract_domain(url: str) -> str:
    """Extrai domínio limpo de uma URL."""
    url = url.replace("https://","").replace("http://","").replace("www.","")
    return url.split("/")[0].split("?")[0]


def is_known_domain(domain: str, known_domains: list[str]) -> bool:
    """Verifica se o domínio já é conhecido (seu site ou concorrentes monitorados)."""
    domain_clean = domain.replace("www.","")
    known_clean = [d.replace("www.","").replace("https://","").replace("http://","") for d in known_domains]
    return any(domain_clean.endswith(k) or k.endswith(domain_clean) for k in known_clean)


def calculate_risk_score(signals: dict) -> tuple[int, str]:
    """Calcula score de risco 0-100 e label."""
    score = sum(RISK_WEIGHTS[k] for k, v in signals.items() if v and k in RISK_WEIGHTS)
    score = min(100, score)

    if score >= 60:
        label = "🔴 Alto risco — monitorar semanalmente"
    elif score >= 35:
        label = "🟡 Risco médio — monitorar mensalmente"
    else:
        label = "🟢 Baixo risco — monitorar trimestralmente"

    return score, label


def analyze_entrant(domain: str, tavily_client, keyword_context: str = "") -> dict:
    """Analisa um domínio recém-detectado para avaliar o nível de ameaça."""

    signals = {k: False for k in RISK_WEIGHTS}
    details = {}

    # 1. Buscar informações sobre o domínio
    try:
        about_results = tavily_client.search(
            f'site:{domain} OR "{domain}" sobre empresa quem somos',
            max_results=3,
            search_depth="basic",
        )
        about_text = " ".join(r.get("content","") for r in about_results.get("results",[]))

        # Sinal: investimento
        if any(s in about_text.lower() for s in FUNDED_SIGNALS):
            signals["funded_company"] = True
            details["funded_note"] = "Sinais de captação de recursos detectados"

    except Exception:
        about_text = ""

    # 2. Verificar tech stack (busca simples sem html fetch completo)
    try:
        tech_results = tavily_client.extract(urls=[f"https://{domain}"])
        html_snippet = str(tech_results)
        if any(s in html_snippet for s in MODERN_STACK_SIGNALS):
            signals["modern_stack"] = True
            details["stack_note"] = "Stack moderno detectado (Next.js / Nuxt / Vercel)"
    except Exception:
        pass

    # 3. Verificar reviews
    try:
        review_results = tavily_client.search(
            f'"{domain}" OR "{domain.replace(".com.br","").replace(".com","")}" avaliação reviews',
            max_results=3,
            search_depth="basic",
        )
        review_text = " ".join(r.get("content","") for r in review_results.get("results",[]))

        # Contar menções de reviews
        review_count_match = re.findall(r"(\d+)\s+(?:avaliações|reviews|comentários)", review_text)
        if review_count_match:
            max_reviews = max(int(x) for x in review_count_match)
            if max_reviews > 20:
                signals["many_reviews"] = True
                details["reviews_count"] = max_reviews
    except Exception:
        pass

    # 4. Verificar presença em anúncios
    try:
        ads_results = tavily_client.search(
            f'{domain} anúncio patrocinado Google Ads Meta',
            max_results=2,
            search_depth="basic",
        )
        ads_text = " ".join(r.get("content","") for r in ads_results.get("results",[]))
        if "patrocinado" in ads_text.lower() or "sponsored" in ads_text.lower():
            signals["paid_ads_running"] = True
    except Exception:
        pass

    risk_score, risk_label = calculate_risk_score(signals)

    return {
        "domain": domain,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "signals": {k: v for k, v in signals.items() if v},
        "details": details,
        "keyword_context": keyword_context,
    }


def find_new_entrants(
    your_site: str,
    keywords: list[str],
    known_competitors: list[str],
    tavily_client=None,
    gsc_client=None,
) -> dict:
    """
    Principal função: encontra novos domínios ranqueando para suas keywords.
    """
    if not tavily_client and not gsc_client:
        return {"status": "skipped", "reason": "Tavily e GSC não configurados"}

    print(f"  🚨 Radar de Entrantes: {len(keywords)} keywords monitoradas")

    all_known = [your_site] + (known_competitors or [])
    new_domains_found = {}  # domain -> list of keywords where found

    # Buscar ranqueamentos para cada keyword
    for kw in keywords[:10]:  # limite para economizar créditos
        print(f"     → '{kw}'...", end=" ", flush=True)
        try:
            results = tavily_client.search(
                kw,
                max_results=10,
                search_depth="basic",
                include_answer=False,
            )
            found_new = 0
            for r in results.get("results", []):
                domain = extract_domain(r.get("url",""))
                if domain and not is_known_domain(domain, all_known):
                    if domain not in new_domains_found:
                        new_domains_found[domain] = []
                    new_domains_found[domain].append(kw)
                    found_new += 1
            print(f"{found_new} novos domínios")
        except Exception as e:
            print(f"erro: {str(e)[:30]}")

    if not new_domains_found:
        return {
            "status": "ok",
            "new_entrants": [],
            "total_found": 0,
            "message": "Nenhum novo entrante detectado — mercado estável",
        }

    # Analisar os top entrantes (mais keywords = mais ativo)
    sorted_domains = sorted(
        new_domains_found.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:5]  # top 5

    print(f"  → Analisando {len(sorted_domains)} candidatos...")
    analyzed = []
    for domain, kws in sorted_domains:
        analysis = analyze_entrant(domain, tavily_client, ", ".join(kws[:3]))
        analysis["keywords_found_in"] = kws
        analysis["keyword_count"] = len(kws)
        analyzed.append(analysis)

    # Ordenar por risco
    analyzed.sort(key=lambda x: x["risk_score"], reverse=True)

    result = {
        "status": "ok",
        "fetched_at": datetime.now().isoformat(),
        "keywords_monitored": keywords[:10],
        "new_entrants": analyzed,
        "total_found": len(new_domains_found),
        "high_risk_count": sum(1 for a in analyzed if a["risk_score"] >= 60),
    }

    # Cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    site_clean = your_site.replace("https://","").replace("http://","").split("/")[0]
    cache_file = CACHE_DIR / f"radar-{site_clean}-{datetime.now().strftime('%Y-%m-%d')}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def to_markdown(data: dict) -> str:
    """Gera seção Markdown do Módulo 9."""
    lines = ["## MÓDULO 9 — RADAR DE NOVOS ENTRANTES", ""]

    if data.get("status") == "skipped":
        lines.append(f"status: skipped — {data.get('reason')}")
        return "\n".join(lines)

    entrants = data.get("new_entrants", [])
    total = data.get("total_found", 0)
    high_risk = data.get("high_risk_count", 0)

    if not entrants:
        lines.append("✅ Nenhum novo entrante detectado — mercado estável (fonte: Tavily)")
        return "\n".join(lines)

    lines.append(f"**{total} novos domínios detectados** | {high_risk} de alto risco (fonte: Tavily)")
    lines.append("")
    lines.append("| Domínio | Keywords | Score de Risco | Sinais Detectados |")
    lines.append("|---|---|---|---|")

    for e in entrants:
        signals_str = ", ".join(e.get("signals", {}).keys()).replace("_"," ") or "—"
        kw_count = e.get("keyword_count", 0)
        lines.append(f"| {e['domain']} | {kw_count} keyword(s) | {e['risk_score']}/100 {e['risk_label'].split('—')[0].strip()} | {signals_str} |")

    lines.append("")

    # Detalhes dos alto risco
    high_risk_entries = [e for e in entrants if e["risk_score"] >= 60]
    if high_risk_entries:
        lines.append("### ⚠️ Entrantes de Alto Risco — Detalhamento")
        lines.append("")
        for e in high_risk_entries:
            lines.append(f"**{e['domain']}** — Score {e['risk_score']}/100")
            lines.append(f"Keywords onde aparece: {', '.join(e.get('keywords_found_in',[])[:5])}")
            for k, v in e.get("details", {}).items():
                lines.append(f"→ {v}")
            lines.append(f"→ {e['risk_label']}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="New Entrant Radar — Módulo 9")
    parser.add_argument("--site", required=True, help="Seu domínio")
    parser.add_argument("--keywords", required=True, help="Keywords separadas por vírgula")
    parser.add_argument("--competitors", default="", help="Concorrentes conhecidos (vírgula)")
    args = parser.parse_args()

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    except Exception:
        client = None

    kws = [k.strip() for k in args.keywords.split(",")]
    comps = [c.strip() for c in args.competitors.split(",")] if args.competitors else []

    result = find_new_entrants(args.site, kws, comps, tavily_client=client)
    print(json.dumps(result, ensure_ascii=False, indent=2))
