#!/usr/bin/env python3
"""
price_monitor.py — Módulo 8
Extrai preços publicados de concorrentes e identifica gaps de mercado.
Faz diferença em nichos de serviços e SaaS onde preços são públicos.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

# Padrões para identificar preços em texto
PRICE_PATTERNS = [
    r"R\$\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)",   # R$ 1.000,00
    r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*reais",  # 1000 reais
    r"(?:a partir de|from|starting at)\s*R?\$?\s*(\d+)",
    r"(?:por apenas|por\s+apenas)\s*R?\$?\s*(\d+)",
    r"mensais?\s*:?\s*R?\$?\s*(\d+)",
    r"R?\$?\s*(\d+)\s*/\s*m[eê]s",                     # $199/mês
]

TIER_KEYWORDS = {
    "entry":   ["starter", "básico", "basic", "gratuito", "free", "essencial", "lite", "simples", "início"],
    "main":    ["profissional", "pro", "business", "padrão", "standard", "plus", "intermediário", "avançado"],
    "premium": ["enterprise", "premium", "elite", "máster", "ilimitado", "completo", "vip", "platinum"],
}

GUARANTEE_KEYWORDS = [
    "garantia", "devolv", "reembolso", "satisfação garantida",
    "money back", "30 dias", "sem risco", "risco zero",
    "se não funcionar", "caso não", "sem perguntas",
]

INSTALLMENT_KEYWORDS = [
    "parcelado", "parcela", "sem juros", "12x", "10x", "6x",
    "cartão", "boleto", "pix",
]


def extract_prices_from_text(text: str) -> list[float]:
    """Extrai valores numéricos de preços em texto."""
    prices = []
    for pattern in PRICE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            clean = m.replace(".", "").replace(",", ".")
            try:
                val = float(clean)
                if 10 < val < 100000:  # filtro de sanidade
                    prices.append(val)
            except Exception:
                pass
    return list(set(prices))


def identify_tier(text_block: str) -> str:
    """Identifica em qual tier de preço um bloco de texto se enquadra."""
    text_lower = text_block.lower()
    for tier, keywords in TIER_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return tier
    return "main"  # default


def detect_guarantee(text: str) -> dict:
    """Detecta se há garantia mencionada e de qual tipo."""
    text_lower = text.lower()
    has_guarantee = any(kw in text_lower for kw in GUARANTEE_KEYWORDS)
    days = None
    if has_guarantee:
        m = re.search(r"(\d+)\s*dias?\s*(?:de garantia|de devolução)?", text_lower)
        if m:
            days = int(m.group(1))
    return {"has_guarantee": has_guarantee, "days": days}


def detect_installments(text: str) -> dict:
    """Detecta opções de parcelamento."""
    text_lower = text.lower()
    has_installment = any(kw in text_lower for kw in INSTALLMENT_KEYWORDS)
    max_installments = None
    if has_installment:
        m = re.search(r"(\d{1,2})x\s*(?:sem juros)?", text_lower)
        if m:
            max_installments = int(m.group(1))
    return {"available": has_installment, "max_installments": max_installments}


def analyze_competitor_prices(competitor_domain: str, tavily_client=None) -> dict:
    """
    Busca e analisa preços publicados de um concorrente.
    """
    if not tavily_client:
        return {"status": "skipped", "reason": "Tavily não configurado", "domain": competitor_domain}

    domain = competitor_domain.replace("https://","").replace("http://","").rstrip("/")
    print(f"  💰 Preços: {domain}", end=" ", flush=True)

    # Páginas-alvo para busca de preços
    price_page_queries = [
        f"site:{domain} preços planos valores investimento",
        f"site:{domain} pricing plans",
        f"{domain} quanto custa preço plano",
    ]

    all_content = ""
    pages_found = []

    for query in price_page_queries[:2]:  # 2 queries para economizar créditos
        try:
            results = tavily_client.search(
                query,
                max_results=3,
                search_depth="basic",
                include_domains=[domain],
            )
            for r in results.get("results", []):
                all_content += f"\n{r.get('title','')} {r.get('content','')}"
                pages_found.append(r.get("url", ""))
        except Exception:
            pass

    if not all_content.strip():
        print("preços não encontrados publicamente")
        return {
            "status": "no_data",
            "domain": domain,
            "note": "Preços não publicados ou não acessíveis",
        }

    prices = extract_prices_from_text(all_content)
    guarantee = detect_guarantee(all_content)
    installments = detect_installments(all_content)

    # Classificar em tiers
    tiers = {}
    if prices:
        prices_sorted = sorted(prices)
        if len(prices_sorted) >= 3:
            tiers["entry"]   = prices_sorted[0]
            tiers["main"]    = prices_sorted[len(prices_sorted) // 2]
            tiers["premium"] = prices_sorted[-1]
        elif len(prices_sorted) == 2:
            tiers["entry"] = prices_sorted[0]
            tiers["main"]  = prices_sorted[1]
        elif len(prices_sorted) == 1:
            tiers["main"] = prices_sorted[0]

    print(f"{'R$ ' + str(int(tiers.get('main', 0))) if tiers else 'preço não identificado'}")

    return {
        "status": "ok",
        "domain": domain,
        "fetched_at": datetime.now().isoformat(),
        "tiers": tiers,
        "all_prices_found": sorted(prices),
        "guarantee": guarantee,
        "installments": installments,
        "pages_analyzed": list(set(pages_found))[:5],
        "source": "Tavily",
    }


def identify_market_gaps(results: list[dict]) -> list[dict]:
    """
    Compara preços de múltiplos concorrentes e identifica lacunas de mercado.
    """
    gaps = []
    valid = [r for r in results if r.get("status") == "ok" and r.get("tiers")]

    if not valid:
        return gaps

    # Gap: ninguém oferece garantia
    with_guarantee = [r for r in valid if r.get("guarantee", {}).get("has_guarantee")]
    if len(with_guarantee) < len(valid) * 0.5:
        gaps.append({
            "type": "garantia",
            "label": "🏆 Oportunidade — Garantia de resultado",
            "detail": f"Apenas {len(with_guarantee)}/{len(valid)} concorrentes oferecem garantia",
            "angle": "Ofereça garantia clara de X dias — poucos no mercado têm coragem de fazer isso.",
        })

    # Gap: parcelamento
    with_installments = [r for r in valid if r.get("installments", {}).get("available")]
    if len(with_installments) < len(valid) * 0.5:
        gaps.append({
            "type": "parcelamento",
            "label": "🏆 Oportunidade — Parcelamento sem juros",
            "detail": "Maioria cobra à vista — parcelamento pode reduzir barreira de entrada",
            "angle": "Parcelamento em X× sem juros enquanto os outros exigem pagamento à vista.",
        })

    # Gap: faixa de preço ausente
    all_main_prices = [r["tiers"].get("main", 0) for r in valid if r["tiers"].get("main")]
    if all_main_prices:
        min_p = min(all_main_prices)
        max_p = max(all_main_prices)
        if max_p > min_p * 3:
            mid = (min_p + max_p) / 2
            gaps.append({
                "type": "preco_entrada",
                "label": "💡 Lacuna de preço identificada",
                "detail": f"Range: R$ {int(min_p):,} – R$ {int(max_p):,}. Gap evidente na faixa intermediária.",
                "angle": f"Produto na faixa de R$ {int(mid):,} atenderia quem acha o básico pequeno e o premium caro.",
            })

    return gaps


def analyze(competitors: list[str], tavily_client=None) -> dict:
    """Ponto de entrada para múltiplos concorrentes."""
    results = []
    for domain in competitors:
        r = analyze_competitor_prices(domain, tavily_client)
        results.append(r)

    gaps = identify_market_gaps(results)

    return {
        "status": "ok",
        "fetched_at": datetime.now().isoformat(),
        "competitors": results,
        "market_gaps": gaps,
    }


def to_markdown(data: dict) -> str:
    """Gera seção Markdown do Módulo 8."""
    lines = ["## MÓDULO 8 — BENCHMARK DE PREÇOS", ""]

    competitors = data.get("competitors", [])
    valid = [r for r in competitors if r.get("status") == "ok"]

    if not valid:
        lines.append("status: skipped — preços não encontrados publicamente (fonte: Tavily)")
        return "\n".join(lines)

    lines.append("### Tabela Comparativa de Preços (fonte: Tavily)")
    lines.append("")
    lines.append("| Empresa | Entrada | Principal | Premium | Garantia | Parcelamento |")
    lines.append("|---|---|---|---|---|---|")

    def fmt_price(val):
        return f"R$ {int(val):,}".replace(",", ".") if val else "N/D"

    for r in competitors:
        if r.get("status") != "ok":
            lines.append(f"| {r.get('domain','?')} | N/D | N/D | N/D | N/D | N/D |")
            continue

        tiers = r.get("tiers", {})
        g = r.get("guarantee", {})
        inst = r.get("installments", {})

        guarantee_str = f"✅ {g['days']}d" if g.get("has_guarantee") and g.get("days") else ("✅ Sim" if g.get("has_guarantee") else "❌")
        inst_str = f"✅ {inst['max_installments']}x" if inst.get("max_installments") else ("✅ Sim" if inst.get("available") else "❌")

        lines.append(
            f"| {r['domain']} | {fmt_price(tiers.get('entry'))} | "
            f"{fmt_price(tiers.get('main'))} | {fmt_price(tiers.get('premium'))} | "
            f"{guarantee_str} | {inst_str} |"
        )

    lines.append("")
    lines.append("> (estimado) — preços extraídos das páginas públicas via Tavily. Podem não refletir negociações privadas.")
    lines.append("")

    gaps = data.get("market_gaps", [])
    if gaps:
        lines.append("### Gaps de Mercado Identificados")
        lines.append("")
        for gap in gaps:
            lines.append(f"**{gap['label']}**")
            lines.append(f"{gap['detail']}")
            lines.append(f"🎯 {gap['angle']}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Price Monitor — Módulo 8")
    parser.add_argument("--competitors", required=True, help="Domínios separados por vírgula")
    parser.add_argument("--output", default="json", choices=["json","markdown"])
    args = parser.parse_args()

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    except Exception:
        client = None

    domains = [d.strip() for d in args.competitors.split(",")]
    result = analyze(domains, client)

    if args.output == "markdown":
        print(to_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
