#!/usr/bin/env python3
"""
competitor_intel.py — Módulos 10 e 11
Módulo 10: Análise de posicionamento (promessa, inimigo, prova, garantia, proposta única)
Módulo 11: Mapa de canais e anúncios (pixels ativos, canais usados, copy de ads)
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

# ────────────────────────────────────────
# MÓDULO 10 — Análise de Posicionamento
# ────────────────────────────────────────

POSITIONING_PATTERNS = {
    "main_promise": [
        r"(?:ajudamos?|ajuda)\s+(?:\w+\s+){1,8}(?:a\s+)?(.{20,80})",
        r"(?:transformamos?|transforme)\s+(.{20,80})",
        r"(?:a solução|a plataforma|o sistema)\s+(?:que\s+)?(.{20,80})",
        r"(?:aumente|gere|conquiste|escale|automatize)\s+(.{20,80})",
        r"(?:Nós|Nosso time|Nossa equipe)\s+(.{20,80})",
    ],
    "enemy_identified": [
        r"(?:esqueça|chega de|pare de|cansado de|sem mais)\s+(.{15,60})",
        r"(?:nunca mais|não precisa mais)\s+(.{15,60})",
        r"(?:enquanto|diferente de|ao contrário de)\s+(?:outros|a maioria|concorrentes)\s+(.{20,60})",
    ],
    "proof_elements": [
        r"(\d+)\s*(?:clientes?|empresas?|marcas?)\s*(?:atendidas?|satisfeitos?)?",
        r"(\d+)\s*(?:anos?|meses?)\s*(?:de|no)\s*(?:mercado|experiência)",
        r"R\$\s*(\d[\d.,]+)\s*(?:em|de)\s*(?:resultados?|faturamento|vendas?|receita)",
        r"(\d+)%\s*(?:de|dos?|das?)\s*(?:clientes?|casos?|projetos?)",
        r"(?:case|caso)\s+(?:de sucesso|real):\s*(.{20,60})",
    ],
    "unique_value": [
        r"(?:único|única|exclusivo|exclusiva|só nós|apenas nós|somente nós)\s+(.{20,80})",
        r"(?:a única\s+(?:empresa|agência|plataforma|solução))\s+(?:que|no Brasil|do Brasil)\s+(.{20,80})",
        r"(?:método|metodologia|framework|processo)\s+(?:proprietário|próprio|exclusivo)\s*:?\s*(.{10,60})",
    ],
}

POSITIONING_GAPS = [
    {"id": "no_deadline_guarantee",   "label": "Sem prazo garantido na promessa"},
    {"id": "no_roi_claim",            "label": "Sem ROI/resultado mensurável"},
    {"id": "no_enemy_identified",     "label": "Não identifica inimigo/dor explícita"},
    {"id": "no_unique_method",        "label": "Sem metodologia proprietária citada"},
    {"id": "no_social_proof_numbers", "label": "Sem números de prova social"},
    {"id": "generic_promise",         "label": "Promessa genérica (fácil de imitar)"},
]

# ────────────────────────────────────────
# MÓDULO 11 — Mapa de Canais e Anúncios
# ────────────────────────────────────────

CHANNEL_SIGNALS = {
    "Google Ads": {
        "patterns": ["googleadservices.com", "AW-", "google_conversion", "gclid"],
        "icon": "🔵",
    },
    "Meta Ads (Facebook/Instagram)": {
        "patterns": ["connect.facebook.net/en_US/fbevents", "fbq(", "_fbp", "facebook.com/tr"],
        "icon": "🔵",
    },
    "TikTok Ads": {
        "patterns": ["analytics.tiktok.com", "tiktok-pixel", "_ttp", "ttq.load"],
        "icon": "⚫",
    },
    "LinkedIn Ads": {
        "patterns": ["snap.licdn.com", "linkedin.com/px", "_li_"],
        "icon": "🔵",
    },
    "Pinterest Ads": {
        "patterns": ["pintrk(", "ct.pinterest.com"],
        "icon": "🔴",
    },
    "Taboola": {
        "patterns": ["trc.taboola.com", "_taboola"],
        "icon": "🟡",
    },
    "Outbrain": {
        "patterns": ["outbrain.com/pixel", "OBPixelID"],
        "icon": "🟡",
    },
    "YouTube Ads": {
        "patterns": ["gtag('config', 'AW-", "youtube.com/channel"],
        "icon": "🔴",
    },
}

ORGANIC_CHANNEL_SIGNALS = {
    "YouTube": {
        "queries": ["site:youtube.com {name}", "{name} canal youtube"],
        "icon": "🔴",
    },
    "Instagram": {
        "queries": ["site:instagram.com {name}", "{name} @instagram"],
        "icon": "📸",
    },
    "LinkedIn": {
        "queries": ["site:linkedin.com/company {domain}"],
        "icon": "🔵",
    },
    "TikTok Orgânico": {
        "queries": ["site:tiktok.com @{name}", "{name} tiktok"],
        "icon": "⚫",
    },
    "Pinterest Orgânico": {
        "queries": ["site:pinterest.com {name}"],
        "icon": "🔴",
    },
    "Podcast": {
        "queries": ["{name} podcast spotify anchor"],
        "icon": "🎙️",
    },
}


def extract_positioning(text: str) -> dict:
    """Extrai elementos de posicionamento do texto da página."""
    result = {}

    for element, patterns in POSITIONING_PATTERNS.items():
        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            found.extend(m.strip() for m in matches if len(m.strip()) > 15)
        result[element] = found[:3]  # top 3 por elemento

    return result


def detect_gaps(positioning: dict) -> list[str]:
    """Identifica quais elementos de posicionamento estão ausentes."""
    gaps = []

    if not positioning.get("main_promise"):
        gaps.append("no_roi_claim")

    if not positioning.get("enemy_identified"):
        gaps.append("no_enemy_identified")

    if not positioning.get("unique_value"):
        gaps.append("no_unique_method")

    if not positioning.get("proof_elements"):
        gaps.append("no_social_proof_numbers")

    # Verificar se a promessa menciona prazo
    promise_text = " ".join(positioning.get("main_promise", []))
    if not re.search(r"\d+\s*(?:dias?|semanas?|horas?|meses?)", promise_text):
        gaps.append("no_deadline_guarantee")

    return gaps


def detect_paid_channels(html: str) -> list[dict]:
    """Detecta pixels de anúncio no HTML."""
    channels = []
    for channel, data in CHANNEL_SIGNALS.items():
        for pattern in data["patterns"]:
            if pattern in html:
                channels.append({
                    "name": channel,
                    "icon": data["icon"],
                    "type": "paid",
                })
                break
    return channels


def detect_organic_channels(domain: str, name: str, tavily_client) -> list[dict]:
    """Detecta canais orgânicos ativos via Tavily."""
    channels = []
    domain_clean = domain.replace("https://","").replace("http://","").split("/")[0]
    name_clean = name or domain_clean.replace(".com.br","").replace(".com","")

    for channel, data in ORGANIC_CHANNEL_SIGNALS.items():
        query = data["queries"][0].replace("{domain}", domain_clean).replace("{name}", name_clean)
        try:
            results = tavily_client.search(query, max_results=2, search_depth="basic")
            if results.get("results"):
                channels.append({
                    "name": channel,
                    "icon": data["icon"],
                    "type": "organic",
                    "evidence": results["results"][0].get("url",""),
                })
        except Exception:
            pass

    return channels


def analyze_competitor_positioning(
    competitor_domain: str,
    competitor_name: str = "",
    tavily_client=None,
    html: str = "",
) -> dict:
    """Análise completa de posicionamento de um concorrente."""
    if not tavily_client:
        return {"status": "skipped", "reason": "Tavily não configurado"}

    domain = competitor_domain.replace("https://","").replace("http://","").split("/")[0]
    name = competitor_name or domain.replace(".com.br","").replace(".com","").title()

    print(f"  🧠 Posicionamento: {name}", end=" ", flush=True)

    # Buscar homepage e páginas principais
    try:
        results = tavily_client.search(
            f'site:{domain} OR "{name}" promessa proposta valor diferencial',
            max_results=5,
            search_depth="advanced",
            include_domains=[domain],
        )
        page_content = " ".join(r.get("content","") for r in results.get("results",[]))
    except Exception:
        page_content = html

    positioning = extract_positioning(page_content)
    gaps = detect_gaps(positioning)

    paid_channels = detect_paid_channels(html)
    organic_channels = detect_organic_channels(domain, name, tavily_client) if tavily_client else []

    print(f"{len(paid_channels)} canais pagos | {len(gaps)} gaps de posicionamento")

    result = {
        "status": "ok",
        "domain": domain,
        "name": name,
        "fetched_at": datetime.now().isoformat(),
        # Módulo 10
        "positioning": positioning,
        "positioning_gaps": gaps,
        # Módulo 11
        "paid_channels": paid_channels,
        "organic_channels": organic_channels,
        "total_channels": len(paid_channels) + len(organic_channels),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"positioning-{domain}-{datetime.now().strftime('%Y-%m-%d')}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def identify_channel_gaps(results: list[dict]) -> list[dict]:
    """Identifica canais onde nenhum concorrente está presente."""
    all_channels = set()
    for r in results:
        if r.get("status") != "ok":
            continue
        for c in r.get("paid_channels", []) + r.get("organic_channels", []):
            all_channels.add(c["name"])

    major_channels = ["YouTube", "TikTok Orgânico", "LinkedIn", "Instagram",
                      "Google Ads", "Meta Ads (Facebook/Instagram)", "Podcast"]

    gaps = []
    for ch in major_channels:
        if ch not in all_channels:
            gaps.append({
                "channel": ch,
                "label": f"🏆 Canal livre — nenhum concorrente presente em {ch}",
                "opportunity": "Primeiros nesse canal podem dominar com menor CAC",
            })

    return gaps


def to_markdown_module10(results: list[dict]) -> str:
    """Gera seção Markdown do Módulo 10."""
    lines = ["## MÓDULO 10 — ANÁLISE DE POSICIONAMENTO", ""]

    for r in results:
        if r.get("status") != "ok":
            continue

        name = r.get("name", r.get("domain",""))
        pos = r.get("positioning", {})
        gaps = r.get("positioning_gaps", [])

        lines.append(f"### {name}")
        lines.append("")
        lines.append("| Elemento | Detectado |")
        lines.append("|---|---|")

        labels = {
            "main_promise": "Promessa principal",
            "enemy_identified": "Inimigo/dor identificada",
            "proof_elements": "Elementos de prova",
            "unique_value": "Proposta única",
        }

        for key, label in labels.items():
            items = pos.get(key, [])
            val = items[0][:80] + "…" if items else "❌ Não detectado"
            lines.append(f"| {label} | {val} |")

        lines.append("")

        if gaps:
            lines.append(f"**Gaps de posicionamento ({len(gaps)} identificados):**")
            gap_labels = {g["id"]: g["label"] for g in POSITIONING_GAPS}
            for g in gaps:
                lines.append(f"→ 🏆 {gap_labels.get(g, g)}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def to_markdown_module11(results: list[dict]) -> str:
    """Gera seção Markdown do Módulo 11."""
    lines = ["## MÓDULO 11 — MAPA DE CANAIS E ANÚNCIOS", ""]

    # Tabela de canais por concorrente
    all_channel_names = set()
    for r in results:
        if r.get("status") == "ok":
            for c in r.get("paid_channels",[]) + r.get("organic_channels",[]):
                all_channel_names.add(c["name"])

    if all_channel_names:
        header = "| Concorrente | " + " | ".join(sorted(all_channel_names)) + " |"
        separator = "|---|" + "---|" * len(all_channel_names)
        lines.append(header)
        lines.append(separator)

        for r in results:
            if r.get("status") != "ok":
                continue
            active = set(c["name"] for c in r.get("paid_channels",[]) + r.get("organic_channels",[]))
            row = f"| {r.get('name', r.get('domain',''))} |"
            for ch in sorted(all_channel_names):
                row += " ✅ |" if ch in active else " ❌ |"
            lines.append(row)

        lines.append("")

    # Gaps de canal
    gaps = identify_channel_gaps(results)
    if gaps:
        lines.append("### 🏆 Oportunidades de Canal")
        lines.append("")
        for g in gaps:
            lines.append(f"**{g['label']}**")
            lines.append(f"→ {g['opportunity']}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--module", default="both", choices=["10","11","both"])
    args = parser.parse_args()

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    except Exception:
        client = None

    result = analyze_competitor_positioning(args.competitor, args.name, client)
    print(json.dumps(result, ensure_ascii=False, indent=2))
