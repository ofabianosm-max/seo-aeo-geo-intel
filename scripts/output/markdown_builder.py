#!/usr/bin/env python3
"""
markdown_builder.py
Monta o relatório final em Markdown estruturado a partir dos dados
coletados por todos os módulos. É o único ponto de saída da skill.

Segue a especificação definida em references/output-spec.md.
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(os.getenv("SEO_SKILL_OUTPUT_DIR", "./reports"))


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _fmt_score(score) -> str:
    if score is None:
        return "N/D"
    s = int(score)
    if s >= 90: return f"{s}/100 🏆"
    if s >= 75: return f"{s}/100 ✅"
    if s >= 50: return f"{s}/100 🟡"
    if s >= 25: return f"{s}/100 🔴"
    return f"{s}/100 💀"


def _fmt_delta(curr, prev) -> str:
    if curr is None or prev is None:
        return "N/D"
    delta = curr - prev
    if delta > 0:   return f"+{delta} ↑"
    if delta < 0:   return f"{delta} ↓"
    return "0 →"


def _severity_order(issue: dict) -> int:
    sev = issue.get("severity", "")
    if "CRÍTICO" in sev: return 0
    if "ALTO"    in sev: return 1
    if "MÉDIO"   in sev: return 2
    return 3


def _today() -> str:
    return date.today().isoformat()


# ──────────────────────────────────────────
# Seções do relatório
# ──────────────────────────────────────────

def _build_frontmatter(ctx: dict) -> str:
    site       = ctx.get("site", "")
    modo       = ctx.get("mode", "full")
    modules    = ctx.get("modules_executed", [])
    skipped    = ctx.get("modules_skipped", [])
    start_date = ctx.get("start_date", "")
    end_date   = ctx.get("end_date", _today())
    baseline   = ctx.get("baseline_date", "")

    skip_block = ""
    if skipped:
        lines = []
        for s in skipped:
            if isinstance(s, dict):
                lines.append(f"  - id: {s['id']}\n    motivo: \"{s['reason']}\"")
            else:
                lines.append(f"  - id: {s}")
        skip_block = "modulos_pulados:\n" + "\n".join(lines)
    else:
        skip_block = "modulos_pulados: []"

    baseline_line = f"baseline_anterior: {baseline}" if baseline else ""

    return f"""---
skill: seo-aeo-geo-intel
versao: "2.2"
modo: {modo}
site: {site}
data: {_today()}
periodo_analise_inicio: {start_date}
periodo_analise_fim: {end_date}
modulos_executados: {json.dumps(modules)}
{skip_block}
{baseline_line}
---"""


def _build_header(ctx: dict) -> str:
    site  = ctx.get("site", "")
    start = ctx.get("start_date", "")
    end   = ctx.get("end_date", _today())
    return (
        f"# Relatório de Inteligência Digital — {site}\n"
        f"**Data:** {_today()} | **Período:** {start} a {end}\n"
    )


def _build_executive_summary(ctx: dict) -> str:
    scores = ctx.get("scores", {})
    prev   = ctx.get("scores_previous", {})

    def row(label, key):
        curr  = scores.get(key)
        p     = prev.get(key)
        delta = _fmt_delta(curr, p) if p else "—"
        return f"| {label} | {_fmt_score(curr)} | {_fmt_score(p)} | {delta} |"

    lines = [
        "## EXECUTIVE SUMMARY", "",
        "| Dimensão | Score Atual | Score Anterior | Δ |",
        "|---|---|---|---|",
        row("SEO",       "seo"),
        row("AEO",       "aeo"),
        row("GEO",       "geo"),
        row("Técnico",   "technical"),
        row("Reputação", "reputation"),
        "",
        f"**Principal oportunidade:** {ctx.get('main_opportunity', 'N/D')}",
        f"**Principal alerta:** {ctx.get('main_alert', 'N/D')}",
        f"**Ação prioritária:** {ctx.get('priority_action', 'N/D')}",
    ]
    return "\n".join(lines)


def _build_pagespeed(data: dict) -> str:
    if not data or data.get("status") == "skipped":
        return (
            "## PAGESPEED INSIGHTS\n\n"
            "> ⏭️ Pulado — PAGESPEED_API_KEY não configurada.\n"
        )

    # Importar formatter do módulo collector
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from pagespeed_fetcher import to_markdown
        return to_markdown(data)
    except ImportError:
        return "## PAGESPEED INSIGHTS\n\n> Dados disponíveis mas formatter não encontrado.\n"


def _build_seo_analysis(data: dict) -> str:
    if not data:
        return "## MÓDULO 1 — ANÁLISE SEO\n\n> ⏭️ Pulado — GSC não configurado.\n"

    score   = data.get("seo_score", 0)
    issues  = sorted(data.get("issues", []), key=_severity_order)
    queries = data.get("top_queries", [])

    lines = [
        f"## MÓDULO 1 — ANÁLISE SEO", "",
        f"### Score SEO: {_fmt_score(score)}", "",
    ]

    if issues:
        lines += ["### Issues Identificados", ""]
        for issue in issues[:10]:
            lines.append(f"{issue.get('severity','⚪')} — {issue.get('message','')}")
            if issue.get("action"):
                lines.append(f"  → Ação: {issue['action']}")
        lines.append("")

    if queries:
        lines += [
            "### Top 10 Páginas por Tráfego (fonte: GSC)", "",
            "| URL | Clicks | Impressões | CTR | Posição Média |",
            "|---|---|---|---|---|",
        ]
        for q in queries[:10]:
            url  = q.get("url", q.get("query", ""))[:55]
            cl   = q.get("clicks", 0)
            imp  = q.get("impressions", 0)
            ctr  = f"{q.get('ctr', 0):.1f}%"
            pos  = q.get("position", 0)
            lines.append(f"| {url} | {cl} | {imp} | {ctr} | {pos} |")
        lines.append("")

    return "\n".join(lines)


def _build_complaints(data: dict) -> str:
    if not data:
        return "## MÓDULO 5 — DETETIVE DE RECLAMAÇÕES\n\n> ⏭️ Pulado.\n"

    lines = ["## MÓDULO 5 — DETETIVE DE RECLAMAÇÕES", ""]

    for competitor, comp_data in data.items():
        rep_score = comp_data.get("reputation_score", 0)
        lines.append(f"### {competitor} — Score de Reputação: {_fmt_score(rep_score)}")
        lines.append("")

        categories = comp_data.get("categories", {})
        total = comp_data.get("total_complaints", 0)
        if total > 0:
            lines += [
                "| Categoria | Ocorrências | % do total |",
                "|---|---|---|",
            ]
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                if count > 0:
                    pct = round(count / total * 100)
                    lines.append(f"| {cat.replace('_',' ').title()} | {count} | {pct}% |")
            lines.append("")

        snippets = comp_data.get("snippets", [])
        if snippets:
            lines.append("**Reclamações Representativas:**")
            lines.append("")
            for s in snippets[:3]:
                lines.append(f"> \"{s.get('snippet','')[:200]}\"")
                lines.append(f"> — *{s.get('source','')}*")
                lines.append("")

        top_cat = comp_data.get("top_category")
        if top_cat:
            lines.append(
                f"🎯 **Oportunidade:** Principal falha de `{competitor}` é "
                f"`{top_cat.replace('_',' ')}`. Use isso como diferencial direto no seu copy."
            )
            lines.append("")

    return "\n".join(lines)


def _build_tech_stack(data: dict) -> str:
    if not data:
        return "## MÓDULO 7 — RAIO-X TECNOLÓGICO\n\n> ⏭️ Pulado.\n"

    lines = ["## MÓDULO 7 — RAIO-X TECNOLÓGICO", "",
             "### Stack por Empresa", "",
             "| Empresa | Framework / CMS | CDN | PageSpeed Mobile | Classificação |",
             "|---|---|---|---|---|"]

    for site, d in data.items():
        detected = d.get("detected", {})
        cms_fw   = next((k for k in ["nextjs","nuxtjs","gatsby","astro","react",
                                      "vue","svelte","angular","wordpress","wix",
                                      "webflow","squarespace","framer","shopify"]
                         if k in detected), "N/D")
        cdn_name = next((k for k in ["cloudflare","vercel","netlify","fastly","aws","azure"]
                         if k in detected), "Não detectado")
        ps_score = d.get("pagespeed_mobile", "N/D")
        classif  = d.get("classification", "N/D")
        lines.append(f"| {site} | {cms_fw} | {cdn_name} | {ps_score} | {classif} |")

    lines += ["", "### Plataformas de Anúncios Detectadas", ""]
    for site, d in data.items():
        ads = d.get("ad_platforms", [])
        if ads:
            lines.append(f"**{site}:** {', '.join(ads)}")

    lines.append("")
    return "\n".join(lines)


def _build_prices(data: dict) -> str:
    if not data:
        return "## MÓDULO 8 — BENCHMARK DE PREÇOS\n\n> ⏭️ Pulado.\n"

    lines = ["## MÓDULO 8 — BENCHMARK DE PREÇOS", "",
             "### Preços Encontrados (fonte: Tavily)", ""]

    competitors = data.get("competitors", {})
    if not competitors:
        lines.append("> Nenhum preço publicado encontrado nos sites analisados.")
        lines.append("")
        return "\n".join(lines)

    lines += ["| Empresa | Preços Identificados |",
              "|---|---|"]
    for comp, comp_data in competitors.items():
        prices = comp_data.get("prices_found", [])
        if prices:
            lines.append(f"| {comp} | {' | '.join(prices[:5])} |")
        else:
            lines.append(f"| {comp} | Não publicado |")

    lines += ["",
              "🎯 **Gap identificado:** Verifique se algum concorrente não publica preços — ",
              "isso pode indicar venda consultiva ou preço alto que não suporta comparação direta.",
              ""]

    return "\n".join(lines)


def _build_keywords(gsc_data: dict) -> str:
    if not gsc_data:
        return "## KEYWORDS\n\n> ⏭️ Pulado — GSC não configurado.\n"

    lines = ["## KEYWORDS", ""]

    # Monitor de posições
    changes = gsc_data.get("changes", {})
    drops   = changes.get("drops", [])
    gains   = changes.get("gains", [])
    new_q   = changes.get("new_queries", [])

    if drops:
        lines += ["### ⚠️ Alertas de Queda (fonte: GSC)", "",
                  "| Keyword | Posição Anterior | Posição Atual | Δ | Clicks Perdidos Est. |",
                  "|---|---|---|---|---|"]
        for d in drops[:10]:
            lines.append(
                f"| {d['query']} | {d['position_prev']} | "
                f"{d['position_curr']} | +{d['delta']} ↓ | "
                f"~{d.get('clicks_lost_est',0)}/mês |"
            )
        lines.append("")

    if gains:
        lines += ["### 🎉 Ganhos de Posição (fonte: GSC)", "",
                  "| Keyword | Posição Anterior | Posição Atual | Δ |",
                  "|---|---|---|---|"]
        for g in gains[:10]:
            lines.append(
                f"| {g['query']} | {g['position_prev']} | "
                f"{g['position_curr']} | -{g['delta']} ↑ |"
            )
        lines.append("")

    # Oportunidades
    opps = gsc_data.get("opportunities", {})
    opp_zone = opps.get("opportunity_zone", [])
    if opp_zone:
        lines += ["### 🎯 Zona de Oportunidade — Posições 8-20 (fonte: GSC)", "",
                  "| Keyword | Posição | Impressões/mês | CTR | Ação |",
                  "|---|---|---|---|---|"]
        for o in opp_zone[:15]:
            acao = "Otimizar post existente" if o.get("clicks", 0) > 0 else "Criar conteúdo"
            lines.append(
                f"| {o['query']} | {o['position']} | "
                f"{o['impressions']} | {o['ctr']}% | {acao} |"
            )
        lines.append("")

    if new_q:
        lines += ["### 🆕 Novas Keywords Detectadas (fonte: GSC)", "",
                  "| Keyword | Posição | Impressões/mês | Clicks |",
                  "|---|---|---|---|"]
        for q in new_q[:10]:
            lines.append(
                f"| {q['query']} | {q['position']} | "
                f"{q['impressions']} | {q['clicks']} |"
            )
        lines.append("")

    return "\n".join(lines)


def _build_action_plan(ctx: dict) -> str:
    actions = ctx.get("action_plan", {})
    if not actions:
        # Gerar plano básico baseado nos issues coletados
        return _generate_default_plan(ctx)

    lines = ["## MÓDULO 4 — PLANO DE AÇÃO", ""]

    sprint_config = [
        ("sprint_1", "Sprint 1 — Quick Wins (Semana 1-2)"),
        ("sprint_2", "Sprint 2 — Crescimento (Semana 3-6)"),
        ("sprint_3", "Sprint 3 — Autoridade e GEO (Semana 7-12)"),
    ]

    for sprint_key, sprint_label in sprint_config:
        sprint_items = actions.get(sprint_key, [])
        if not sprint_items:
            continue
        lines += [f"### {sprint_label}", "",
                  "| # | Ação | Impacto Estimado | Esforço | Módulo Origem |",
                  "|---|---|---|---|---|"]
        for i, item in enumerate(sprint_items, 1):
            sev    = item.get("severity", "🟢")
            action = item.get("action", "")
            impact = item.get("impact", "—")
            effort = item.get("effort", "Médio")
            module = item.get("module", "—")
            lines.append(f"| {sev} {i} | {action} | {impact} | {effort} | {module} |")
        lines.append("")

    return "\n".join(lines)


def _generate_default_plan(ctx: dict) -> str:
    """Gera plano de ação básico a partir dos issues coletados."""
    all_issues = ctx.get("all_issues", [])
    critical = [i for i in all_issues if "CRÍTICO" in i.get("severity", "")]
    high     = [i for i in all_issues if "ALTO"    in i.get("severity", "")]
    medium   = [i for i in all_issues if "MÉDIO"   in i.get("severity", "")]

    lines = ["## MÓDULO 4 — PLANO DE AÇÃO", ""]

    if critical:
        lines += ["### Sprint 1 — Quick Wins (Semana 1-2)", "",
                  "| # | Ação | Esforço |",
                  "|---|---|---|"]
        for i, issue in enumerate(critical[:5], 1):
            action = issue.get("action", issue.get("message", ""))
            lines.append(f"| 🔴 {i} | {action} | Baixo-Médio |")
        lines.append("")

    if high:
        lines += ["### Sprint 2 — Crescimento (Semana 3-6)", "",
                  "| # | Ação | Esforço |",
                  "|---|---|---|"]
        for i, issue in enumerate(high[:5], 1):
            action = issue.get("action", issue.get("message", ""))
            lines.append(f"| 🟡 {i} | {action} | Médio |")
        lines.append("")

    if medium:
        lines += ["### Sprint 3 — Autoridade (Semana 7-12)", "",
                  "| # | Ação | Esforço |",
                  "|---|---|---|"]
        for i, issue in enumerate(medium[:5], 1):
            action = issue.get("action", issue.get("message", ""))
            lines.append(f"| 🟢 {i} | {action} | Médio-Alto |")
        lines.append("")

    return "\n".join(lines)


def _build_execution_metadata(ctx: dict) -> str:
    meta = {
        "skill_version":        "2.2",
        "execution_date":       datetime.now().isoformat(),
        "execution_duration_seconds": ctx.get("duration_seconds", 0),
        "data_sources":         ctx.get("data_sources", {}),
        "modules_executed":     ctx.get("modules_executed", []),
        "modules_skipped":      ctx.get("modules_skipped", []),
        "competitors_analyzed": ctx.get("competitors_analyzed", []),
        "warnings":             ctx.get("warnings", []),
    }
    return (
        "## METADADOS DE EXECUÇÃO\n\n"
        "```json\n"
        + json.dumps(meta, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


# ──────────────────────────────────────────
# Builder principal
# ──────────────────────────────────────────

def build(ctx: dict, output_path: Path = None) -> str:
    """
    Monta o relatório completo a partir do contexto de dados.

    ctx esperado:
      site, mode, start_date, end_date, scores, scores_previous,
      modules_executed, modules_skipped, data_sources, warnings,
      competitors_analyzed, duration_seconds,
      main_opportunity, main_alert, priority_action,
      action_plan, all_issues,

      # Dados por módulo:
      pagespeed_data, seo_data, complaints_data, tech_data,
      prices_data, gsc_data
    """
    mode = ctx.get("mode", "full")

    if mode == "delta":
        report = _build_delta(ctx)
    elif mode == "competitor":
        report = _build_competitor(ctx)
    else:
        report = _build_full(ctx)

    # Salvar
    if output_path is None:
        site_clean = ctx.get("site", "unknown").replace("https://", "").replace("/", "-")
        filename   = f"relatorio-{_today()}-{site_clean}-{mode}.md"
        output_path = OUTPUT_DIR / filename

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"✅ Relatório salvo em: {output_path}", file=sys.stderr)
    return report


def _build_full(ctx: dict) -> str:
    sections = [
        _build_frontmatter(ctx),
        "",
        _build_header(ctx),
        "---",
        "",
        _build_executive_summary(ctx),
        "---",
        "",
        _build_pagespeed(ctx.get("pagespeed_data", {})),
        "---",
        "",
        _build_seo_analysis(ctx.get("seo_data", {})),
        "---",
        "",
        _build_complaints(ctx.get("complaints_data", {})),
        "---",
        "",
        _build_tech_stack(ctx.get("tech_data", {})),
        "---",
        "",
        _build_prices(ctx.get("prices_data", {})),
        "---",
        "",
        _build_keywords(ctx.get("gsc_data", {})),
        "---",
        "",
        _build_action_plan(ctx),
        "---",
        "",
        _build_execution_metadata(ctx),
    ]
    return "\n".join(sections)


def _build_delta(ctx: dict) -> str:
    site       = ctx.get("site", "")
    baseline   = ctx.get("baseline_date", "")
    changes    = ctx.get("gsc_data", {}).get("changes", {})
    drops      = changes.get("drops", [])
    gains      = changes.get("gains", [])
    new_q      = changes.get("new_queries", [])
    competitor_changes = ctx.get("competitor_changes", [])

    lines = [
        _build_frontmatter(ctx), "",
        f"# Update Semanal — {site}",
        f"**Semana:** {baseline} a {_today()}",
        "", "---", "",
    ]

    if drops:
        lines.append("## ALERTAS")
        lines.append("")
        for d in drops[:5]:
            lines.append(
                f"🔴 CRÍTICO — \"{d['query']}\" caiu posição "
                f"{d['position_prev']} → {d['position_curr']} "
                f"(~{d.get('clicks_lost_est',0)} clicks/mês perdidos)"
            )
        lines.append("")

    if competitor_changes:
        if "## ALERTAS" not in "\n".join(lines):
            lines.append("## ALERTAS")
            lines.append("")
        for c in competitor_changes:
            lines.append(f"🟡 ALTO — {c}")
        lines.append("")

    if gains:
        lines.append("## GANHOS")
        lines.append("")
        for g in gains[:5]:
            lines.append(
                f"🎉 \"{g['query']}\" subiu posição "
                f"{g['position_prev']} → {g['position_curr']}"
            )
        lines.append("")

    if new_q:
        lines += [
            "## NOVAS KEYWORDS (fonte: GSC)", "",
            "| Keyword | Posição | Impressões/mês | Ação Sugerida |",
            "|---|---|---|---|",
        ]
        for q in new_q[:8]:
            acao = "Criar conteúdo" if q.get("clicks", 0) < 5 else "Otimizar"
            lines.append(f"| {q['query']} | {q['position']} | {q['impressions']} | {acao} |")
        lines.append("")

    if not drops and not gains and not new_q and not competitor_changes:
        lines.append("## SEM ALTERAÇÕES RELEVANTES")
        lines.append("")
        lines.append("Scores, keywords e concorrentes sem mudanças significativas nesta semana.")
        lines.append("")

    lines += ["---", "", _build_execution_metadata(ctx)]
    return "\n".join(lines)


def _build_competitor(ctx: dict) -> str:
    competitor = ctx.get("competitor_site", ctx.get("site", ""))
    reference  = ctx.get("reference_site", "")

    header = (
        f"# Dossiê Competitivo — {competitor}\n"
        f"vs {reference} | {_today()}\n" if reference else
        f"# Dossiê Competitivo — {competitor}\n"
        f"Data: {_today()}\n"
    )

    sections = [
        _build_frontmatter(ctx), "",
        header,
        "---", "",
        _build_tech_stack(ctx.get("tech_data", {})),
        "---", "",
        _build_complaints(ctx.get("complaints_data", {})),
        "---", "",
        _build_prices(ctx.get("prices_data", {})),
        "---", "",
        _build_execution_metadata(ctx),
    ]
    return "\n".join(sections)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Markdown Report Builder")
    parser.add_argument("--data",   required=True, help="Path para JSON com contexto")
    parser.add_argument("--output", help="Path de output do .md (opcional)")
    parser.add_argument("--stdout", action="store_true", help="Imprimir na stdout também")
    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as f:
        ctx = json.load(f)

    output_path = Path(args.output) if args.output else None
    report = build(ctx, output_path)

    if args.stdout:
        print(report)
