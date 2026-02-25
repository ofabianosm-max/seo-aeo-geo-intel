#!/usr/bin/env python3
"""
check_integrations.py
Verifica o status de todas as integrações da skill seo-aeo-geo-intel.
Executar antes de análises para garantir que as APIs estão disponíveis.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"

def ok(msg):    print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg):  print(f"  {RED}❌ {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}⚠️  {msg}{RESET}")
def skip(msg):  print(f"  {CYAN}⏭️  {msg}{RESET}")
def info(msg):  print(f"     {msg}")


def check_tavily() -> dict:
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        fail("Tavily API — não configurada")
        info("Obter em: https://tavily.com")
        info("Variável: TAVILY_API_KEY")
        return {"status": "missing", "modules_affected": [2,5,6,7,8,9,10,11,13,15,16]}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=key)
        result = client.search("test", max_results=1)
        ok(f"Tavily API — OK")
        return {"status": "ok"}
    except ImportError:
        warn("Tavily API — chave encontrada, mas pacote não instalado")
        info("Execute: pip install tavily-python")
        return {"status": "package_missing"}
    except Exception as e:
        fail(f"Tavily API — erro de conexão: {str(e)[:60]}")
        return {"status": "error", "error": str(e)}


def check_gsc() -> dict:
    json_path = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
    oauth_token = os.getenv("GSC_OAUTH_TOKEN", "")

    if not json_path and not oauth_token:
        fail("Google Search Console — não configurado")
        info("Guia de configuração: references/onboarding.md → Integração 2")
        info("Variável: GSC_SERVICE_ACCOUNT_JSON ou GSC_OAUTH_TOKEN")
        return {"status": "missing", "modules_affected": [1,3,9,12,13,15]}

    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        # Tentar carregar do JSON
        if json_path:
            if os.path.isfile(json_path):
                creds_data = json_path
            else:
                # Pode ser o conteúdo inline
                creds_data = json.loads(json_path)
                import tempfile
                tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(creds_data, tmp)
                tmp.close()
                creds_data = tmp.name

            creds = service_account.Credentials.from_service_account_file(
                creds_data,
                scopes=['https://www.googleapis.com/auth/webmasters.readonly']
            )
            service = build('searchconsole', 'v1', credentials=creds)
            sites = service.sites().list().execute()
            site_count = len(sites.get('siteEntry', []))
            ok(f"Google Search Console — OK ({site_count} propriedade(s) encontrada(s))")
            return {"status": "ok", "sites": site_count}

    except ImportError:
        warn("GSC — credencial encontrada, mas pacote não instalado")
        info("Execute: pip install google-auth google-auth-oauthlib google-api-python-client")
        return {"status": "package_missing"}
    except Exception as e:
        fail(f"GSC — erro de conexão: {str(e)[:60]}")
        return {"status": "error", "error": str(e)}


def check_pagespeed() -> dict:
    key = os.getenv("PAGESPEED_API_KEY", "")
    if not key:
        warn("PageSpeed API — não configurada [recomendada]")
        info("Dados de performance serão estimados (menos precisos)")
        info("Obter gratuitamente: https://console.developers.google.com")
        info("Variável: PAGESPEED_API_KEY")
        return {"status": "missing", "impact": "performance_estimated"}

    try:
        import requests
        url = (
            f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url=https://google.com&strategy=mobile&key={key}"
            f"&category=performance"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            score = int(data['lighthouseResult']['categories']['performance']['score'] * 100)
            ok(f"PageSpeed API — OK (teste: google.com mobile = {score}/100)")
            return {"status": "ok"}
        elif r.status_code == 400:
            fail(f"PageSpeed API — chave inválida (HTTP 400)")
            return {"status": "invalid_key"}
        else:
            fail(f"PageSpeed API — erro HTTP {r.status_code}")
            return {"status": "error", "http_status": r.status_code}
    except ImportError:
        warn("PageSpeed — chave encontrada, mas 'requests' não instalado")
        info("Execute: pip install requests")
        return {"status": "package_missing"}
    except Exception as e:
        fail(f"PageSpeed API — erro: {str(e)[:60]}")
        return {"status": "error", "error": str(e)}


def check_ahrefs() -> dict:
    key = os.getenv("AHREFS_API_KEY", "")
    if not key:
        skip("Ahrefs API — não configurada [opcional]")
        info("Módulo 14 (Backlinks) ficará indisponível")
        info("Necessário plano Advanced do Ahrefs")
        return {"status": "skipped"}

    try:
        import requests
        r = requests.get(
            "https://apiv2.ahrefs.com",
            params={"from": "subscription_info", "token": key, "output": "json"},
            timeout=10
        )
        if r.status_code == 200:
            ok("Ahrefs API — OK")
            return {"status": "ok"}
        else:
            fail(f"Ahrefs API — chave inválida ou sem permissão (HTTP {r.status_code})")
            return {"status": "invalid_key"}
    except Exception as e:
        fail(f"Ahrefs API — erro: {str(e)[:60]}")
        return {"status": "error", "error": str(e)}


def check_semrush() -> dict:
    key = os.getenv("SEMRUSH_API_KEY", "")
    if not key:
        skip("Semrush API — não configurada [opcional]")
        info("Alternativa ao Ahrefs para dados de backlinks")
        return {"status": "skipped"}

    try:
        import requests
        r = requests.get(
            f"https://api.semrush.com/?type=phrase_this&key={key}"
            f"&phrase=test&export_columns=Ph,Nq&database=br",
            timeout=10
        )
        if "ERROR" not in r.text and r.status_code == 200:
            ok("Semrush API — OK")
            return {"status": "ok"}
        else:
            fail(f"Semrush API — chave inválida ou sem créditos")
            return {"status": "invalid_key"}
    except Exception as e:
        fail(f"Semrush API — erro: {str(e)[:60]}")
        return {"status": "error", "error": str(e)}


def compute_coverage(results: dict) -> dict:
    """Calcula quais módulos estão disponíveis com base nas integrações."""

    all_modules = list(range(1, 17))
    skipped = []

    # Módulos que dependem do GSC
    if results["gsc"]["status"] != "ok":
        gsc_modules = [1, 3, 9, 12, 13, 15]
        # Módulo 1 é parcialmente disponível via Tavily
        # Módulo 12 é parcialmente disponível via PageSpeed
        for m in gsc_modules:
            if m not in skipped:
                skipped.append(m)

    # Módulos que dependem do Tavily
    if results["tavily"]["status"] != "ok":
        tavily_modules = [2, 5, 6, 7, 8, 9, 10, 11, 13, 15, 16]
        for m in tavily_modules:
            if m not in skipped:
                skipped.append(m)

    # Módulo 14 depende de Ahrefs OU Semrush
    if results["ahrefs"]["status"] != "ok" and results["semrush"]["status"] != "ok":
        if 14 not in skipped:
            skipped.append(14)

    # Módulo 16 (Local SEO) é condicional — não conta como skip obrigatório

    available = [m for m in all_modules if m not in skipped]
    return {"available": sorted(available), "skipped": sorted(skipped)}


def print_coverage_summary(coverage: dict):
    available = coverage["available"]
    skipped = coverage["skipped"]

    print()
    print(f"{BOLD}📊 Cobertura de Módulos:{RESET}")
    print(f"  ✅ Disponíveis ({len(available)}/16): {', '.join(map(str, available))}")
    if skipped:
        print(f"  ⏭️  Indisponíveis ({len(skipped)}/16): {', '.join(map(str, skipped))}")

    # Qual cenário
    if len(available) == 16:
        print(f"\n  {GREEN}{BOLD}🏆 Setup completo — todos os módulos ativos{RESET}")
    elif len(available) >= 12:
        print(f"\n  {GREEN}✅ Setup recomendado — cobertura boa para análise completa{RESET}")
    elif len(available) >= 8:
        print(f"\n  {YELLOW}⚠️  Setup parcial — análise de concorrentes disponível, dados do seu site limitados{RESET}")
    else:
        print(f"\n  {RED}❌ Setup mínimo — configure GSC para análises mais completas{RESET}")


def main():
    print(f"\n{BOLD}🔧 seo-aeo-geo-intel — Verificação de Integrações{RESET}")
    print("=" * 55)

    results = {}

    print(f"\n{BOLD}APIs Obrigatórias:{RESET}")
    results["tavily"]     = check_tavily()
    results["gsc"]        = check_gsc()

    print(f"\n{BOLD}APIs Recomendadas:{RESET}")
    results["pagespeed"]  = check_pagespeed()

    print(f"\n{BOLD}APIs Opcionais:{RESET}")
    results["ahrefs"]     = check_ahrefs()
    results["semrush"]    = check_semrush()

    coverage = compute_coverage(results)
    print_coverage_summary(coverage)

    print()

    # Exit code 0 se pelo menos Tavily ou GSC disponível
    if results["tavily"]["status"] == "ok" or results["gsc"]["status"] == "ok":
        sys.exit(0)
    else:
        print(f"  {RED}Configure ao menos Tavily ou GSC para usar a skill.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
