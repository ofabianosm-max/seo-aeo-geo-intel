# PRD — Skill SEO · AEO · GEO · Intelligence
**Product Requirements Document — Versão 2.2**
Fevereiro 2026 | Revisão: +5 módulos SEO técnico + Google PageSpeed Insights API

---

## 🧭 Índice Rápido

| # | Módulo | APIs Necessárias | ROI |
|---|---|---|---|
| 1 | Análise do Site (SEO+AEO+GEO) | GSC + Tavily + PageSpeed | Médio |
| 2 | Espião de Concorrentes | Tavily + PageSpeed | Médio |
| 3 | Monitoramento de Keywords | GSC | Médio |
| 4 | Plano de Ação Priorizado | — | Alto |
| 5 | 🕵️ Detetive de Reclamações | Tavily | 🔥 Alto |
| 6 | 🎣 Espião de Iscas | Tavily | Médio |
| 7 | ⚡ Raio-X Tecnológico | Tavily + **PageSpeed** | 🔥 Alto |
| 8 | 💰 Benchmark de Preços | Tavily | 🔥 Alto |
| 9 | 🚨 Radar de Novos Entrantes | GSC + Tavily | Médio |
| 10 | 🧠 Análise de Posicionamento | Tavily | Alto |
| 11 | 📣 Mapa de Canais e Anúncios | Tavily | Alto |
| **12** | **🔬 SEO Técnico (Crawl & Indexação)** | **GSC + Tavily** | **🔥 Alto** |
| **13** | **🕸️ Arquitetura e Links Internos** | **GSC + Tavily** | **Alto** |
| **14** | **🔗 Backlinks** | **Ahrefs/Semrush (opcional)** | **Alto** |
| **15** | **📉 Saúde do Conteúdo** | **GSC + Tavily** | **🔥 Alto** |
| **16** | **📍 Local SEO** | **GSC + Tavily (opcional)** | **Alto** |

---

## NOVO — Google PageSpeed Insights API

### Por que API dedicada e não só Tavily?

O Módulo 7 (Raio-X Tecnológico) já coletava dados de PageSpeed via Tavily extract, mas de forma limitada e indireta. Com a **PageSpeed Insights API oficial do Google**, ganhamos:

| Capacidade | Tavily (antes) | PageSpeed API (agora) |
|---|---|---|
| Score 0-100 | ✅ Estimado | ✅ Real (dado oficial Google) |
| Core Web Vitals | ⚠️ Parcial | ✅ Completo (LCP, CLS, FID, INP, TTFB) |
| Lab data vs Field data | ❌ | ✅ Ambos separados |
| Mobile vs Desktop | ❌ | ✅ Estratégias separadas |
| Oportunidades de melhoria | ❌ | ✅ Lista detalhada com impacto estimado |
| Diagnósticos técnicos | ❌ | ✅ Detalhados |
| CrUX data (usuários reais) | ❌ | ✅ Chrome User Experience Report |
| Análise de recursos (JS/CSS/img) | ❌ | ✅ Por arquivo, com tamanho e savings |
| Gratuita | ✅ | ✅ (25.000 req/dia) |

### Configuração

```bash
# Chave gratuita em: https://developers.google.com/speed/docs/insights/v5/get-started
PAGESPEED_API_KEY=AIzaSy...
```

**Endpoint:**
```
GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed
  ?url={URL}
  &strategy={mobile|desktop}
  &category={performance|accessibility|best-practices|seo}
  &key={API_KEY}
```

### Onde a PageSpeed API é usada

```
Módulo 1  → Score de performance do seu site (mobile + desktop)
Módulo 2  → Comparar performance vs concorrentes
Módulo 7  → Raio-X Tecnológico (dado real, não estimado)
Módulo 12 → SEO Técnico (auditoria completa de performance)
```

### Estrutura de dados coletados

```python
PAGESPEED_METRICS = {
    # Scores (0-100)
    "performance_score":      int,   # Score geral
    "accessibility_score":    int,   # Acessibilidade
    "best_practices_score":   int,   # Boas práticas
    "seo_score":              int,   # SEO básico

    # Core Web Vitals — Lab Data (Lighthouse)
    "lcp_seconds":            float, # Largest Contentful Paint
    "cls_score":              float, # Cumulative Layout Shift
    "fid_ms":                 int,   # First Input Delay
    "inp_ms":                 int,   # Interaction to Next Paint (novo)
    "ttfb_ms":                int,   # Time to First Byte
    "fcp_seconds":            float, # First Contentful Paint
    "tbt_ms":                 int,   # Total Blocking Time
    "speed_index":            float, # Speed Index

    # Core Web Vitals — Field Data (CrUX — usuários reais)
    "field_lcp_status":       str,   # good | needs-improvement | poor
    "field_cls_status":       str,
    "field_inp_status":       str,
    "field_fcp_status":       str,

    # Oportunidades de melhoria (com saving estimado)
    "opportunities": [
        {
            "id":             str,   # ex: "render-blocking-resources"
            "title":          str,   # ex: "Eliminar recursos que bloqueiam renderização"
            "savings_ms":     int,   # tempo economizável em ms
            "savings_bytes":  int,   # bytes economizáveis
        }
    ],

    # Diagnósticos
    "diagnostics": [
        {
            "id":             str,
            "title":          str,
            "display_value":  str,
        }
    ],

    # Recursos analisados
    "total_bytes":            int,   # peso total da página
    "js_bytes":               int,
    "css_bytes":              int,
    "image_bytes":            int,
    "font_bytes":             int,
}
```

### Classificação automática de performance

```python
def classify_performance(score: int) -> str:
    if score >= 90: return "🏆 Elite (90-100)"
    if score >= 75: return "✅ Boa (75-89)"
    if score >= 50: return "🟡 Melhorar (50-74)"
    return "🔴 Crítica (0-49)"

def classify_cwv(metric: str, value: float) -> str:
    thresholds = {
        "lcp":  {"good": 2.5,  "poor": 4.0},   # segundos
        "cls":  {"good": 0.1,  "poor": 0.25},   # score
        "fid":  {"good": 100,  "poor": 300},     # ms
        "inp":  {"good": 200,  "poor": 500},     # ms
        "ttfb": {"good": 800,  "poor": 1800},    # ms
        "fcp":  {"good": 1.8,  "poor": 3.0},     # segundos
    }
    t = thresholds[metric]
    if value <= t["good"]: return "✅ Bom"
    if value <= t["poor"]: return "⚠️ Melhorar"
    return "🔴 Ruim"
```

### Output da PageSpeed no Markdown

```markdown
## PAGESPEED INSIGHTS — seunegocio.com.br

### Scores (fonte: PageSpeed API — dados reais Google)

| Categoria | Mobile | Desktop |
|---|---|---|
| Performance | 94/100 🏆 | 98/100 🏆 |
| Acessibilidade | 88/100 ✅ | 88/100 ✅ |
| Boas Práticas | 100/100 🏆 | 100/100 🏆 |
| SEO Básico | 100/100 🏆 | 100/100 🏆 |

### Core Web Vitals — Lab Data (Lighthouse)

| Métrica | Mobile | Desktop | Status Mobile |
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
| FCP | ✅ Bom | 1.1s |

### Oportunidades de Melhoria

| Oportunidade | Economia Estimada |
|---|---|
| Nenhuma crítica identificada | — |

### Peso da Página

| Recurso | Tamanho |
|---|---|
| Total | 420 KB |
| JavaScript | 180 KB |
| CSS | 45 KB |
| Imagens | 160 KB |
| Fontes | 35 KB |
```

---

## Módulo 12 — 🔬 SEO Técnico (Crawl & Indexação)

### O que cobre

Toda a infraestrutura que determina se o Google consegue rastrear, entender e indexar o site corretamente. Um site com SEO técnico ruim não ranqueia independente do conteúdo.

### Fontes de dados

```
GSC API  → erros de cobertura, sitemaps, inspeção de URLs
Tavily   → crawl de robots.txt, sitemap XML, headers HTTP
PageSpeed API → performance + sinais técnicos de SEO
```

### Sub-módulos

#### 12a. Rastreabilidade

```python
CRAWL_CHECKS = {
    "robots_txt": {
        "existe": bool,
        "bloqueia_css_js": bool,       # erro comum — bloquear recursos
        "bloqueia_paginas_importantes": bool,
        "tem_sitemap_declarado": bool,
        "conteudo_raw": str,
    },
    "sitemap": {
        "existe": bool,
        "url": str,
        "total_urls": int,
        "urls_noindex": int,           # URLs noindex no sitemap (erro!)
        "urls_redirect": int,          # redirects no sitemap (erro!)
        "urls_404": int,               # 404s no sitemap (erro!)
        "ultima_modificacao": date,
        "sitemap_imagens": bool,
        "sitemap_videos": bool,
    },
    "redirect_chains": [
        {
            "url_origem": str,
            "cadeia": list[str],       # ex: A → B → C → D (ruim)
            "status_final": int,
            "profundidade": int,       # > 2 = problema
        }
    ],
}
```

#### 12b. Cobertura de Indexação (via GSC)

```python
INDEXING_COVERAGE = {
    "indexadas": int,
    "excluidas": int,
    "erros": int,
    "avisos": int,

    "razoes_exclusao": {
        "noindex_tag": int,
        "redirecionado": int,
        "canonico_alternativo": int,
        "bloqueado_robots": int,
        "pagina_404": int,
        "soft_404": int,
        "descoberta_nao_indexada": int,  # rastreada mas não indexada (sinal ruim)
        "crawl_anomaly": int,
    }
}
```

#### 12c. Canonical e Duplicate Content

```python
CANONICAL_CHECKS = {
    "paginas_sem_canonical": int,
    "canonicals_apontando_para_noindex": int,   # erro grave
    "canonicals_em_redirect": int,              # erro
    "paginas_canonico_nao_self": int,           # pode ser intencional
    "duplicatas_suspeitas": [
        {
            "url_a": str,
            "url_b": str,
            "similaridade": float,   # 0-1
        }
    ],
}
```

#### 12d. HTTPS e Segurança

```python
SECURITY_CHECKS = {
    "https_ativo": bool,
    "certificado_valido": bool,
    "certificado_expira_em_dias": int,
    "mixed_content": bool,              # HTTP assets em página HTTPS
    "hsts_ativo": bool,
    "http_redireciona_para_https": bool,
    "www_redireciona_corretamente": bool,
}
```

#### 12e. Performance Técnica (via PageSpeed API)

```python
PERFORMANCE_CHECKS = {
    "mobile_score": int,
    "desktop_score": int,
    "cwv_aprovados_mobile": bool,
    "cwv_aprovados_desktop": bool,
    "oportunidades": list[dict],        # da PageSpeed API
    "peso_total_kb": int,
    "js_kb": int,
    "imagens_kb": int,
}
```

### Output

```markdown
## MÓDULO 12 — SEO TÉCNICO

### Score Técnico: 61/100

| Sub-módulo | Score | Issues |
|---|---|---|
| Rastreabilidade | 15/20 | robots.txt bloqueia /assets/ |
| Cobertura de Indexação | 12/25 | 47 páginas "descobertas mas não indexadas" |
| Canonical & Duplicatas | 18/20 | 3 pages sem canonical |
| HTTPS & Segurança | 16/20 | Mixed content em 2 páginas |
| Performance (PageSpeed) | N/A | Ver seção PageSpeed Insights |

### Issues Identificados

🔴 CRÍTICO — 47 URLs "descobertas mas não indexadas" no GSC
  → Causa provável: thin content ou bloqueio de rastreamento
  → Ação: inspecionar as 47 URLs e decidir: melhorar conteúdo ou noindex

🔴 CRÍTICO — sitemap.xml contém 12 URLs com redirect
  → Erro clássico após migração
  → Ação: regenerar sitemap com URLs finais

🟡 ALTO — robots.txt bloqueia /assets/ (CSS e JS)
  → Google não consegue renderizar as páginas corretamente
  → Ação: remover regra Disallow: /assets/

🟡 ALTO — 3 redirect chains com profundidade > 2
  → /antiga-url → /intermediaria → /url-atual → desperdiça link equity
  → Ação: redirecionar direto da origem para o destino final

🟢 MÉDIO — 3 páginas sem canonical tag
  → URLs: /pagina-a, /pagina-b, /pagina-c
  → Ação: adicionar <link rel="canonical"> em cada uma

### Cobertura de Indexação (fonte: GSC)

| Status | Quantidade |
|---|---|
| ✅ Indexadas | 284 |
| ⚠️ Descobertas, não indexadas | 47 |
| ❌ Erros | 8 |
| ➡️ Redirecionadas | 34 |
| 🚫 Excluídas por noindex | 12 |

### Sitemap

| Propriedade | Valor |
|---|---|
| URL | /sitemap.xml |
| Total de URLs | 341 |
| URLs com redirect | 12 🔴 |
| URLs 404 | 0 ✅ |
| URLs noindex | 2 🟡 |
| Última modificação | 2026-01-15 |
```

---

## Módulo 13 — 🕸️ Arquitetura e Links Internos

### O que cobre

Como o PageRank interno flui pelo site — se as páginas mais importantes recebem mais links internos, se há páginas órfãs e se a profundidade de cliques está adequada.

### Coleta de dados

```python
# Via Tavily extract: crawl das páginas principais
# Via GSC: identificar páginas com tráfego mas sem links internos

INTERNAL_LINK_ANALYSIS = {
    "paginas_orfas": [str],             # indexadas, sem link interno
    "paginas_profundidade_alta": [
        {
            "url": str,
            "cliques_do_home": int,     # > 3 = problema
        }
    ],
    "distribuicao_links": {
        "home_links_saida": int,
        "paginas_mais_linkadas": list[dict],
        "paginas_menos_linkadas": list[dict],
    },
    "anchor_text": {
        "genericos": int,               # "clique aqui", "saiba mais" = ruim
        "descritivos": int,
        "exatos": int,
    }
}
```

### Output

```markdown
## MÓDULO 13 — ARQUITETURA E LINKS INTERNOS

### Score de Arquitetura: 54/100

🔴 CRÍTICO — 23 páginas órfãs identificadas
  → Páginas indexadas e com impressões no GSC mas sem link interno apontando
  → Estão "invisíveis" para o Google em termos de PageRank
  → Ação: mapear e adicionar links internos relevantes

🟡 ALTO — 8 páginas com profundidade > 3 cliques do home
  → Google rastreia com menor frequência páginas profundas
  → Ação: adicionar links diretos da home ou seções principais

🟡 ALTO — 67% dos anchor texts são genéricos ("clique aqui", "saiba mais")
  → Anchor texts descritivos passam contexto semântico ao Google
  → Ação: revisar os 20 links mais importantes e tornar anchors descritivos

### Top 5 Páginas Mais Linkadas Internamente

| URL | Links Recebidos | Justificado? |
|---|---|---|
| /home | 0 | — (origem) |
| /servicos | 34 | ✅ |
| /blog | 28 | ✅ |
| /pagina-pouco-importante | 22 | ⚠️ Desproporcional |
| /contato | 19 | ✅ |

### Páginas Órfãs (Top 5 por impressões GSC)

| URL | Impressões/mês | Ação |
|---|---|---|
| /artigo-relevante | 1.240 | 🔴 Linkar imediatamente |
| /servico-especifico | 890 | 🔴 Linkar imediatamente |
| /caso-de-sucesso-x | 340 | 🟡 Linkar em breve |
```

---

## Módulo 14 — 🔗 Backlinks (Módulo Opcional)

### Dependência

Requer chave de API do **Ahrefs** ou **Semrush**. Se nenhuma estiver configurada, o módulo é pulado e o relatório registra `status: skipped — API key não configurada`.

```bash
# Pelo menos uma das duas:
AHREFS_API_KEY=
SEMRUSH_API_KEY=
```

### O que coleta

```python
BACKLINK_ANALYSIS = {
    # Perfil do seu site
    "seu_site": {
        "domain_rating": int,          # Ahrefs DR (0-100)
        "authority_score": int,        # Semrush AS (0-100)
        "backlinks_total": int,
        "dominios_referencia": int,
        "backlinks_dofollow": int,
        "backlinks_nofollow": int,
        "tendencia_90d": str,          # "crescendo" | "estável" | "caindo"
        "distribuicao_anchor": dict,   # branded, exato, genérico, URL nua
    },

    # Link gap vs concorrentes
    "link_gap": [
        {
            "dominio": str,            # quem linka para concorrentes mas não você
            "linka_para": list[str],   # para quais concorrentes
            "dr_do_dominio": int,
            "oportunidade": str,       # "alta" | "média" | "baixa"
        }
    ],

    # Links tóxicos
    "links_toxicos": [
        {
            "dominio": str,
            "razao": str,              # spam score alto, PBN, etc.
            "acao": str,               # "disavow" | "monitorar"
        }
    ],
}
```

### Output

```markdown
## MÓDULO 14 — BACKLINKS (fonte: Ahrefs)

### Perfil de Backlinks — seunegocio.com.br

| Métrica | Valor | vs rival1 | vs rival2 |
|---|---|---|---|
| Domain Rating | 34 | 52 (-18) | 28 (+6) |
| Domínios de referência | 87 | 134 | 61 |
| Backlinks totais | 412 | 890 | 203 |
| Tendência 90d | ↑ Crescendo | → Estável | ↓ Caindo |

### Link Gap — Top 10 Oportunidades

| Domínio | DR | Linka para | Oportunidade |
|---|---|---|---|
| autoridade-nicho.com.br | 67 | rival1, rival2 | 🏆 Alta |
| blog-referencia.com.br | 54 | rival1 | 🏆 Alta |
| portal-do-setor.com.br | 48 | rival2 | ⭐ Média |

### Links Tóxicos Detectados

| Domínio | Motivo | Ação |
|---|---|---|
| spam-site.ru | Spam score 94/100 | Disavow imediato |
```

---

## Módulo 15 — 📉 Saúde do Conteúdo

### O que cobre

Conteúdo que está perdendo ranqueamento, páginas que brigam entre si pela mesma keyword e tópicos do nicho que você ainda não cobriu.

### Sub-módulos

#### 15a. Content Decay (via GSC)

Detecta páginas com queda contínua de tráfego por 3+ meses seguidos — sinal de conteúdo desatualizado ou superado por concorrentes.

```python
CONTENT_DECAY = {
    "paginas_em_decay": [
        {
            "url": str,
            "clicks_3m_atras": int,
            "clicks_atual": int,
            "queda_percentual": float,
            "principal_keyword": str,
            "posicao_atual": float,
            "causa_provavel": str,     # "desatualizado" | "superado" | "canibalização"
        }
    ]
}
```

#### 15b. Canibalização de Keywords

Duas ou mais páginas ranqueando para a mesma keyword principal — elas brigam entre si e enfraquecem ambas.

```python
CANNIBALIZATION = {
    "grupos_canibalização": [
        {
            "keyword": str,
            "paginas_competindo": [
                {
                    "url": str,
                    "posicao": float,
                    "clicks": int,
                }
            ],
            "acao_sugerida": str,   # "consolidar" | "canonical" | "diferenciar"
        }
    ]
}
```

#### 15c. Thin Content

```python
THIN_CONTENT = {
    "paginas_thin": [
        {
            "url": str,
            "palavras_estimadas": int,   # < 300 = thin
            "indexada": bool,
            "impressoes_gsc": int,
            "acao": str,   # "melhorar" | "noindex" | "consolidar"
        }
    ]
}
```

#### 15d. Topical Authority Map

Mapeia os subtópicos do nicho que você cobre vs os que estão em branco — via Tavily (análise do nicho) + GSC (o que você já ranqueia).

```python
TOPICAL_MAP = {
    "topico_principal": str,
    "subtopicos": [
        {
            "subtopico": str,
            "cobertura_sua": str,       # "forte" | "fraca" | "ausente"
            "cobertura_rival1": str,
            "volume_estimado": int,
            "prioridade": str,
        }
    ]
}
```

### Output

```markdown
## MÓDULO 15 — SAÚDE DO CONTEÚDO

### Score de Saúde: 58/100

### Content Decay — Páginas em Queda

| URL | Clicks (3m atrás) | Clicks (atual) | Queda | Causa Provável |
|---|---|---|---|---|
| /artigo-x | 890 | 340 | -62% 🔴 | Desatualizado |
| /guia-y | 420 | 280 | -33% 🟡 | Superado por rival2 |
| /post-z | 180 | 120 | -33% 🟡 | Canibalização |

### Canibalização de Keywords

🔴 CRÍTICO — "keyword principal" aparece em 3 URLs simultaneamente
  → /pagina-a (pos. 4, 120 clicks), /pagina-b (pos. 7, 80 clicks), /pagina-c (pos. 11, 30 clicks)
  → Ação: consolidar /pagina-b e /pagina-c em /pagina-a (301 redirect)

### Thin Content

| URL | Palavras Est. | Indexada | Impressões/mês | Ação |
|---|---|---|---|---|
| /servico-x | 180 | ✅ | 340 | 🔴 Expandir conteúdo |
| /sobre-nos | 95 | ✅ | 120 | 🟡 Expandir ou noindex |
| /obrigado | 45 | ✅ | 0 | ⚪ Adicionar noindex |

### Topical Authority Map — [Nicho: X]

| Subtópico | Você | rival1 | rival2 | Volume Est. | Prioridade |
|---|---|---|---|---|---|
| subtópico A | ✅ Forte | ✅ Forte | ✅ Forte | 2.400/mês | 🟡 Melhorar |
| subtópico B | ⚠️ Fraco | ✅ Forte | ❌ Ausente | 1.800/mês | 🔴 Urgente |
| subtópico C | ❌ Ausente | ✅ Forte | ✅ Forte | 1.200/mês | 🔴 Urgente |
| subtópico D | ❌ Ausente | ❌ Ausente | ❌ Ausente | 880/mês | 🏆 Primeiro a cobrir |
```

---

## Módulo 16 — 📍 Local SEO (Módulo Condicional)

### Quando ativa

Ativa automaticamente quando o nicho tem componente local — detectado por:
- Presença de cidade/estado nas keywords do GSC
- Nicho reconhecidamente local (médico, dentista, restaurante, etc.)
- Usuário informa explicitamente

### O que analisa

```python
LOCAL_SEO = {
    # Google Business Profile
    "gbp": {
        "existe": bool,
        "nome_negocio": str,
        "categoria_principal": str,
        "categorias_secundarias": list[str],
        "endereco_completo": bool,
        "telefone": bool,
        "site_linkado": bool,
        "horarios_completos": bool,
        "fotos_quantidade": int,       # < 10 = problema
        "reviews_total": int,
        "rating_medio": float,
        "reviews_respondidos_pct": float,  # % de reviews com resposta
        "posts_recentes": bool,        # postou nos últimos 30 dias?
        "perguntas_sem_resposta": int,
    },

    # NAP Consistency
    "nap": {
        "nome": str,
        "endereco": str,
        "telefone": str,
        "inconsistencias_detectadas": list[dict],  # via Tavily: outros diretórios
    },

    # Keywords locais
    "keywords_locais": [
        {
            "keyword": str,            # "médico em [cidade]"
            "posicao": float,
            "impressoes": int,
            "em_local_pack": bool,
        }
    ],

    # Concorrentes no Local Pack
    "local_pack_concorrentes": [
        {
            "nome": str,
            "rating": float,
            "reviews": int,
            "distancia": str,
        }
    ],
}
```

### Output

```markdown
## MÓDULO 16 — LOCAL SEO

### Score Local: 47/100

### Google Business Profile

| Item | Status |
|---|---|
| Perfil existe | ✅ |
| Categoria principal | ✅ Médico Clínico Geral |
| Fotos | ⚠️ 4 fotos (recomendado: mínimo 10) |
| Reviews | ⚠️ 12 reviews — rating 4.1 |
| % Reviews respondidos | 🔴 17% (responda todos!) |
| Posts recentes | 🔴 Último post há 94 dias |
| Perguntas sem resposta | 🔴 3 perguntas abertas |

### Keywords Locais (fonte: GSC)

| Keyword | Posição | Impressões/mês | No Local Pack? |
|---|---|---|---|
| "médico em [cidade]" | 8 | 420 | ❌ |
| "clínica [bairro]" | 14 | 180 | ❌ |
| "consulta [especialidade] [cidade]" | N/D | N/D | ❌ |

### Local Pack — Concorrentes no Top 3

| Nome | Rating | Reviews | Diferença para você |
|---|---|---|---|
| Clínica Rival A | 4.8 | 89 | +0.7 rating, +77 reviews |
| Clínica Rival B | 4.6 | 54 | +0.5 rating, +42 reviews |
| Clínica Rival C | 4.3 | 23 | +0.2 rating, +11 reviews |

### Plano de Ação Local

🔴 Responder todos os 12 reviews (especialmente os negativos)
🔴 Postar 1x/semana no GBP pelos próximos 30 dias
🟡 Adicionar 10+ fotos de qualidade
🟡 Responder as 3 perguntas em aberto
🟢 Padronizar NAP em todos os diretórios
```

---

## Arquitetura Atualizada v2.2

```
seo-aeo-geo-intel/
├── SKILL.md
├── references/
│   ├── seo-checklist.md
│   ├── aeo-framework.md
│   ├── geo-framework.md
│   ├── competitor-spy.md
│   ├── keyword-discovery.md
│   ├── complaint-detective.md
│   ├── lead-magnet-spy.md
│   ├── tech-stack-radar.md
│   ├── price-benchmark.md
│   ├── new-entrant-radar.md
│   ├── positioning-analysis.md
│   ├── ads-channel-map.md
│   ├── seo-tecnico.md           ← NOVO
│   ├── internal-links.md        ← NOVO
│   ├── backlinks.md             ← NOVO
│   ├── content-health.md        ← NOVO
│   └── local-seo.md             ← NOVO
└── scripts/
    ├── gsc_fetcher.py
    ├── tavily_fetcher.py
    ├── pagespeed_fetcher.py      ← NOVO (PageSpeed Insights API)
    ├── competitor_analyzer.py
    ├── keyword_monitor.py
    ├── complaint_detective.py
    ├── tech_stack_detector.py
    ├── price_monitor.py
    ├── new_entrant_radar.py
    ├── crawl_analyzer.py         ← NOVO (Módulo 12)
    ├── internal_link_analyzer.py ← NOVO (Módulo 13)
    ├── backlink_fetcher.py       ← NOVO (Módulo 14 — opcional)
    ├── content_health.py         ← NOVO (Módulo 15)
    ├── local_seo_analyzer.py     ← NOVO (Módulo 16 — condicional)
    └── output/
        └── markdown_builder.py
```

---

## Variáveis de Ambiente Completas v2.2

```bash
# ──── APIs Obrigatórias ────
TAVILY_API_KEY=
GSC_SERVICE_ACCOUNT_JSON=
PAGESPEED_API_KEY=               # NOVO — gratuita em console.developers.google.com

# ──── APIs Opcionais ────
GSC_OAUTH_TOKEN=                 # alternativa ao service account
AHREFS_API_KEY=                  # Módulo 14 — backlinks
SEMRUSH_API_KEY=                 # Módulo 14 — alternativa ao Ahrefs

# ──── Configurações ────
SEO_SKILL_CACHE_DIR=./cache
SEO_SKILL_OUTPUT_DIR=./reports
SEO_SKILL_TIMEZONE=America/Sao_Paulo
SEO_SKILL_LANGUAGE=pt-BR
SEO_SKILL_LOCAL_SEO=auto         # "auto" | "on" | "off"
```

---

## Índice Completo de Módulos v2.2

| # | Módulo | APIs | Obrigatório | Condicional |
|---|---|---|---|---|
| 1 | Análise SEO+AEO+GEO | GSC + Tavily + PageSpeed | ✅ | — |
| 2 | Espião de Concorrentes | Tavily + PageSpeed | ✅ | — |
| 3 | Monitoramento de Keywords | GSC | ✅ | — |
| 4 | Plano de Ação | — | ✅ | — |
| 5 | Detetive de Reclamações | Tavily | ✅ | — |
| 6 | Espião de Iscas | Tavily | ✅ | — |
| 7 | Raio-X Tecnológico | Tavily + PageSpeed | ✅ | — |
| 8 | Benchmark de Preços | Tavily | ✅ | — |
| 9 | Radar de Novos Entrantes | GSC + Tavily | ✅ | — |
| 10 | Análise de Posicionamento | Tavily | ✅ | — |
| 11 | Mapa de Canais e Anúncios | Tavily | ✅ | — |
| 12 | SEO Técnico | GSC + Tavily + PageSpeed | ✅ | — |
| 13 | Arquitetura e Links Internos | GSC + Tavily | ✅ | — |
| 14 | Backlinks | Ahrefs ou Semrush | ❌ | Se API configurada |
| 15 | Saúde do Conteúdo | GSC + Tavily | ✅ | — |
| 16 | Local SEO | GSC + Tavily | ❌ | Se nicho local detectado |

---

## Backlog v3.0 (inalterado)

| Módulo Futuro | Descrição | Prioridade |
|---|---|---|
| Monitor de SERP | Screenshot do resultado de busca + detecção de mudanças de layout | Alta |
| Score E-E-A-T Avançado | Análise profunda dos sinais de autoridade | Alta |
| Tendências Emergentes | Tópicos crescendo antes de virarem keyword competitiva | Alta |
| Detetive de Hiring | Vagas abertas revelam onde concorrentes estão investindo | Média |
| Monitor de Mudanças de Site | Detectar quando concorrente altera homepage ou preços | Alta |
| Análise de Conteúdo Viral | Quais conteúdos dos concorrentes têm mais engajamento | Média |

---

*PRD v2.2 — Skill `seo-aeo-geo-intel` — Fevereiro 2026*
