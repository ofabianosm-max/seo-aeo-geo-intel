#!/usr/bin/env python3
"""
complaint_detective.py — Módulo 5
Encontra reclamações sobre concorrentes em Reclame Aqui, Google Reviews,
Reddit, fóruns e redes sociais. Categoriza padrões e gera copy de vendas.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

# Categorias de reclamação e seus termos associados
COMPLAINT_CATEGORIES = {
    "prazo_entrega": [
        "demora", "demorou", "atrasou", "atraso", "prazo", "prometeu",
        "não entregou", "nunca chegou", "sumiu", "semanas", "meses esperando",
        "muito tempo", "demorado", "lento", "cadê",
    ],
    "suporte_atendimento": [
        "sem resposta", "não respondem", "ignoraram", "sumiram",
        "atendimento horrível", "não atendem", "difícil contato",
        "ninguém resolve", "jogam para lá e para cá", "chat não funciona",
        "ligação não atende", "email sem retorno",
    ],
    "qualidade_resultado": [
        "não funcionou", "resultado ruim", "abaixo do esperado",
        "não adiantou", "não melhorou", "piorou", "problema voltou",
        "não resolveu", "mal feito", "cheio de erros", "péssima qualidade",
    ],
    "preco_cobranca": [
        "caro demais", "cobrou a mais", "cobrança indevida", "não avisou",
        "aumento sem aviso", "taxa escondida", "não devolveu", "reembolso",
        "estorno", "pegou o dinheiro", "não cumpriu", "propaganda enganosa",
    ],
    "pos_venda": [
        "depois que pagou", "sumiu após contrato", "não acompanha",
        "sem suporte pós", "abandonou", "esqueceram", "mudou tudo",
        "não dá atenção", "só quer vender",
    ],
    "tecnico_plataforma": [
        "sistema caiu", "bug", "erro", "não carrega", "travou",
        "perdeu dados", "falha", "instável", "fora do ar",
    ],
}

# Frases geradoras de copy de vendas por categoria
COPY_ANGLES = {
    "prazo_entrega": [
        "Enquanto {rival} demora {X} semanas, entregamos em {Y} dias — com data garantida no contrato.",
        "Cansado de esperar? Nossos projetos têm prazo fixo. Se atrasar, você não paga.",
        "67% das reclamações do mercado são sobre atraso. Nós entregamos na data ou devolvemos tudo.",
    ],
    "suporte_atendimento": [
        "No {rival}, você fica na fila. Aqui você fala com especialista em até {X}h.",
        "Suporte que some depois do contrato? Aqui você tem canal direto por todo o projeto.",
        "Você merece ser atendido. Tempo médio de resposta: menos de {X} horas.",
    ],
    "qualidade_resultado": [
        "Resultado ruim com garantia de nada? Aqui trabalhamos com métricas acordadas. Sem resultado, sem pagamento.",
        "Antes de contratar, veja os números reais dos nossos clientes — não prints de tela.",
        "Prometem o mundo, entregam pouco. Nós mostramos o resultado antes de cobrar.",
    ],
    "preco_cobranca": [
        "Preço fixo, sem surpresas. O que foi acordado é o que você paga — período.",
        "Cobrança indevida e taxa escondida são o maior medo de quem já foi enganado. Nossa proposta é tudo incluído.",
        "Invista com transparência. Contrato claro, nota fiscal em tudo, sem cobranças extras.",
    ],
    "pos_venda": [
        "O projeto não termina na entrega — começa. Acompanhamento mensal incluso.",
        "A maioria some após o pagamento. Nós fazemos reunião mensal de resultados pelo primeiro ano.",
        "Seu sucesso é o nosso portfolio. Por isso não te largamos.",
    ],
    "tecnico_plataforma": [
        "Plataforma estável, uptime 99.9%, backups diários. Sem susto.",
        "Construído para durar — não para impressionar na demo e travar na produção.",
    ],
}


def build_search_queries(competitor_domain: str, competitor_name: str = "") -> list[dict]:
    """Gera queries estratégicas para cada fonte de reclamação."""
    name = competitor_name or competitor_domain.replace(".com.br", "").replace(".com", "").replace("-", " ").title()

    queries = [
        # Reclame Aqui
        {"source": "reclame_aqui", "query": f'site:reclameaqui.com.br "{name}"', "max_results": 5},
        {"source": "reclame_aqui", "query": f'reclameaqui.com.br {name} reclamação', "max_results": 5},

        # Google Reviews / Maps
        {"source": "google_reviews", "query": f'"{name}" avaliação ruim Google Maps problemas', "max_results": 5},
        {"source": "google_reviews", "query": f'"{name}" 1 estrela 2 estrelas reclamação', "max_results": 5},

        # Reddit Brasil
        {"source": "reddit", "query": f'site:reddit.com {name} reclamação problema ruim', "max_results": 5},
        {"source": "reddit", "query": f'reddit {name} cuidado golpe enganação', "max_results": 5},

        # Fóruns e comunidades
        {"source": "forum", "query": f'"{name}" experiência negativa fórum', "max_results": 5},
        {"source": "forum", "query": f'"{competitor_domain}" reclamação problema cuidado', "max_results": 5},

        # Twitter/X
        {"source": "twitter", "query": f'"{name}" reclamação insatisfeito decepcionado', "max_results": 5},

        # Procon / Consumidor.gov
        {"source": "procon", "query": f'site:consumidor.gov.br "{name}"', "max_results": 3},
    ]
    return queries


def categorize_complaint(text: str) -> list[str]:
    """Categoriza uma reclamação textual nos grupos definidos."""
    text_lower = text.lower()
    categories = []
    for cat, terms in COMPLAINT_CATEGORIES.items():
        if any(term in text_lower for term in terms):
            categories.append(cat)
    return categories if categories else ["outros"]


def extract_complaint_patterns(results: list[dict]) -> dict:
    """
    Analisa os resultados de busca e extrai padrões de reclamação.
    results: lista de resultados do Tavily com title, content, url
    """
    patterns = {cat: [] for cat in COMPLAINT_CATEGORIES}
    patterns["outros"] = []
    total = 0

    for r in results:
        text = f"{r.get('title','')} {r.get('content','')}"
        cats = categorize_complaint(text)
        total += 1
        for cat in cats:
            snippet = text[:300].strip()
            patterns[cat].append({
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "snippet": snippet,
                "score": r.get("score", 0),
            })

    # Calcular distribuição percentual
    distribution = {}
    for cat, items in patterns.items():
        if items:
            pct = round(len(items) / max(total, 1) * 100)
            distribution[cat] = {"count": len(items), "percent": pct, "items": items[:3]}

    return {"total_found": total, "distribution": distribution}


def calculate_reputation_score(patterns: dict) -> int:
    """
    Score de reputação 0-100 baseado na quantidade e severidade das reclamações.
    100 = excelente reputação (poucos problemas)
    0   = reputação péssima (muitos problemas graves)
    """
    total = patterns.get("total_found", 0)
    dist = patterns.get("distribution", {})

    if total == 0:
        return 85  # sem dados = assumir neutro-positivo

    # Penalizações por categoria (algumas são mais graves)
    penalties = {
        "prazo_entrega": 8,
        "suporte_atendimento": 10,
        "qualidade_resultado": 15,
        "preco_cobranca": 12,
        "pos_venda": 7,
        "tecnico_plataforma": 5,
        "outros": 2,
    }

    base = 100
    for cat, data in dist.items():
        count = data.get("count", 0)
        penalty = penalties.get(cat, 3)
        base -= min(count * penalty, 30)  # máximo 30 pontos por categoria

    # Penalização adicional por volume total
    if total > 20:
        base -= 10
    elif total > 10:
        base -= 5

    return max(0, min(100, base))


def generate_copy_suggestions(patterns: dict, competitor_name: str) -> list[dict]:
    """Gera sugestões de copy de vendas baseadas nas fraquezas do concorrente."""
    dist = patterns.get("distribution", {})
    suggestions = []

    # Ordenar por frequência
    sorted_cats = sorted(dist.items(), key=lambda x: x[1].get("count", 0), reverse=True)

    for cat, data in sorted_cats[:3]:  # top 3 categorias
        if cat in COPY_ANGLES and data.get("count", 0) >= 2:
            angle = COPY_ANGLES[cat][0]  # primeiro ângulo
            pct = data.get("percent", 0)
            suggestions.append({
                "category": cat,
                "frequency": f"{pct}% das reclamações",
                "copy_angle": angle.replace("{rival}", competitor_name),
                "priority": "🔴 Alta" if pct > 40 else ("🟡 Média" if pct > 20 else "🟢 Baixa"),
            })

    return suggestions


def analyze(competitor_domain: str, competitor_name: str = "", tavily_client=None) -> dict:
    """
    Ponto de entrada. Executa análise completa de reputação do concorrente.
    """
    if not tavily_client:
        return {"status": "skipped", "reason": "Tavily não configurado"}

    name = competitor_name or competitor_domain.replace(".com.br","").replace(".com","").title()
    print(f"  🕵️ Detetive de Reclamações: {name}")

    queries = build_search_queries(competitor_domain, name)
    all_results = []

    sources_checked = set()
    for q in queries:
        source = q["source"]
        if source in sources_checked:
            continue  # uma query por fonte para economizar créditos

        print(f"     → {source}...", end=" ", flush=True)
        try:
            results = tavily_client.search(
                q["query"],
                max_results=q["max_results"],
                search_depth="basic",
                include_domains=_source_domains(source),
            )
            items = results.get("results", [])
            for item in items:
                item["source"] = source
            all_results.extend(items)
            print(f"{len(items)} resultado(s)")
        except Exception as e:
            print(f"erro: {str(e)[:40]}")

        sources_checked.add(source)

    patterns = extract_complaint_patterns(all_results)
    reputation_score = calculate_reputation_score(patterns)
    copy_suggestions = generate_copy_suggestions(patterns, name)

    # Insight principal
    top_complaint = ""
    if patterns["distribution"]:
        top_cat = max(patterns["distribution"].items(), key=lambda x: x[1]["count"])
        top_pct = top_cat[1]["percent"]
        top_complaint = f"{top_pct}% das reclamações são sobre {_cat_label(top_cat[0])}"

    result = {
        "status": "ok",
        "competitor": competitor_domain,
        "competitor_name": name,
        "fetched_at": datetime.now().isoformat(),
        "reputation_score": reputation_score,
        "reputation_label": _rep_label(reputation_score),
        "total_complaints_found": patterns["total_found"],
        "top_complaint": top_complaint,
        "distribution": patterns["distribution"],
        "copy_suggestions": copy_suggestions,
    }

    # Cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"complaints-{competitor_domain}-{datetime.now().strftime('%Y-%m-%d')}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def to_markdown(results: list[dict]) -> str:
    """Gera seção Markdown do Módulo 5 para múltiplos concorrentes."""
    lines = ["## MÓDULO 5 — DETETIVE DE RECLAMAÇÕES", ""]

    for r in results:
        if r.get("status") == "skipped":
            lines.append(f"status: skipped — {r.get('reason')}")
            continue

        name = r.get("competitor_name", r.get("competitor", ""))
        score = r.get("reputation_score", 0)
        label = r.get("reputation_label", "")
        total = r.get("total_complaints_found", 0)
        top = r.get("top_complaint", "")

        lines.append(f"### {name} — Score de Reputação: {score}/100 {label}")
        lines.append("")
        if top:
            lines.append(f"> {top} (fonte: Tavily)")
        lines.append("")

        dist = r.get("distribution", {})
        if dist:
            lines.append("| Categoria | Menções | % | Exemplo |")
            lines.append("|---|---|---|---|")
            for cat, data in sorted(dist.items(), key=lambda x: x[1]["count"], reverse=True):
                example = data["items"][0]["snippet"][:80] + "..." if data["items"] else "—"
                lines.append(f"| {_cat_label(cat)} | {data['count']} | {data['percent']}% | {example} |")
            lines.append("")

        suggestions = r.get("copy_suggestions", [])
        if suggestions:
            lines.append("#### 🎯 Copy Sugerido (explorar fraquezas)")
            lines.append("")
            for s in suggestions:
                lines.append(f"**{s['priority']} — {_cat_label(s['category'])}** ({s['frequency']})")
                lines.append(f"> {s['copy_angle']}")
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _source_domains(source: str) -> list[str]:
    domains = {
        "reclame_aqui": ["reclameaqui.com.br"],
        "reddit":       ["reddit.com"],
        "procon":       ["consumidor.gov.br", "procon.sp.gov.br"],
        "twitter":      ["twitter.com", "x.com"],
    }
    return domains.get(source, [])


def _cat_label(cat: str) -> str:
    labels = {
        "prazo_entrega":      "Prazo / Entrega",
        "suporte_atendimento":"Suporte / Atendimento",
        "qualidade_resultado":"Qualidade / Resultado",
        "preco_cobranca":     "Preço / Cobrança",
        "pos_venda":          "Pós-venda",
        "tecnico_plataforma": "Técnico / Plataforma",
        "outros":             "Outros",
    }
    return labels.get(cat, cat)


def _rep_label(score: int) -> str:
    if score >= 80: return "✅ Boa reputação"
    if score >= 60: return "🟡 Reputação moderada"
    if score >= 40: return "🟠 Reputação problemática"
    return "🔴 Reputação crítica"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Complaint Detective — Módulo 5")
    parser.add_argument("--competitor", required=True, help="Domínio do concorrente")
    parser.add_argument("--name", default="", help="Nome comercial do concorrente")
    args = parser.parse_args()

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    except Exception:
        client = None

    result = analyze(args.competitor, args.name, client)
    print(json.dumps(result, ensure_ascii=False, indent=2))
