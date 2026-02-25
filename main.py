#!/usr/bin/env python3
"""
main.py
Orquestrador principal da skill seo-aeo-geo-intel.
Detecta modo, verifica integrações, executa módulos e gera relatório Markdown.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Adicionar scripts ao path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

OUTPUT_DIR = Path(os.getenv("SEO_SKILL_OUTPUT_DIR", "./reports"))
CACHE_DIR  = Path(os.getenv("SEO_SKILL_CACHE_DIR",  "./cache"))


# ──────────────────────────────────────────
# Verificação de integrações
# ──────────────────────────────────────────

def check_integrations(verbose: bool = True) -> dict:
    status = {
        "tavily":    bool(os.getenv("TAVILY_API_KEY")),
        "gsc":       bool(os.getenv("GSC_SERVICE_ACCOUNT_JSON") or os.getenv("GSC_OAUTH_TOKEN")),
        "pagespeed": bool(os.getenv("PAGESPEED_API_KEY")),
        "ahrefs":    bool(os.getenv("AHREFS_API_KEY")),
        "semrush":   bool(os.getenv("SEMRUSH_API_KEY")),
    }

    if verbose:
        print("\n🔧 Verificando integrações...")
        icons = {True: "✅", False: "❌"}
        opt   = {True: "✅", False: "⏭️  [opcional]"}
        print(f"  {icons[status['tavily']]}  Tavily API")
        print(f"  {icons[status['gsc']]}  Google Search Console")
        print(f"  {'✅' if status['pagespeed'] else '⚠️  [recomendada]'}  PageSpeed Insights API")
        print(f"  {opt[status['ahrefs']]}  Ahrefs API")
        print(f"  {opt[status['semrush']]}  Semrush API")

    return status


def active_modules(integrations: dict, mode: str, local_niche: bool = False) -> tuple[list, list]:
    """Retorna (módulos_ativos, módulos_pulados) baseado nas integrações e modo."""
    tavily = integrations["tavily"]
    gsc    = integrations["gsc"]
    psi    = integrations["pagespeed"]
    backlinks = integrations["ahrefs"] or integrations["semrush"]

    all_modules = list(range(1, 17))

    skipped = []
    reasons = {}

    # Dependências de cada módulo
    deps = {
        1:  {"requires": gsc or tavily,  "reason": "GSC e Tavily ausentes"},
        2:  {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        3:  {"requires": gsc,             "reason": "GSC_SERVICE_ACCOUNT_JSON não configurado"},
        4:  {"requires": True,            "reason": ""},
        5:  {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        6:  {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        7:  {"requires": tavily or psi,   "reason": "Tavily e PageSpeed ausentes"},
        8:  {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        9:  {"requires": tavily or gsc,   "reason": "Tavily e GSC ausentes"},
        10: {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        11: {"requires": tavily,          "reason": "TAVILY_API_KEY não configurada"},
        12: {"requires": True,            "reason": ""},   # crawl funciona sem APIs externas
        13: {"requires": True,            "reason": ""},   # crawl funciona sem APIs externas
        14: {"requires": backlinks,       "reason": "AHREFS_API_KEY e SEMRUSH_API_KEY não configuradas"},
        15: {"requires": gsc or tavily,   "reason": "GSC e Tavily ausentes"},
        16: {"requires": local_niche,     "reason": "Nicho não-local detectado"},
    }

    # Módulos por modo
    mode_modules = {
        "full":        list(range(1, 17)),
        "delta":       [3, 4, 9, 15],
        "competitor":  [2, 5, 6, 7, 8, 10, 11],
        "keywords":    [3, 4, 15],
        "performance": [7, 12],
        "technical":   [12, 13],
        "local":       [16],
        "backlinks":   [14],
        "sentiment":   [5],
        "pricing":     [8],
        "radar":       [9],
    }

    relevant = mode_modules.get(mode, list(range(1, 17)))

    active  = []
    skipped = []

    for m in relevant:
        dep = deps.get(m, {"requires": True, "reason": ""})
        if dep["requires"]:
            active.append(m)
        else:
            skipped.append({"id": m, "reason": dep["reason"]})

    return active, skipped


# ──────────────────────────────────────────
# Módulos de execução
# ──────────────────────────────────────────

def run_pagespeed(url: str, competitors: list[str] = None,
                  use_cache: bool = True) -> dict:
    try:
        from scripts.pagespeed_fetcher import fetch_both, fetch
        data = {"your_site": fetch_both(url, use_cache)}
        if competitors:
            data["competitors"] = {}
            for comp in competitors[:3]:
                comp_url = f"https://{comp}" if not comp.startswith("http") else comp
                data["competitors"][comp] = fetch(comp_url, "mobile", use_cache)
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_gsc(site: str, days: int = 30, use_cache: bool = True) -> dict:
    try:
        from scripts.gsc_fetcher import (
            fetch_top_queries, fetch_top_pages,
            fetch_opportunity_queries, fetch_position_changes,
            fetch_sitemaps, fetch_device_breakdown
        )
        return {
            "top_queries":   fetch_top_queries(site, days, use_cache=use_cache)["queries"]
                             if fetch_top_queries(site, days, use_cache=use_cache).get("status") == "ok"
                             else [],
            "top_pages":     fetch_top_pages(site, days, use_cache=use_cache),
            "opportunities": fetch_opportunity_queries(site, days, use_cache),
            "changes":       fetch_position_changes(site),
            "sitemaps":      fetch_sitemaps(site),
            "devices":       fetch_device_breakdown(site, days, use_cache),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_tech_stack(competitors: list[str], pagespeed_data: dict = None,
                   use_cache: bool = True) -> dict:
    try:
        from scripts.tavily_fetcher import search_tech_stack

        result = {}
        for comp in competitors:
            url = f"https://{comp}" if not comp.startswith("http") else comp
            tech = search_tech_stack(url, use_cache)

            # Adicionar PageSpeed score se disponível
            if pagespeed_data and "competitors" in pagespeed_data:
                comp_ps = pagespeed_data["competitors"].get(comp, {})
                mobile_score = comp_ps.get("scores", {}).get("performance")
                if mobile_score:
                    tech["pagespeed_mobile"] = f"{mobile_score}/100"

            result[comp] = tech
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_complaints(competitors: list[str], use_cache: bool = True) -> dict:
    try:
        from scripts.tavily_fetcher import search_complaints
        return {comp: search_complaints(comp, use_cache) for comp in competitors}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_prices(competitors: list[str], niche: str, use_cache: bool = True) -> dict:
    try:
        from scripts.tavily_fetcher import search_prices
        return search_prices(competitors, niche, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_technical(site: str, use_cache: bool = True) -> dict:
    try:
        from scripts.crawl_analyzer import full_analysis
        return full_analysis(site, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_internal_links(site: str, gsc_pages: list[str] = None,
                       use_cache: bool = True) -> dict:
    try:
        from scripts.internal_link_analyzer import analyze
        return analyze(site, gsc_pages, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_content_health(site: str, niche: str = "", competitors: list[str] = None,
                       use_cache: bool = True) -> dict:
    try:
        from scripts.content_health import full_analysis
        return full_analysis(site, niche, competitors or [], use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_backlinks(site: str, competitors: list[str] = None,
                  use_cache: bool = True) -> dict:
    try:
        from scripts.backlink_fetcher import fetch
        return fetch(site, competitors, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_local_seo(business_name: str, city: str, niche: str,
                  site: str = "", use_cache: bool = True) -> dict:
    try:
        from scripts.local_seo_analyzer import analyze
        return analyze(business_name, city, niche, site, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_radar(keywords: list[str], known_domains: list[str],
              use_cache: bool = True) -> dict:
    try:
        from scripts.tavily_fetcher import search_new_entrants
        return search_new_entrants(keywords, known_domains, use_cache)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────
# Orquestrador principal
# ──────────────────────────────────────────

def run(
    site: str,
    mode: str = "full",
    competitors: list[str] = None,
    niche: str = "",
    days: int = 30,
    business_name: str = "",
    city: str = "",
    use_cache: bool = True,
    output_path: str = "",
) -> str:
    """
    Executa a skill completa e retorna o relatório em Markdown.
    """
    start_time  = time.time()
    competitors = competitors or []

    print(f"\n🚀 seo-aeo-geo-intel v2.2 — Modo: {mode.upper()}")
    print(f"   Site: {site}")
    if competitors:
        print(f"   Concorrentes: {', '.join(competitors)}")

    # ── Verificar integrações
    integrations = check_integrations(verbose=True)

    # ── Detectar nicho local
    from scripts.local_seo_analyzer import is_local_niche
    local_niche = (
        os.getenv("SEO_SKILL_LOCAL_SEO", "auto") == "on" or
        (os.getenv("SEO_SKILL_LOCAL_SEO", "auto") == "auto" and is_local_niche([], niche))
    )

    # ── Módulos ativos
    active, skipped = active_modules(integrations, mode, local_niche)
    print(f"\n📊 Módulos ativos: {active}")
    if skipped:
        print(f"   Pulados: {[s['id'] for s in skipped]}")

    # ── Coletar dados
    ctx = {
        "site":               site,
        "mode":               mode,
        "start_date":         (date.today() - timedelta(days=days)).isoformat(),
        "end_date":           date.today().isoformat(),
        "modules_executed":   active,
        "modules_skipped":    skipped,
        "competitors_analyzed": competitors,
        "warnings":           [],
        "data_sources":       {},
    }

    # PageSpeed
    if integrations["pagespeed"] and (1 in active or 7 in active or 12 in active):
        print("\n⚡ Coletando PageSpeed Insights...")
        ps_url = f"https://{site}" if not site.startswith("http") else site
        ctx["pagespeed_data"] = run_pagespeed(ps_url, competitors, use_cache)
        ctx["data_sources"]["pagespeed"] = {"status": "ok"}

    # GSC
    if integrations["gsc"] and any(m in active for m in [1, 3, 9, 13, 15]):
        print("\n📊 Coletando Google Search Console...")
        gsc_site = site if site.startswith("http") else f"https://{site}/"
        gsc_data = run_gsc(gsc_site, days, use_cache)
        ctx["gsc_data"] = gsc_data
        ctx["data_sources"]["gsc"] = {"status": "ok", "days": days}

        # Top pages para análise de links internos
        top_pages = gsc_data.get("top_pages", {}).get("pages", [])
        ctx["gsc_top_pages"] = [p["url"] for p in top_pages]

    # Análise de Tech Stack
    if 7 in active and competitors:
        print("\n🔬 Detectando tech stack dos concorrentes...")
        ctx["tech_data"] = run_tech_stack(
            competitors,
            ctx.get("pagespeed_data", {}),
            use_cache
        )

    # Reclamações
    if 5 in active and competitors:
        print("\n🕵️ Investigando reclamações...")
        ctx["complaints_data"] = run_complaints(competitors, use_cache)

    # Preços
    if 8 in active and competitors and niche:
        print("\n💰 Coletando benchmark de preços...")
        ctx["prices_data"] = run_prices(competitors, niche, use_cache)

    # SEO Técnico
    if 12 in active:
        print("\n🔬 Analisando SEO técnico...")
        tech_data = run_technical(site, use_cache)
        ctx["technical_data"] = tech_data
        all_issues = tech_data.get("all_issues", [])
        ctx.setdefault("all_issues", []).extend(all_issues)

    # Links Internos
    if 13 in active:
        print("\n🕸️ Analisando links internos...")
        ctx["internal_links_data"] = run_internal_links(
            site,
            ctx.get("gsc_top_pages", []),
            use_cache
        )

    # Saúde do Conteúdo
    if 15 in active:
        print("\n📉 Analisando saúde do conteúdo...")
        ctx["content_health_data"] = run_content_health(site, niche, competitors, use_cache)

    # Backlinks
    if 14 in active:
        print("\n🔗 Coletando backlinks...")
        ctx["backlinks_data"] = run_backlinks(site, competitors, use_cache)

    # Local SEO
    if 16 in active and business_name and city:
        print("\n📍 Analisando Local SEO...")
        ctx["local_seo_data"] = run_local_seo(
            business_name, city, niche, site, use_cache
        )

    # Radar de novos entrantes
    if 9 in active:
        print("\n🚨 Verificando novos entrantes...")
        top_queries = ctx.get("gsc_data", {}).get("opportunities", {}).get("opportunity_zone", [])
        keywords = [q["query"] for q in top_queries[:5]]
        if keywords:
            ctx["radar_data"] = run_radar(keywords, competitors, use_cache)

    # Calcular scores
    ctx["scores"] = _compute_scores(ctx)

    # Resumo executivo
    ctx["main_opportunity"] = _detect_main_opportunity(ctx)
    ctx["main_alert"]       = _detect_main_alert(ctx)
    ctx["priority_action"]  = _detect_priority_action(ctx)

    # Tempo de execução
    ctx["duration_seconds"] = round(time.time() - start_time)

    # ── Gerar relatório Markdown
    print(f"\n📝 Gerando relatório Markdown...")
    from scripts.output.markdown_builder import build

    out_path = Path(output_path) if output_path else None
    report   = build(ctx, out_path)

    # Salvar baseline para modo delta
    if mode == "full":
        _save_baseline(site, ctx)

    print(f"\n✅ Concluído em {ctx['duration_seconds']}s")
    return report


# ──────────────────────────────────────────
# Helpers de análise
# ──────────────────────────────────────────

def _compute_scores(ctx: dict) -> dict:
    scores = {}

    # SEO score: baseado em posição média e issues técnicos
    gsc = ctx.get("gsc_data", {})
    if gsc and gsc.get("top_pages"):
        pages = gsc.get("top_pages", {}).get("pages", [])
        if pages:
            avg_pos = sum(p.get("position", 50) for p in pages[:20]) / min(len(pages), 20)
            scores["seo"] = max(0, min(100, int(100 - avg_pos * 1.5)))

    # Technical score: do crawl analyzer
    tech = ctx.get("technical_data", {})
    if tech:
        scores["technical"] = tech.get("technical_score", 0)

    # Content health score
    content = ctx.get("content_health_data", {})
    if content:
        scores["content"] = content.get("health_score", 0)

    # Reputation score: média dos scores de reputação dos concorrentes (inverso)
    complaints = ctx.get("complaints_data", {})
    if complaints:
        rep_scores = [d.get("reputation_score", 80) for d in complaints.values()]
        if rep_scores:
            scores["reputation"] = int(sum(rep_scores) / len(rep_scores))

    # AEO e GEO: estimados (sem integração direta ainda)
    scores.setdefault("aeo", None)
    scores.setdefault("geo", None)

    return scores


def _detect_main_opportunity(ctx: dict) -> str:
    # Verifica se há oportunidade de keywords na zona 8-20
    opps = ctx.get("gsc_data", {}).get("opportunities", {}).get("opportunity_zone", [])
    if opps:
        best = opps[0]
        return f"Keyword \"{best['query']}\" em posição {best['position']} com {best['impressions']} impressões/mês"

    # Ou gap no topical map
    content = ctx.get("content_health_data", {})
    topical = content.get("topical_map", {}).get("topical_map", [])
    firsts  = [t for t in topical if t.get("priority") == "🏆 Primeiro a cobrir"]
    if firsts:
        return f"Subtópico \"{firsts[0]['subtopic']}\" — nenhum concorrente cobre ainda"

    return "Análise completa disponível nos módulos acima"


def _detect_main_alert(ctx: dict) -> str:
    # Quedas de keyword
    drops = ctx.get("gsc_data", {}).get("changes", {}).get("drops", [])
    if drops:
        worst = drops[0]
        return (f"Queda de posição: \"{worst['query']}\" "
                f"{worst['position_prev']} → {worst['position_curr']}")

    # Issues técnicos críticos
    issues = ctx.get("all_issues", [])
    critical = [i for i in issues if "CRÍTICO" in i.get("severity", "")]
    if critical:
        return critical[0].get("message", "")

    return "Nenhum alerta crítico detectado"


def _detect_priority_action(ctx: dict) -> str:
    issues = ctx.get("all_issues", [])
    critical = sorted(
        [i for i in issues if "CRÍTICO" in i.get("severity", "")],
        key=lambda i: len(i.get("message", "")),
    )
    if critical and critical[0].get("action"):
        return critical[0]["action"]
    return "Revisar plano de ação no Módulo 4"


def _save_baseline(site: str, ctx: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    site_clean = site.replace("https://", "").replace("/", "-").strip("-")
    path = CACHE_DIR / f"baseline-{site_clean}.json"
    baseline = {
        "date":             date.today().isoformat(),
        "scores":           ctx.get("scores", {}),
        "top_queries":      ctx.get("gsc_data", {}).get("top_queries", [])[:20],
        "competitors":      ctx.get("competitors_analyzed", []),
    }
    with open(path, "w") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
    print(f"   Baseline salvo: {path}")


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="seo-aeo-geo-intel — Inteligência Digital Completa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Análise completa
  python main.py --site seunegocio.com.br --competitors rival1.com.br,rival2.com.br --niche "agência de SEO"

  # Só performance
  python main.py --site seunegocio.com.br --mode performance

  # Espionar concorrente
  python main.py --site rival1.com.br --mode competitor --competitors rival1.com.br

  # Monitoramento semanal
  python main.py --site seunegocio.com.br --mode delta

  # Local SEO
  python main.py --site clinica.com.br --mode local --business-name "Clínica X" --city "São Paulo" --niche "dentista"
        """
    )

    parser.add_argument("--site",          required=True, help="Domínio principal")
    parser.add_argument("--mode",          default="full",
                        choices=["full","delta","competitor","keywords","performance",
                                 "technical","local","backlinks","sentiment","pricing","radar"])
    parser.add_argument("--competitors",   default="",    help="Domínios separados por vírgula")
    parser.add_argument("--niche",         default="",    help="Nicho ou segmento do negócio")
    parser.add_argument("--days",          type=int, default=30)
    parser.add_argument("--business-name", default="",    help="Nome do negócio (modo local)")
    parser.add_argument("--city",          default="",    help="Cidade (modo local)")
    parser.add_argument("--output",        default="",    help="Caminho do arquivo de output")
    parser.add_argument("--no-cache",      action="store_true")
    parser.add_argument("--print",         action="store_true", help="Imprimir relatório na stdout")
    args = parser.parse_args()

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]

    report = run(
        site          = args.site,
        mode          = args.mode,
        competitors   = competitors,
        niche         = args.niche,
        days          = args.days,
        business_name = args.business_name,
        city          = args.city,
        use_cache     = not args.no_cache,
        output_path   = args.output,
    )

    if args.print:
        print("\n" + "─" * 60)
        print(report)
