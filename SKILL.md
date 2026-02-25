---
name: seo-aeo-geo-intel
description: >
  Skill completa de inteligência digital e SEO. Use sempre que o usuário mencionar
  SEO, AEO, GEO, ranqueamento no Google, análise de site, auditoria de SEO, espionar
  concorrentes, benchmark competitivo, palavras-chave, keyword research, tráfego orgânico,
  Google Search Console, PageSpeed, Core Web Vitals, reclamações de concorrentes,
  tech stack de concorrentes, preços de concorrentes, novos entrantes no mercado,
  posicionamento de marca, canais de aquisição, links internos, backlinks, conteúdo
  desatualizado, canibalização de keywords, local SEO, Google Business Profile,
  ou qualquer variação de "meu site não aparece no Google", "quero mais tráfego",
  "o que meus concorrentes fazem", "que conteúdo devo criar". Ative também quando
  o usuário perguntar como aparecer no ChatGPT, Perplexity ou outros sistemas de IA.
  Esta skill SEMPRE gera output em Markdown estruturado para consumo por agentes downstream.
---

# Skill — SEO · AEO · GEO · Intelligence

## Visão Geral

Esta skill coleta dados reais via APIs (GSC, Tavily, PageSpeed) e entrega relatórios
em Markdown estruturado e semântico. O agente downstream decide o formato de apresentação.

**APIs utilizadas:**
- Google Search Console API — dados reais de performance do site
- Tavily API — crawl, análise de conteúdo e inteligência competitiva
- Google PageSpeed Insights API — métricas de performance reais (grátis)
- Ahrefs ou Semrush API — backlinks (opcional)

---

## PASSO 1 — ONBOARDING (sempre executar se config ausente)

Antes de qualquer análise, verificar se as integrações estão configuradas.
Ler o arquivo `references/onboarding.md` para o protocolo completo.

### Lógica de onboarding

```
1. Verificar existência de cada credencial (env vars ou config file)
2. Para cada credencial ausente:
   a. Informar o que é e para que serve
   b. Dar link de onde obter
   c. Perguntar: "Deseja configurar agora ou pular?"
   d. Se pular: registrar como skipped e continuar
   e. Se configurar: testar conexão antes de salvar
3. Ao final: mostrar resumo do que está ativo e o que foi pulado
4. Informar quais módulos ficarão indisponíveis pelos skips
```

### Classificação das integrações

| Integração | Tipo | Impacto se ausente |
|---|---|---|
| `TAVILY_API_KEY` | Obrigatória | Módulos 2,5,6,7,8,9,10,11,13,15,16 indisponíveis |
| `GSC_CREDENTIALS` | Obrigatória | Módulos 1,3,9,12,13,15 indisponíveis |
| `PAGESPEED_API_KEY` | Recomendada | Performance com dados reais indisponível |
| `AHREFS_API_KEY` | Opcional | Módulo 14 (backlinks) indisponível |
| `SEMRUSH_API_KEY` | Opcional | Módulo 14 alternativo indisponível |

### Mensagem de onboarding (template)

```
🔧 CONFIGURAÇÃO INICIAL — seo-aeo-geo-intel

Vou verificar o que está disponível para executar a análise completa.

[✅ ou ❌] Tavily API         → [status]
[✅ ou ❌] Google Search Console → [status]
[✅ ou ❌] PageSpeed API      → [status]
[⚙️ opcional] Ahrefs API     → [status]
[⚙️ opcional] Semrush API    → [status]

[Se houver itens ausentes:]
Itens ausentes: X
Deseja configurar agora? Posso guiar cada um.
Ou prefere pular e rodar com o que está disponível?
```

### Relatório de cobertura (após onboarding)

Sempre informar quais módulos vão rodar e quais serão pulados:

```
📊 Cobertura desta execução:
✅ Módulos ativos (12/16): 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15
⏭️  Pulados por integração ausente:
   • Módulo 9 (Radar de Entrantes) — requer GSC
   • Módulo 13 (Links Internos) — requer GSC
   • Módulo 14 (Backlinks) — requer Ahrefs ou Semrush
   • Módulo 16 (Local SEO) — nicho não-local detectado
```

---

## PASSO 2 — DETECTAR MODO DE EXECUÇÃO

Com base na solicitação do usuário, identificar qual modo executar:

| Gatilho do usuário | Modo | Módulos |
|---|---|---|
| "Analise meu site X" / análise completa | `full` | Todos disponíveis |
| "Atualize" / "o que mudou" / "monitoramento" | `delta` | 3 + comparação com baseline |
| "Espione [concorrente]" / "analise concorrente" | `competitor` | 2, 5, 6, 7, 10, 11 |
| "Keywords" / "palavras-chave" / "que conteúdo criar" | `keywords` | 3, 15d |
| "Reclamações" / "o que falam dos concorrentes" | `sentiment` | 5 |
| "Preços" / "quanto cobram" / "benchmark" | `pricing` | 8 |
| "Performance" / "PageSpeed" / "site lento" | `performance` | 7, 12e, PageSpeed |
| "Técnico" / "auditoria técnica" / "indexação" | `technical` | 12, 13 |
| "Local" / "Google Meu Negócio" / "GBP" | `local` | 16 |
| "Backlinks" / "quem linka" | `backlinks` | 14 |
| "Novos concorrentes" / "entrantes" | `radar` | 9 |

---

## PASSO 3 — EXECUÇÃO DOS MÓDULOS

Para detalhes de cada módulo, ler o reference correspondente.
Executar apenas os módulos do modo selecionado + os que têm integrações disponíveis.

### Módulos e seus references

| Módulo | Reference | Quando carregar |
|---|---|---|
| 1 — SEO+AEO+GEO | `references/seo-aeo-geo.md` | Modo full ou análise do site |
| 2 — Spy Concorrentes | `references/competitor-spy.md` | Modo full ou competitor |
| 3 — Keywords | `references/keyword-discovery.md` | Modo full, delta ou keywords |
| 5 — Reclamações | `references/complaint-detective.md` | Modo full, competitor ou sentiment |
| 6 — Iscas | `references/lead-magnet-spy.md` | Modo full ou competitor |
| 7 — Tech Stack | `references/tech-stack-radar.md` | Modo full, competitor ou performance |
| 8 — Preços | `references/price-benchmark.md` | Modo full, competitor ou pricing |
| 9 — Radar | `references/new-entrant-radar.md` | Modo full ou radar |
| 10 — Posicionamento | `references/positioning-analysis.md` | Modo full ou competitor |
| 11 — Canais | `references/ads-channel-map.md` | Modo full ou competitor |
| 12 — SEO Técnico | `references/seo-tecnico.md` | Modo full ou technical |
| 13 — Links Internos | `references/internal-links.md` | Modo full ou technical |
| 14 — Backlinks | `references/backlinks.md` | Modo backlinks (se API disponível) |
| 15 — Saúde Conteúdo | `references/content-health.md` | Modo full, delta ou keywords |
| 16 — Local SEO | `references/local-seo.md` | Modo full ou local (se nicho local) |

### Scripts disponíveis

Executar via bash quando necessário:

```bash
# Coletar dados do GSC
python scripts/gsc_fetcher.py --site SITE --days 30

# Coletar dados do PageSpeed (mobile + desktop)
python scripts/pagespeed_fetcher.py --url URL --strategy both

# Análise via Tavily (crawl ou search)
python scripts/tavily_fetcher.py --mode [search|extract] --query QUERY

# Análise técnica (robots, sitemap, redirects)
python scripts/crawl_analyzer.py --site SITE

# Detector de tech stack
python scripts/tech_stack_detector.py --url URL

# Detetive de reclamações
python scripts/complaint_detective.py --competitor DOMAIN

# Monitor de preços
python scripts/price_monitor.py --competitors DOMAIN1,DOMAIN2

# Radar de novos entrantes
python scripts/new_entrant_radar.py --keywords "kw1,kw2" --site SITE

# Análise de saúde do conteúdo
python scripts/content_health.py --site SITE

# Local SEO
python scripts/local_seo_analyzer.py --business-name NAME --city CITY

# Backlinks (requer Ahrefs ou Semrush)
python scripts/backlink_fetcher.py --site SITE --competitors DOMAIN1,DOMAIN2

# Gerar relatório Markdown final
python scripts/output/markdown_builder.py --data DATA_JSON --output reports/
```

---

## PASSO 4 — GERAR OUTPUT MARKDOWN

**Regra absoluta:** todo output é Markdown estruturado. Nunca entregar dados brutos ou
formatação ad-hoc. Sempre seguir a especificação em `references/output-spec.md`.

### Estrutura obrigatória do arquivo gerado

```
relatorio-[YYYY-MM-DD]-[dominio]-[modo].md
```

**Ordem das seções:**
1. YAML frontmatter (metadados)
2. Executive Summary
3. PageSpeed Insights (se disponível)
4. Módulos executados (na ordem numérica)
5. Keywords
6. Plano de Ação (sempre ao final)
7. Bloco JSON de metadados de execução

### Convenções semânticas obrigatórias

```
🔴 CRÍTICO    → ação imediata (impacto alto, esforço baixo-médio)
🟡 ALTO       → próximo sprint
🟢 MÉDIO      → backlog
⚪ BAIXO      → nice-to-have
🏆            → oportunidade competitiva de destaque
🎯            → sugestão de ação ou copy
(fonte: GSC)  → dado real do Google Search Console
(fonte: Tavily) → dado coletado via Tavily
(estimado)    → estimativa — não dado exato
N/D           → não disponível / não foi possível coletar
status: skipped → módulo não executado (motivo declarado)
```

### Relatório delta (modo monitoramento)

Quando `modo = delta`, gerar relatório menor com apenas o que mudou.
Ver template completo em `references/output-spec.md`.

---

## PASSO 5 — SALVAR BASELINE

Após cada execução completa (`modo = full`), salvar os dados como baseline para
comparações futuras (modo delta). Salvar em `cache/baseline-[dominio].json`.

---

## Regras Gerais

1. **Nunca inventar dados.** Se não foi possível coletar, usar `N/D`.
2. **Sempre declarar a fonte** de cada dado: GSC, Tavily, PageSpeed ou estimado.
3. **Onboarding sempre primeiro** — nunca tentar executar sem verificar integrações.
4. **Skip gracioso** — módulo sem integração disponível: registrar como skipped, continuar.
5. **Transparência sobre cobertura** — informar sempre quais módulos rodaram e quais não.
6. **Baseline automático** — salvar após cada full run para habilitar modo delta.
7. **Modo local é condicional** — ativar apenas se nicho local detectado ou usuário pedir.
8. **Módulo 14 é opcional** — nunca bloquear execução pela ausência de Ahrefs/Semrush.
