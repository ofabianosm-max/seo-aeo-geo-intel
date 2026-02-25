# seo-aeo-geo-intel

> Skill de inteligência digital para SEO, AEO e GEO — com espionagem competitiva completa.

Coleta dados reais via Google Search Console, PageSpeed Insights API e Tavily, analisa seu site e seus concorrentes, e entrega relatórios em Markdown estruturado para consumo por agentes downstream.

---

## O que faz

**16 módulos de análise:**

| # | Módulo | APIs |
|---|---|---|
| 1 | Análise SEO + AEO + GEO | GSC + Tavily + PageSpeed |
| 2 | Espião de Concorrentes | Tavily + PageSpeed |
| 3 | Monitoramento de Keywords | GSC |
| 4 | Plano de Ação Priorizado | — |
| 5 | Detetive de Reclamações | Tavily |
| 6 | Espião de Iscas Digitais | Tavily |
| 7 | Raio-X Tecnológico | Tavily + PageSpeed |
| 8 | Benchmark de Preços | Tavily |
| 9 | Radar de Novos Entrantes | GSC + Tavily |
| 10 | Análise de Posicionamento | Tavily |
| 11 | Mapa de Canais e Anúncios | Tavily |
| 12 | SEO Técnico (Crawl & Indexação) | GSC + Tavily + PageSpeed |
| 13 | Arquitetura e Links Internos | GSC + Tavily |
| 14 | Backlinks *(opcional)* | Ahrefs ou Semrush |
| 15 | Saúde do Conteúdo | GSC + Tavily |
| 16 | Local SEO *(condicional)* | GSC + Tavily |

---

## Instalação

```bash
git clone https://github.com/SEU_USUARIO/seo-aeo-geo-intel.git
cd seo-aeo-geo-intel

pip install tavily-python google-auth google-auth-oauthlib \
            google-api-python-client requests python-dotenv pandas
```

### Configurar credenciais

```bash
cp .env.example .env
# editar .env com suas chaves
```

Mínimo para começar (análise de concorrentes):
```
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
```

Setup recomendado (análise completa):
```
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
GSC_SERVICE_ACCOUNT_JSON=/path/to/credentials.json
PAGESPEED_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
```

### Verificar integrações

```bash
python scripts/check_integrations.py
```

---

## Uso

```bash
# Análise completa do seu site
python scripts/run_analysis.py --site seunegocio.com.br

# Análise de performance (PageSpeed + Core Web Vitals)
python scripts/run_analysis.py --site seunegocio.com.br --mode performance

# Dossiê de um concorrente específico
python scripts/run_analysis.py --site seunegocio.com.br --mode competitor --target rival.com.br

# Atualização semanal (só o que mudou)
python scripts/run_analysis.py --site seunegocio.com.br --mode delta

# Auditoria técnica de SEO
python scripts/run_analysis.py --site seunegocio.com.br --mode technical

# Com concorrentes específicos
python scripts/run_analysis.py --site seunegocio.com.br --competitors rival1.com.br,rival2.com.br
```

O relatório é salvo em `reports/relatorio-YYYY-MM-DD-dominio-modo.md`.

Consulte [`USAGE.md`](USAGE.md) para todos os comandos e casos de uso.

---

## Estrutura

```
seo-aeo-geo-intel/
├── SKILL.md                    # Instruções para o agente de IA
├── USAGE.md                    # Guia de uso completo
├── .env.example                # Template de configuração
├── references/
│   ├── onboarding.md           # Guia de configuração de cada API
│   ├── output-spec.md          # Especificação do formato Markdown de saída
│   └── modules.md              # Documentação detalhada dos módulos
├── scripts/
│   ├── run_analysis.py         # ← ponto de entrada principal
│   ├── check_integrations.py   # health check das APIs
│   ├── pagespeed_fetcher.py    # Google PageSpeed Insights API
│   ├── gsc_fetcher.py          # Google Search Console API
│   ├── tavily_fetcher.py       # Tavily API (crawl + busca)
│   ├── complaint_detective.py  # Módulo 5 — reclamações
│   ├── lead_magnet_spy.py      # Módulo 6 — iscas digitais
│   ├── tech_stack_detector.py  # Módulo 7 — tech stack
│   ├── price_monitor.py        # Módulo 8 — benchmark de preços
│   ├── new_entrant_radar.py    # Módulo 9 — novos concorrentes
│   ├── competitor_intel.py     # Módulos 10+11 — posicionamento e canais
│   ├── crawl_analyzer.py       # Módulo 12 — SEO técnico
│   ├── internal_link_analyzer.py # Módulo 13 — links internos
│   ├── backlink_fetcher.py     # Módulo 14 — backlinks (opcional)
│   ├── content_health.py       # Módulo 15 — saúde do conteúdo
│   ├── local_seo_analyzer.py   # Módulo 16 — Local SEO
│   └── output/
│       └── markdown_builder.py # montador do relatório final
└── docs/
    └── PRD-v2.2.md             # Product Requirements Document
```

---

## APIs utilizadas

| API | Tipo | Plano mínimo |
|---|---|---|
| [Tavily](https://tavily.com) | Busca e extração web | Gratuito (1.000/mês) |
| [Google Search Console](https://search.google.com/search-console) | Performance do site | Gratuito |
| [Google PageSpeed Insights](https://developers.google.com/speed/docs/insights/v5/get-started) | Performance real | Gratuito (25.000 req/dia) |
| [Ahrefs](https://ahrefs.com) | Backlinks | Advanced (~$449/mês) — opcional |
| [Semrush](https://semrush.com) | Backlinks | Guru+ — opcional |

---

## Output

Todo relatório é Markdown estruturado, pronto para ser consumido por um agente downstream que decide o formato de apresentação final (PDF, email, Slack, Notion, etc.).

Formato do arquivo: `reports/relatorio-YYYY-MM-DD-dominio-modo.md`

Consulte [`references/output-spec.md`](references/output-spec.md) para a especificação completa do formato.

---

## Versão

**v2.2** — Fevereiro 2026
- 16 módulos de análise
- Google PageSpeed Insights API integrada
- 5 módulos de SEO técnico (Módulos 12–16)
- Onboarding interativo com skip gracioso
- Modo delta para monitoramento semanal leve

Histórico completo: [`docs/PRD-v2.2.md`](docs/PRD-v2.2.md)
