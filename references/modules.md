# References — Módulos 1 a 16

Este arquivo é o guia de execução de cada módulo.
Ler sob demanda: o SKILL.md referencia este arquivo quando um módulo precisa ser executado.

---

## MÓDULO 1 — Análise SEO + AEO + GEO

### O que analisa
- **SEO:** performance real via GSC (clicks, impressões, CTR, posição média)
- **AEO:** presença em featured snippets, People Also Ask e zero-click results
- **GEO:** chance de ser citado por IAs (ChatGPT, Perplexity, Gemini)

### Score SEO (0-100)
```
posição média <= 5  → 80-100
posição média 6-15  → 50-80
posição média > 15  → 0-50
penalidade por issues técnicos críticos: -10 a -20
```

### Score AEO (0-100)
```
featured snippets: +20
PAA boxes: +15 por pergunta
schema markup: +15 (FAQ, HowTo, Article)
respostas diretas detectadas: +20
```

### Score GEO (0-100)
```
conteúdo em formato citável (listas, definições, estatísticas): +25
E-E-A-T signals (autor, data, fontes): +20
Conteúdo em sites que IAs citam: +20
Estrutura semântica clara: +15
```

### Scripts
```bash
python scripts/gsc_fetcher.py --site SITE --report top_queries
python scripts/gsc_fetcher.py --site SITE --report top_pages
python scripts/pagespeed_fetcher.py --url URL --strategy both
```

### Output esperado
Score SEO + AEO + GEO + tabela de top páginas + issues identificados.

---

## MÓDULO 2 — Espião de Concorrentes

### O que analisa
Comparativo completo entre seu site e cada concorrente listado.

### Dimensões comparadas
- Scores SEO/AEO/GEO (estimados via Tavily se GSC indisponível para eles)
- PageSpeed mobile vs desktop
- Número de páginas indexadas (estimado)
- Velocidade de publicação de conteúdo
- Presença em featured snippets

### Scripts
```bash
python scripts/tavily_fetcher.py --mode tech --competitor DOMAIN
python scripts/pagespeed_fetcher.py --url https://DOMAIN
```

### Output esperado
Tabela comparativa com deltas vs seu site. Oportunidades de superação.

---

## MÓDULO 3 — Monitoramento de Keywords

### O que analisa
Mudanças de posição, novas keywords descobertas e oportunidades de quick wins.

### Lógica de alertas
- **Queda crítica:** posição piorou 5+ posições E página tinha > 50 clicks/mês
- **Oportunidade:** posição 8-20, impressões > 50/mês → quick win potencial
- **Latent demand:** CTR < 2% mas impressões altas → problema de título/meta

### Frequência recomendada
- Monitoramento completo: semanal (modo `delta`)
- Relatório completo: mensal (modo `full`)

### Scripts
```bash
python scripts/gsc_fetcher.py --site SITE --report changes
python scripts/gsc_fetcher.py --site SITE --report opportunities
```

---

## MÓDULO 4 — Plano de Ação

### Geração do plano
O Módulo 4 é sempre gerado pelo `markdown_builder.py` ao final da execução.
Consolida issues de todos os módulos em sprints priorizados.

### Critérios de priorização
```
Sprint 1 (Quick wins): impacto ALTO + esforço BAIXO
  → Issues técnicos críticos (robots.txt, sitemap, redirects)
  → Keywords em posição 8-10 (uma otimização pode subir para top 5)

Sprint 2 (Crescimento): impacto ALTO + esforço MÉDIO
  → Content decay: atualizar artigos caindo
  → Canibalização: consolidar páginas

Sprint 3 (Autoridade): impacto MÉDIO-ALTO + esforço ALTO
  → Backlinks: link gap
  → GEO: reestruturar conteúdo para citação por IAs
  → Topical authority: criar conteúdo para gaps identificados
```

---

## MÓDULO 5 — Detetive de Reclamações

### Fontes de busca
- Reclame Aqui (site:reclameaqui.com.br)
- Google Reviews (via snippets)
- Twitter/X
- Reddit (site:reddit.com)
- Fóruns e grupos

### Categorias de reclamação
```
prazo_entrega   → atraso, demora, não entregou
suporte         → não responde, sumiu, sem resposta
qualidade       → mal feito, bugado, não funciona
preco           → cobrou a mais, golpe, fraude
resultado       → zero resultado, não adiantou
transparencia   → escondia, enganoso, letra miúda
pos_venda       → abandonou após o pagamento
```

### Script
```bash
python scripts/tavily_fetcher.py --mode complaints --competitor DOMAIN
```

### Output esperado
Score de reputação + distribuição de categorias + snippets representativos + copy sugerido.

---

## MÓDULO 6 — Espião de Iscas (Lead Magnets)

### O que detecta
- eBooks e PDFs
- Checklists e templates
- Ferramentas e calculadoras
- Aulas gratuitas e webinars
- Auditorias e diagnósticos gratuitos
- Cursos gratuitos

### Script
```bash
python scripts/tavily_fetcher.py --mode magnets --niche "NICHO" --competitors DOMAIN1,DOMAIN2
```

### Output esperado
Lista de iscas identificadas por tipo + gaps (o que ninguém oferece ainda) + sugestão de isca diferenciada.

---

## MÓDULO 7 — Raio-X Tecnológico

### Classificação de stack
```
🏆 Elite:    Next.js/Nuxt/Astro + CDN (Vercel/Netlify/Cloudflare)
✅ Moderna:   React/Vue/Svelte ou framework moderno
🟡 Mediana:  WordPress + CDN
🔴 Legada:   WordPress + Elementor/Divi sem CDN, Wix, SquareSpace
```

### Scripts
```bash
python scripts/tavily_fetcher.py --mode tech --url https://DOMAIN
python scripts/pagespeed_fetcher.py --url https://DOMAIN --strategy mobile
```

### Output esperado
Stack detectada + PageSpeed score + classificação + argumento de venda técnico.

---

## MÓDULO 8 — Benchmark de Preços

### Como coleta
1. Tenta `/precos`, `/planos`, `/pricing`, `/servicos`
2. Busca via Tavily: `site:DOMAIN preço OR plano OR R$`
3. Busca social: publicações com preços

### Script
```bash
python scripts/tavily_fetcher.py --mode prices --competitors DOMAIN1,DOMAIN2 --niche "NICHO"
```

### Output esperado
Tabela comparativa de preços + gaps de oferta + sugestão de posicionamento.

---

## MÓDULO 9 — Radar de Novos Entrantes

### O que detecta
- Novos domínios ranqueando para suas keywords principais
- Domínios que não existiam no baseline anterior

### Script
```bash
python scripts/tavily_fetcher.py --mode radar --keywords "kw1,kw2" --known DOMAIN1,DOMAIN2
```

### Output esperado
Lista de novos players + tech stack + risco estimado.

---

## MÓDULO 10 — Análise de Posicionamento

### O que extrai
- Promessa principal (headline da home)
- Inimigo declarado ("pare de perder tempo com...")
- Prova (depoimentos, números, cases)
- Garantia
- Proposta de valor única

### Script
```bash
python scripts/tavily_fetcher.py --mode positioning --competitor DOMAIN
```

### Output esperado
Mapa de posicionamento de cada player + gaps narrativos + sugestão de diferenciação.

---

## MÓDULO 11 — Mapa de Canais e Anúncios

### Pixels detectados
- Google Ads (gtag, adsbygoogle)
- Meta Pixel (fbq)
- TikTok Pixel (ttq)
- LinkedIn Insight (snap)
- Hotjar / Clarity (analytics de comportamento)
- RD Station / HubSpot (automação)

### Canais orgânicos verificados
YouTube, Instagram, LinkedIn, TikTok, Facebook

### Script
```bash
python scripts/tavily_fetcher.py --mode channels --competitor DOMAIN
```

### Output esperado
Mapa de canais pagos e orgânicos por concorrente + canais com zero competição.

---

## MÓDULO 12 — SEO Técnico

### Sub-módulos
- **12a Robots.txt:** bloqueio de CSS/JS, sitemap declarado, Disallow total
- **12b Cobertura GSC:** páginas descobertas mas não indexadas, erros
- **12c Canonical:** páginas sem canonical, canonicals incorretos
- **12d HTTPS:** certificado válido, HTTP→HTTPS, mixed content
- **12e Performance:** via PageSpeed API (scores + Core Web Vitals)

### Script
```bash
python scripts/crawl_analyzer.py --site SITE --report full --md
```

### Output esperado
Score técnico + issues por sub-módulo + tabelas de cobertura e sitemap.

---

## MÓDULO 13 — Arquitetura e Links Internos

### O que analisa
- Páginas órfãs (indexadas, sem links internos apontando)
- Profundidade de cliques do home (> 3 = problema)
- Distribuição de PageRank interno
- Qualidade dos anchor texts

### Script
```bash
python scripts/internal_link_analyzer.py --site SITE --md
```

### Output esperado
Score de arquitetura + lista de órfãs + profundidade por página + qualidade de anchors.

---

## MÓDULO 14 — Backlinks (Opcional)

### Requer
`AHREFS_API_KEY` ou `SEMRUSH_API_KEY` (plano pago).
Se ausentes: `status: skipped`.

### O que coleta
- Domain Rating (Ahrefs) ou Authority Score (Semrush)
- Total de backlinks e domínios de referência
- Link gap vs concorrentes (oportunidades de link building)
- Links potencialmente tóxicos

### Script
```bash
python scripts/backlink_fetcher.py --site SITE --competitors DOMAIN1,DOMAIN2 --md
```

---

## MÓDULO 15 — Saúde do Conteúdo

### Sub-módulos
- **15a Decay:** páginas com queda contínua de tráfego (3 períodos de 28d)
- **15b Canibalização:** 2+ páginas competindo pela mesma keyword
- **15c Thin content:** páginas indexadas com < 300 palavras
- **15d Topical map:** subtópicos do nicho cobertos vs ausentes

### Script
```bash
python scripts/content_health.py --site SITE --niche "NICHO" --competitors DOMAIN1 --md
```

### Output esperado
Score de saúde + páginas em decay + grupos de canibalização + thin content + topical map.

---

## MÓDULO 16 — Local SEO (Condicional)

### Ativa quando
- `SEO_SKILL_LOCAL_SEO=on` na config
- Nicho local detectado nas keywords (médico, dentista, restaurante, etc.)
- Usuário pede explicitamente

### O que analisa
- Google Business Profile (via Tavily — sem API oficial)
- Rating e volume de reviews
- Consistência NAP em diretórios
- Keywords locais ranqueadas (GSC)
- Concorrentes no Local Pack

### Script
```bash
python scripts/local_seo_analyzer.py \
  --business-name "Nome do Negócio" \
  --city "Cidade" \
  --niche "nicho" \
  --site seunegocio.com.br \
  --md
```

### Output esperado
Score local + checklist GBP + keywords locais + concorrentes no pack + plano de ação local.
