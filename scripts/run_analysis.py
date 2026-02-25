#!/usr/bin/env python3
"""
run_analysis.py — Orquestrador Principal
Ponto de entrada único para executar a skill seo-aeo-geo-intel.
Detecta modo, verifica integrações, executa módulos e gera relatório Markdown.

Uso:
    python run_analysis.py --site seunegocio.com.br
    python run_analysis.py --site seunegocio.com.br --mode competitor --target rival1.com.br
    python run_analysis.py --site seunegocio.com.br --mode delta
    python run_analysis.py --site seunegocio.com.br --mode performance
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Adicionar scripts/ ao path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

OUTPUT_DIR = Path(os.getenv("SEO_SKILL_OUTPUT_DIR", "./reports"))
CACHE_DIR  = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── Carregamento lazy de clientes de API ──
def get_tavily_client():
    key = os.getenv("TAVILY_API_KEY","")
    if not key:
        return None
    try:
        from tavily import TavilyClient
        return TavilyClient(api_key=key)
    except ImportError:
        print("⚠️  Instale tavily-python: pip install tavily-python")
        return None


def get_gsc_service():
    json_path = os.getenv("GSC_SERVICE_ACCOUNT_JSON","")
    if not json_path:
        return None
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        import json as jsonlib

        if Path(json_path).exists():
            creds = service_account.Credentials.from_service_account_file(
                json_path,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
            )
        else:
            info = jsonlib.loads(json_path)
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
            )
        return build("searchconsole", "v1", credentials=creds)
    except Exception as e:
        print(f"⚠️  GSC: {e}")
        return None


# ── Execução por módulo ──
def run_pagespeed(url: str) -> dict:
    from pagespeed_fetcher import analyze
    return analyze(url)


def run_gsc(site: str, gsc_service, days: int = 30) -> dict:
    from gsc_fetcher import fetch_all
    return fetch_all(site, gsc_service, days=days)


def run_complaints(competitor: str, tavily) -> dict:
    from complaint_detective import analyze
    return analyze(competitor, tavily_client=tavily)


def run_tech_stack(url: str, pagespeed_data: dict = None) -> dict:
    from tech_stack_detector import analyze
    return analyze(url, pagespeed_data)


def run_prices(competitors: list, tavily) -> dict:
    from price_monitor import analyze
    return analyze(competitors, tavily)


def run_radar(site: str, keywords: list, competitors: list, tavily) -> dict:
    from new_entrant_radar import find_new_entrants
    return find_new_entrants(site, keywords, competitors, tavily_client=tavily)


def run_positioning(competitor: str, name: str, tavily, html: str = "") -> dict:
    from competitor_intel import analyze_competitor_positioning
    return analyze_competitor_positioning(competitor, name, tavily, html)


def run_lead_magnets(competitor: str, name: str, tavily) -> dict:
    from lead_magnet_spy import analyze
    return analyze(competitor, name, tavily)


def run_crawl(site: str, gsc_service) -> dict:
    from crawl_analyzer import analyze
    return analyze(site, gsc_service)


def run_internal_links(site: str, gsc_service, tavily) -> dict:
    from internal_link_analyzer import analyze
    return analyze(site, gsc_service, tavily)


def run_content_health(site: str, gsc_service, tavily) -> dict:
    from content_health import analyze
    return analyze(site, gsc_service, tavily)


def run_local_seo(site: str, business_name: str, city: str, tavily) -> dict:
    from local_seo_analyzer import analyze
    return analyze(site, business_name, city, tavily)


def run_backlinks(site: str, competitors: list) -> dict:
    from backlink_fetcher import analyze
    return analyze(site, competitors)


# ── Construtor do relatório Markdown ──
def build_report(data: dict, mode: str, site: str) -> str:
    from output.markdown_builder import build
    return build(data, mode, site)


# ── Fluxo principal ──
def run(args):
    site   = args.site.replace("https://","").replace("http://","").rstrip("/")
    mode   = args.mode
    days   = args.days
    competitors = [c.strip() for c in args.competitors.split(",")] if args.competitors else []
    target = args.target  # para modo competitor

    print(f"\n{'='*55}")
    print(f"  seo-aeo-geo-intel v2.2")
    print(f"  Site: {site} | Modo: {mode}")
    print(f"{'='*55}\n")

    # Verificar integrações
    tavily  = get_tavily_client()
    gsc     = get_gsc_service()
    has_ps  = bool(os.getenv("PAGESPEED_API_KEY",""))

    print("📡 Integrações:")
    print(f"  {'✅' if tavily  else '❌'} Tavily API")
    print(f"  {'✅' if gsc     else '❌'} Google Search Console")
    print(f"  {'✅' if has_ps  else '⚠️ '} PageSpeed API {'(estimativa)' if not has_ps else ''}")
    print()

    if not tavily and not gsc:
        print("❌ Nenhuma API disponível. Configure TAVILY_API_KEY ou GSC_SERVICE_ACCOUNT_JSON.")
        sys.exit(1)

    data = {
        "meta": {
            "skill_version": "2.2",
            "site": site,
            "mode": mode,
            "start_time": datetime.now().isoformat(),
            "days": days,
            "competitors_monitored": competitors,
        },
        "modules": {},
        "skipped": [],
        "warnings": [],
    }

    site_url = f"https://{site}"

    # ── MODO: full ──
    if mode == "full":
        print("🚀 Iniciando análise completa...\n")

        # PageSpeed do seu site
        if has_ps:
            print("📊 Módulo: PageSpeed")
            data["pagespeed"] = run_pagespeed(site_url)
        else:
            data["skipped"].append({"module": "pagespeed", "reason": "PAGESPEED_API_KEY não configurada"})

        # GSC
        if gsc:
            print("\n📊 Módulo: GSC (dados do seu site)")
            data["gsc"] = run_gsc(site, gsc, days=days)
        else:
            data["skipped"].append({"module": "gsc", "reason": "GSC não configurado"})

        # Concorrentes (detectar automaticamente se não informados)
        if not competitors and tavily:
            print("\n🔍 Detectando concorrentes automaticamente...")
            # Busca simples para encontrar quem compete
            try:
                niche_query = data.get("gsc", {}).get("top_keywords", [])[:3]
                if niche_query:
                    results = tavily.search(" ".join(niche_query[:2]), max_results=5)
                    auto_competitors = []
                    for r in results.get("results",[]):
                        d = r.get("url","").replace("https://","").replace("http://","").split("/")[0]
                        if d and d != site and d not in auto_competitors:
                            auto_competitors.append(d)
                    competitors = auto_competitors[:3]
                    print(f"  → {len(competitors)} concorrente(s) detectado(s): {', '.join(competitors)}")
            except Exception:
                pass

        # Tech stack (seu site + concorrentes)
        if tavily or has_ps:
            print("\n📊 Módulo 7: Tech Stack")
            tech_results = [run_tech_stack(site_url, data.get("pagespeed"))]
            for c in competitors:
                tech_results.append(run_tech_stack(f"https://{c}"))
            data["modules"]["tech_stack"] = tech_results

        # Reclamações dos concorrentes
        if tavily and competitors:
            print("\n📊 Módulo 5: Detetive de Reclamações")
            data["modules"]["complaints"] = [run_complaints(c, tavily) for c in competitors]

        # Iscas dos concorrentes
        if tavily and competitors:
            print("\n📊 Módulo 6: Espião de Iscas")
            data["modules"]["lead_magnets"] = [run_lead_magnets(c, "", tavily) for c in competitors]

        # Preços
        if tavily and competitors:
            print("\n📊 Módulo 8: Benchmark de Preços")
            data["modules"]["prices"] = run_prices(competitors, tavily)

        # Posicionamento + Canais
        if tavily and competitors:
            print("\n📊 Módulos 10+11: Posicionamento e Canais")
            data["modules"]["positioning"] = [run_positioning(c, "", tavily) for c in competitors]

        # Radar de entrantes
        if tavily and gsc:
            print("\n📊 Módulo 9: Radar de Entrantes")
            top_kws = [k["query"] for k in data.get("gsc",{}).get("top_keywords",[])[:10]]
            data["modules"]["radar"] = run_radar(site, top_kws, competitors, tavily)
        else:
            data["skipped"].append({"module": "radar", "reason": "Requer GSC + Tavily"})

        # SEO Técnico
        if gsc:
            print("\n📊 Módulo 12: SEO Técnico (Crawl & Indexação)")
            data["modules"]["seo_tecnico"] = run_crawl(site, gsc)

        # Links Internos
        if gsc:
            print("\n📊 Módulo 13: Links Internos")
            data["modules"]["internal_links"] = run_internal_links(site, gsc, tavily)
        else:
            data["skipped"].append({"module": "internal_links", "reason": "Requer GSC"})

        # Saúde do Conteúdo
        if gsc:
            print("\n📊 Módulo 15: Saúde do Conteúdo")
            data["modules"]["content_health"] = run_content_health(site, gsc, tavily)
        else:
            data["skipped"].append({"module": "content_health", "reason": "Requer GSC"})

        # Backlinks (opcional)
        if os.getenv("AHREFS_API_KEY") or os.getenv("SEMRUSH_API_KEY"):
            print("\n📊 Módulo 14: Backlinks")
            data["modules"]["backlinks"] = run_backlinks(site, competitors)
        else:
            data["skipped"].append({"module": "backlinks", "reason": "Ahrefs e Semrush não configurados"})

        # Local SEO (condicional)
        if args.local_seo and tavily:
            print("\n📊 Módulo 16: Local SEO")
            data["modules"]["local_seo"] = run_local_seo(site, args.business_name or site, args.city or "", tavily)

    # ── MODO: performance ──
    elif mode == "performance":
        if has_ps:
            data["pagespeed"] = run_pagespeed(site_url)
        if tavily and competitors:
            data["modules"]["tech_stack"] = [run_tech_stack(f"https://{c}") for c in competitors[:3]]
        if gsc:
            data["modules"]["seo_tecnico"] = run_crawl(site, gsc)

    # ── MODO: competitor ──
    elif mode == "competitor":
        target_domain = target or (competitors[0] if competitors else None)
        if not target_domain:
            print("❌ Informe --target DOMINIO para o modo competitor")
            sys.exit(1)

        if tavily:
            ps_data = run_pagespeed(f"https://{target_domain}") if has_ps else {}
            data["modules"]["tech_stack"]   = [run_tech_stack(f"https://{target_domain}", ps_data)]
            data["modules"]["complaints"]   = [run_complaints(target_domain, tavily)]
            data["modules"]["lead_magnets"] = [run_lead_magnets(target_domain, "", tavily)]
            data["modules"]["prices"]       = run_prices([target_domain], tavily)
            data["modules"]["positioning"]  = [run_positioning(target_domain, "", tavily)]

    # ── MODO: delta ──
    elif mode == "delta":
        if gsc:
            data["gsc"] = run_gsc(site, gsc, days=7)
        if tavily and competitors:
            # Delta só verifica tech stack e reclamações (leve)
            data["modules"]["complaints"] = [run_complaints(c, tavily) for c in competitors[:2]]

    # ── MODO: keywords ──
    elif mode == "keywords":
        if gsc:
            data["gsc"] = run_gsc(site, gsc, days=days)
        if gsc and tavily:
            data["modules"]["content_health"] = run_content_health(site, gsc, tavily)

    # ── MODO: technical ──
    elif mode == "technical":
        if has_ps:
            data["pagespeed"] = run_pagespeed(site_url)
        if gsc:
            data["modules"]["seo_tecnico"]    = run_crawl(site, gsc)
            data["modules"]["internal_links"] = run_internal_links(site, gsc, tavily)

    # ── Gerar relatório Markdown ──
    data["meta"]["end_time"] = datetime.now().isoformat()

    print("\n📝 Gerando relatório Markdown...")
    report_md = build_report(data, mode, site)

    # Salvar
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"relatorio-{date_str}-{site}-{mode}.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(report_md, encoding="utf-8")

    # Salvar baseline para modo delta
    if mode == "full":
        baseline_path = CACHE_DIR / f"baseline-{site}.json"
        baseline_data = {
            "date": date_str,
            "gsc_summary": data.get("gsc", {}).get("summary", {}),
            "pagespeed_mobile": data.get("pagespeed", {}).get("mobile", {}).get("scores", {}),
            "competitors": competitors,
        }
        baseline_path.write_text(json.dumps(baseline_data, ensure_ascii=False, indent=2))
        print(f"  → Baseline salvo: {baseline_path}")

    print(f"\n✅ Relatório salvo: {output_path}")
    print(f"   Módulos executados: {len(data['modules'])}")
    print(f"   Pulados: {len(data['skipped'])}")

    if data["skipped"]:
        print("\n⏭️  Módulos pulados:")
        for s in data["skipped"]:
            print(f"   • {s['module']}: {s['reason']}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="seo-aeo-geo-intel v2.2 — Análise de Inteligência Digital",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_analysis.py --site seunegocio.com.br
  python run_analysis.py --site seunegocio.com.br --mode performance
  python run_analysis.py --site seunegocio.com.br --mode competitor --target rival.com.br
  python run_analysis.py --site seunegocio.com.br --mode delta
  python run_analysis.py --site seunegocio.com.br --competitors rival1.com.br,rival2.com.br
        """
    )
    parser.add_argument("--site",         required=True, help="Seu domínio (ex: seunegocio.com.br)")
    parser.add_argument("--mode",         default="full",
                        choices=["full","delta","competitor","keywords","performance","technical","local"],
                        help="Modo de execução (padrão: full)")
    parser.add_argument("--target",       default="", help="Domínio alvo para modo competitor")
    parser.add_argument("--competitors",  default="", help="Concorrentes conhecidos (vírgula)")
    parser.add_argument("--days",         type=int, default=30, help="Período GSC em dias (padrão: 30)")
    parser.add_argument("--local-seo",    action="store_true", help="Ativar módulo de Local SEO")
    parser.add_argument("--business-name",default="", help="Nome comercial para Local SEO")
    parser.add_argument("--city",         default="", help="Cidade para Local SEO")
    args = parser.parse_args()

    run(args)


if __name__ == "__main__":
    main()
