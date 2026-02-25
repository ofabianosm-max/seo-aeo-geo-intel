#!/usr/bin/env python3
"""
lead_magnet_spy.py — Módulo 6
Detecta e analisa lead magnets de concorrentes (ebooks, ferramentas,
webinars, checklists, auditorias, templates).
Identifica gaps de mercado para criar isca superior.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

LEAD_MAGNET_TYPES = {
    "ebook":      ["ebook", "e-book", "guia completo", "guia definitivo", "livro digital", "pdf grátis"],
    "checklist":  ["checklist", "lista de verificação", "lista completa", "planilha"],
    "template":   ["template", "modelo", "kit de templates", "pack de"],
    "ferramenta": ["ferramenta gratuita", "calculadora", "simulador", "gerador", "tool"],
    "webinar":    ["webinar", "aula gratuita", "masterclass", "workshop gratuito", "treinamento grátis"],
    "auditoria":  ["auditoria gratuita", "diagnóstico gratuito", "análise gratuita", "consultoria grátis"],
    "minicurso":  ["minicurso", "mini-curso", "curso grátis", "email course"],
    "quiz":       ["quiz", "teste gratuito", "descubra seu", "qual é o seu"],
    "comunidade": ["grupo vip", "comunidade grátis", "discord", "telegram vip"],
    "trial":      ["teste grátis", "trial", "30 dias grátis", "7 dias grátis", "experimente grátis"],
}

FORMAT_VALUE = {
    "ebook":      {"effort": "baixo", "perceived_value": "médio"},
    "checklist":  {"effort": "muito baixo", "perceived_value": "baixo"},
    "template":   {"effort": "baixo", "perceived_value": "médio-alto"},
    "ferramenta": {"effort": "alto", "perceived_value": "muito alto"},
    "webinar":    {"effort": "médio", "perceived_value": "alto"},
    "auditoria":  {"effort": "alto", "perceived_value": "muito alto"},
    "minicurso":  {"effort": "médio", "perceived_value": "alto"},
    "quiz":       {"effort": "médio", "perceived_value": "médio"},
    "comunidade": {"effort": "médio", "perceived_value": "alto"},
    "trial":      {"effort": "alto", "perceived_value": "muito alto"},
}


def classify_lead_magnet(text: str) -> tuple[str, str]:
    """Classifica o tipo de lead magnet e extrai o título/promessa."""
    text_lower = text.lower()
    for lm_type, keywords in LEAD_MAGNET_TYPES.items():
        if any(kw in text_lower for kw in keywords):
            # Tentar extrair o título/promessa
            title_match = re.search(
                r'(?:baixe|acesse|garanta|receba|pegue|obtenha|download)\s+(?:grátis|gratuitamente|agora)?\s*[:\-]?\s*["""]?(.{15,80})["""]?',
                text, re.IGNORECASE
            )
            title = title_match.group(1).strip() if title_match else text[:80].strip()
            return lm_type, title
    return "outro", text[:80].strip()


def extract_cta_quality(text: str) -> dict:
    """Avalia a qualidade do CTA (Call to Action) da isca."""
    has_urgency = bool(re.search(r"(?:vagas limitadas|por tempo limitado|últimas|últimas horas|encerra em)", text, re.IGNORECASE))
    has_social_proof = bool(re.search(r"\d+\s*(?:pessoas?|profissionais?|empresas?|downloads?|alunos?)", text, re.IGNORECASE))
    has_specific_benefit = len(text) > 30 and any(v in text.lower() for v in ["aprenda","descubra","aumente","reduza","evite","gere"])

    score = sum([has_urgency, has_social_proof, has_specific_benefit]) * 33
    return {
        "has_urgency": has_urgency,
        "has_social_proof": has_social_proof,
        "has_specific_benefit": has_specific_benefit,
        "quality_score": score,
        "quality_label": "🏆 Alta" if score >= 66 else ("✅ Média" if score >= 33 else "🔴 Baixa"),
    }


def analyze(competitor_domain: str, competitor_name: str = "", tavily_client=None) -> dict:
    """Encontra e analisa as iscas de um concorrente."""
    if not tavily_client:
        return {"status": "skipped", "reason": "Tavily não configurado", "domain": competitor_domain}

    domain = competitor_domain.replace("https://","").replace("http://","").split("/")[0]
    name = competitor_name or domain.replace(".com.br","").replace(".com","").title()

    print(f"  🎣 Iscas: {name}", end=" ", flush=True)

    queries = [
        f'site:{domain} (ebook OR checklist OR template OR "grátis" OR "gratuito" OR webinar OR auditoria)',
        f'"{name}" isca digital lead magnet material gratuito',
    ]

    magnets_found = []
    for query in queries:
        try:
            results = tavily_client.search(query, max_results=5, search_depth="basic")
            for r in results.get("results", []):
                text = f"{r.get('title','')} {r.get('content','')}"
                lm_type, title = classify_lead_magnet(text)
                if lm_type != "outro" or any(kw in text.lower() for kw in ["grát","download","baixe"]):
                    cta = extract_cta_quality(text)
                    val = FORMAT_VALUE.get(lm_type, {"effort": "N/D", "perceived_value": "N/D"})
                    magnets_found.append({
                        "type": lm_type,
                        "title": title[:100],
                        "url": r.get("url",""),
                        "cta_quality": cta,
                        "effort_to_create": val["effort"],
                        "perceived_value": val["perceived_value"],
                    })
        except Exception:
            pass

    # Deduplicar por tipo + título similar
    seen = set()
    unique_magnets = []
    for m in magnets_found:
        key = f"{m['type']}:{m['title'][:30]}"
        if key not in seen:
            seen.add(key)
            unique_magnets.append(m)

    print(f"{len(unique_magnets)} iscas encontradas")

    # Resumo por tipo
    by_type = {}
    for m in unique_magnets:
        by_type.setdefault(m["type"], []).append(m)

    result = {
        "status": "ok",
        "domain": domain,
        "name": name,
        "fetched_at": datetime.now().isoformat(),
        "total_magnets": len(unique_magnets),
        "by_type": {k: len(v) for k, v in by_type.items()},
        "magnets": unique_magnets[:10],
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"iscas-{domain}-{datetime.now().strftime('%Y-%m-%d')}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def identify_gaps(results: list[dict]) -> list[str]:
    """Identifica formatos de isca não explorados pelos concorrentes."""
    used_types = set()
    for r in results:
        for t in r.get("by_type", {}).keys():
            used_types.add(t)

    high_value_unused = []
    for lm_type, val in FORMAT_VALUE.items():
        if lm_type not in used_types and val["perceived_value"] in ("alto", "muito alto"):
            high_value_unused.append({
                "type": lm_type,
                "label": f"🏆 Nenhum concorrente tem {lm_type} — valor percebido: {val['perceived_value']}",
            })

    return high_value_unused


def to_markdown(results: list[dict]) -> str:
    lines = ["## MÓDULO 6 — ESPIÃO DE ISCAS DIGITAIS", ""]

    all_valid = [r for r in results if r.get("status") == "ok"]

    # Tabela resumo
    lines.append("### Inventário de Iscas (fonte: Tavily)")
    lines.append("")
    lines.append("| Concorrente | Total | Tipos Usados | Melhor CTA |")
    lines.append("|---|---|---|---|")
    for r in all_valid:
        types_str = ", ".join(r.get("by_type", {}).keys()) or "Nenhuma detectada"
        best = max(r.get("magnets", []), key=lambda x: x.get("cta_quality",{}).get("quality_score",0), default={})
        best_label = best.get("cta_quality",{}).get("quality_label","—")
        lines.append(f"| {r['name']} | {r['total_magnets']} | {types_str} | {best_label} |")

    lines.append("")

    # Gaps
    gaps = identify_gaps(all_valid)
    if gaps:
        lines.append("### 🏆 Oportunidades de Isca")
        lines.append("")
        for g in gaps:
            lines.append(f"**{g['label']}**")
        lines.append("")

    # Melhor isca de cada concorrente
    lines.append("### Melhores Iscas Detectadas")
    lines.append("")
    for r in all_valid:
        if r.get("magnets"):
            best = max(r["magnets"], key=lambda x: x.get("cta_quality",{}).get("quality_score",0))
            lines.append(f"**{r['name']}** — `{best['type']}` | Valor percebido: {best['perceived_value']}")
            lines.append(f"> {best['title']}")
            lines.append(f"> CTA: {best['cta_quality']['quality_label']}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor", required=True)
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    except Exception:
        client = None

    result = analyze(args.competitor, args.name, client)
    print(json.dumps(result, ensure_ascii=False, indent=2))
