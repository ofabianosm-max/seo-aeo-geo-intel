# Especificação de Output — Markdown Estruturado

## Contrato de Formato

Este documento define o formato exato do Markdown gerado pela skill.
É um contrato entre a skill e o agente downstream que consome o relatório.

---

## Estrutura do Arquivo

```
relatorio-[YYYY-MM-DD]-[dominio]-[modo].md

Exemplos:
  relatorio-2026-02-24-seunegocio.com.br-full.md
  relatorio-2026-02-24-seunegocio.com.br-delta.md
  relatorio-2026-02-24-rival1.com.br-competitor.md
```

---

## Template Completo — Modo `full`

```markdown
---
skill: seo-aeo-geo-intel
versao: 2.2
modo: full
site: seunegocio.com.br
data: 2026-02-24
periodo_analise_inicio: 2026-01-25
periodo_analise_fim: 2026-02-24
modulos_executados: [1,2,3,4,5,6,7,8,9,10,11,12,13,15]
modulos_pulados:
  - id: 14
    motivo: "Ahrefs e Semrush não configurados"
  - id: 16
    motivo: "Nicho não-local detectado"
tempo_execucao_segundos: 187
baseline_anterior: 2026-02-17
---

# Relatório de Inteligência Digital — seunegocio.com.br
**Data:** 2026-02-24 | **Período:** 2026-01-25 a 2026-02-24

---

## EXECUTIVE SUMMARY

| Dimensão | Score Atual | Score Anterior | Δ |
|---|---|---|---|
| SEO | 73/100 | 68/100 | +5 ↑ |
| AEO | 41/100 | 41/100 | 0 → |
| GEO | 29/100 | 25/100 | +4 ↑ |
| Técnico | 61/100 | N/D | — |
| Reputação | 82/100 | 82/100 | 0 → |

**Principal oportunidade:** [1 frase]
**Principal alerta:** [1 frase]
**Ação prioritária:** [1 frase]

---

## PAGESPEED INSIGHTS

### Scores (fonte: PageSpeed API — dados reais Google)

| Categoria | Mobile | Desktop |
|---|---|---|
| Performance | 94/100 🏆 | 98/100 🏆 |
| Acessibilidade | 88/100 ✅ | 88/100 ✅ |
| Boas Práticas | 100/100 🏆 | 100/100 🏆 |
| SEO Básico | 100/100 🏆 | 100/100 🏆 |

### Core Web Vitals — Lab Data

| Métrica | Mobile | Desktop | Status |
|---|---|---|---|
| LCP | 1.2s | 0.8s | ✅ Bom |
| CLS | 0.02 | 0.01 | ✅ Bom |
| INP | 145ms | 90ms | ✅ Bom |
| TTFB | 320ms | 280ms | ✅ Bom |
| FCP | 0.9s | 0.6s | ✅ Bom |
| TBT | 80ms | 30ms | ✅ Bom |

### Core Web Vitals — Field Data (Usuários Reais / CrUX)

| Métrica | Status | Percentil 75 |
|---|---|---|
| LCP | ✅ Bom | 1.8s |
| CLS | ✅ Bom | 0.03 |
| INP | ✅ Bom | 180ms |

### Oportunidades de Melhoria

| Oportunidade | Economia Estimada |
|---|---|
| [oportunidade identificada] | [X]ms / [Y]KB |

### Peso da Página

| Recurso | Tamanho |
|---|---|
| Total | X KB |
| JavaScript | X KB |
| CSS | X KB |
| Imagens | X KB |
| Fontes | X KB |

---

## MÓDULO 1 — ANÁLISE SEO

### Score SEO: XX/100

[conteúdo do módulo]

---

## MÓDULO 2 — ESPIÃO DE CONCORRENTES

[conteúdo do módulo]

---

## MÓDULO 3 — KEYWORDS

### Monitor de Posições (fonte: GSC)

#### Alertas de Queda

| Keyword | Posição Anterior | Posição Atual | Δ | Clicks Perdidos Est. |
|---|---|---|---|---|
| [keyword] | [n] | [n] | [Δ] | [n]/mês |

#### Ganhos

| Keyword | Posição Anterior | Posição Atual | Δ | Clicks Ganhos Est. |
|---|---|---|---|---|
| [keyword] | [n] | [n] | [Δ] | [n]/mês |

### Oportunidades (posições 8-20, alto volume)

| Keyword | Posição | Volume Est. | Intenção | Ação |
|---|---|---|---|---|

### Novas Keywords Descobertas

| Keyword | Volume Est. | Dificuldade | Intenção | Fonte |
|---|---|---|---|---|

---

[... demais módulos na sequência numérica ...]

---

## MÓDULO 4 — PLANO DE AÇÃO

### Sprint 1 — Quick Wins (Semana 1-2)

| # | Ação | Impacto Estimado | Esforço | Módulo Origem |
|---|---|---|---|---|
| 🔴 1 | [ação] | [impacto] | Baixo | [módulo] |

### Sprint 2 — Crescimento (Semana 3-6)

| # | Ação | Impacto Estimado | Esforço | Módulo Origem |
|---|---|---|---|---|

### Sprint 3 — Autoridade (Semana 7-12)

| # | Ação | Impacto Estimado | Esforço | Módulo Origem |
|---|---|---|---|---|

---

## METADADOS DE EXECUÇÃO

```json
{
  "skill_version": "2.2",
  "execution_date": "2026-02-24T14:32:11-03:00",
  "execution_duration_seconds": 187,
  "data_sources": {
    "gsc": {
      "status": "ok",
      "property": "sc-domain:seunegocio.com.br",
      "data_range": "2026-01-25/2026-02-24",
      "queries_fetched": 847
    },
    "tavily": {
      "status": "ok",
      "searches_used": 31,
      "extracts_used": 14,
      "cache_hits": 6
    },
    "pagespeed": {
      "status": "ok",
      "urls_tested": 3,
      "strategies": ["mobile", "desktop"]
    },
    "ahrefs": {
      "status": "skipped",
      "reason": "API key não configurada"
    }
  },
  "modules_executed": [1,2,3,4,5,6,7,8,9,10,11,12,13,15],
  "modules_skipped": [
    {"id": 14, "reason": "Ahrefs e Semrush não configurados"},
    {"id": 16, "reason": "Nicho não-local detectado"}
  ],
  "competitors_analyzed": ["rival1.com.br","rival2.com.br"],
  "warnings": [
    "rival2.com.br: crawl parcial — robots.txt restritivo",
    "Módulo 13: análise de links internos baseada em amostra (top 50 páginas)"
  ]
}
```
```

---

## Template — Modo `delta`

Menor, foca apenas no que mudou desde o baseline.

```markdown
---
skill: seo-aeo-geo-intel
versao: 2.2
modo: delta
site: seunegocio.com.br
data: 2026-02-24
periodo_delta: 7d
baseline_data: 2026-02-17
---

# Update Semanal — seunegocio.com.br
**Semana:** 2026-02-17 a 2026-02-24

---

## ALERTAS

🔴 CRÍTICO — [descrição do alerta]
🟡 ALTO — [descrição do alerta]

## GANHOS

🎉 [descrição do ganho]

## NOVAS KEYWORDS

| Keyword | Volume Est. | Ação Sugerida |
|---|---|---|

## MUDANÇAS COMPETITIVAS

[mudanças detectadas em concorrentes]

## SEM MUDANÇAS RELEVANTES

Scores SEO/AEO/GEO, benchmark de preços e tech stack sem alterações.

---

## METADADOS DE EXECUÇÃO

```json
{ "modo": "delta", "baseline_data": "2026-02-17", ... }
```
```

---

## Template — Modo `competitor`

Dossiê completo de um concorrente específico.

```markdown
---
skill: seo-aeo-geo-intel
versao: 2.2
modo: competitor
site_analisado: rival1.com.br
site_referencia: seunegocio.com.br
data: 2026-02-24
---

# Dossiê Competitivo — rival1.com.br
vs seunegocio.com.br | 2026-02-24

---

## RESUMO EXECUTITVO

[pontos mais importantes em 5 linhas]

## TECH STACK
[módulo 7]

## RECLAMAÇÕES
[módulo 5]

## ISCAS
[módulo 6]

## POSICIONAMENTO
[módulo 10]

## CANAIS
[módulo 11]

## OPORTUNIDADES IDENTIFICADAS

| Oportunidade | Tipo | Prioridade |
|---|---|---|
| [oportunidade] | [tipo] | 🔴🟡🟢 |
```

---

## Convenções Semânticas (contrato com agente downstream)

### Identificadores de bloco

| Padrão | Significado para o agente |
|---|---|
| `## MÓDULO N —` | Início de módulo (N = número, sempre maiúsculo) |
| `## PAGESPEED INSIGHTS` | Seção PageSpeed (sempre antes dos módulos) |
| `## EXECUTIVE SUMMARY` | Resumo executivo (sempre primeiro após frontmatter) |
| `## MÓDULO 4 — PLANO DE AÇÃO` | Sempre o último módulo antes dos metadados |
| `## METADADOS DE EXECUÇÃO` | Sempre o último bloco, contém JSON |

### Prefixos de severidade

| Prefixo | Significado |
|---|---|
| `🔴 CRÍTICO` | Ação imediata — impacto alto |
| `🟡 ALTO` | Próximo sprint |
| `🟢 MÉDIO` | Backlog |
| `⚪ BAIXO` | Nice-to-have |
| `🏆` | Oportunidade competitiva de destaque |
| `🎯` | Sugestão de ação ou copy pronto |
| `🎉` | Ganho positivo |

### Fontes de dados

| Sufixo | Significado |
|---|---|
| `(fonte: GSC)` | Dado real do Google Search Console |
| `(fonte: Tavily)` | Dado coletado via Tavily |
| `(fonte: PageSpeed API)` | Dado real da PageSpeed Insights API |
| `(fonte: Ahrefs)` | Dado da Ahrefs API |
| `(estimado)` | Estimativa — não dado verificado |
| `N/D` | Não disponível — não foi possível coletar |
| `status: skipped` | Módulo não executado |

### Scores

Sempre no formato `XX/100`. Nunca `XX%` ou `0.XX`.

### Valores monetários

Sempre `R$ X.XXX` ou `R$ X.XXX,XX`. Nunca sem o símbolo.

### Datas

Sempre ISO 8601: `YYYY-MM-DD`. Em texto corrido: "24 de fevereiro de 2026".

### Deltas

Sempre `+N ↑` ou `-N ↓` ou `0 →`. Nunca só o número.
