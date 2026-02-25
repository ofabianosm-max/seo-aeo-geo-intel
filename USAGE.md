# Como Usar a Skill — seo-aeo-geo-intel

## Instalação Rápida

### 1. Instalar dependências Python

```bash
pip install google-auth google-auth-oauthlib google-api-python-client \
            tavily-python requests python-dotenv pandas
```

### 2. Configurar credenciais

Copiar o arquivo de exemplo e preencher:
```bash
cp .env.example .env
# editar .env com suas chaves
```

Mínimo para começar (só com Tavily — análise de concorrentes):
```bash
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
```

Setup recomendado (análise completa do seu site):
```bash
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
GSC_SERVICE_ACCOUNT_JSON=/path/to/credentials.json
PAGESPEED_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
```

### 3. Verificar integrações

```bash
python scripts/check_integrations.py
```

---

## Primeiro Uso — Onboarding Interativo

Na primeira vez que usar a skill, ela automaticamente inicia o onboarding:

```
Você: "Analise meu site seunegocio.com.br"

Skill: 🔧 CONFIGURAÇÃO INICIAL — seo-aeo-geo-intel

       Verificando integrações...

       ✅ Tavily API         — OK
       ❌ Google Search Console — não configurado
       ✅ PageSpeed API      — OK
       ⏭️  Ahrefs API        — não configurada [opcional]
       ⏭️  Semrush API       — não configurada [opcional]

       Google Search Console está ausente.
       Sem ele, não consigo dados reais de performance do seu site.
       Módulos afetados: Análise SEO/AEO/GEO, Monitor de Keywords,
       SEO Técnico, Links Internos, Saúde do Conteúdo.

       [C] Configurar agora (leva ~10 minutos, vou guiar)
       [S] Pular — analisar apenas com Tavily e PageSpeed

Você: "S" (ou "pular" ou "skip")

Skill: ✅ Entendido. Seguindo com Tavily + PageSpeed.

       📊 Cobertura desta execução:
       ✅ Módulos ativos (10/16): 2, 4, 5, 6, 7, 8, 10, 11, 12e, 15a
       ⏭️  Pulados por integração ausente:
          • Módulos 1, 3, 9, 12a-d, 13, 15b-d (requerem GSC)
          • Módulo 14 (requer Ahrefs ou Semrush)
          • Módulo 16 (nicho não-local detectado)

       Iniciando análise de seunegocio.com.br...
```

Para pular o onboarding em execuções futuras (se já configurado):
```
Você: "Analise meu site, skip onboarding"
```

---

## Comandos por Caso de Uso

### Análise Completa do Seu Site

```
"Analise meu site seunegocio.com.br"
"Faça uma auditoria completa de seunegocio.com.br"
"Diagnóstico completo de SEO do meu site"
```

O que entrega:
- Scores SEO + AEO + GEO + Técnico
- PageSpeed Insights (mobile + desktop)
- Análise de todos os concorrentes detectados
- Monitor de keywords
- Todos os módulos disponíveis
- Plano de ação em sprints

Tempo estimado: 3-5 minutos

---

### Monitoramento Semanal (Atualização)

```
"Atualize o monitoramento"
"O que mudou essa semana?"
"Update do site"
"Relatório delta desde segunda-feira"
```

**Requer:** baseline de uma análise anterior salva em `cache/`.

O que entrega:
- Apenas o que mudou (delta)
- Alertas de queda de keywords
- Ganhos de posição
- Novas keywords descobertas
- Mudanças detectadas em concorrentes

Tempo estimado: 1-2 minutos

---

### Espionar um Concorrente Específico

```
"Espione rival1.com.br"
"Analise o concorrente rival1.com.br"
"Dossiê completo de rival1.com.br"
"O que rival1.com.br faz de diferente?"
```

O que entrega:
- Tech stack + PageSpeed score
- Reclamações e padrões de falha
- Iscas e lead magnets
- Preços (se publicados)
- Posicionamento e narrativa
- Canais de aquisição
- Comparativo vs seu site (se já analisado)

Tempo estimado: 2-3 minutos

---

### Análise de Performance

```
"Como está a performance do meu site?"
"PageSpeed do seunegocio.com.br"
"Core Web Vitals do site"
"Meu site está lento?"
"Compare minha velocidade com a dos concorrentes"
```

O que entrega:
- Score PageSpeed mobile + desktop
- Todos os Core Web Vitals (Lab + Field data)
- Oportunidades de melhoria com economia estimada
- Comparativo vs concorrentes (se informados)
- Diagnóstico técnico (Módulo 12e)

Tempo estimado: 30-60 segundos

---

### Descoberta de Keywords

```
"Que palavras-chave devo atacar?"
"Novas oportunidades de keywords"
"Palavras-chave que estou perdendo"
"Que conteúdo devo criar?"
"Encontre keywords fáceis de ranquear no meu nicho"
```

O que entrega:
- Keywords na zona de oportunidade (posições 8-20)
- Keywords com impressões mas CTR baixo (oportunidade latente)
- Novas keywords via Tavily (PAA, relacionadas, fóruns)
- Keywords em decay (estava bem, está caindo)
- Canibalização de keywords
- Sugestão de ação por keyword

Tempo estimado: 2 minutos

---

### Benchmark de Preços

```
"Quanto cobram os concorrentes?"
"Compare os preços do mercado de [nicho]"
"Benchmark de preços: rival1.com.br, rival2.com.br"
"Estou cobrando certo?"
```

O que entrega:
- Tabela comparativa de preços por tier
- O que cada plano inclui
- Garantias oferecidas (ou ausência)
- Gaps de oferta no mercado
- Sugestão de posicionamento de preço

Tempo estimado: 1-2 minutos

---

### Detetive de Reclamações

```
"O que reclamam dos meus concorrentes?"
"Encontre fraquezas de rival1.com.br"
"Reclamações sobre agências de [nicho]"
"Onde meus concorrentes falham?"
```

O que entrega:
- Score de reputação por concorrente
- Padrões de reclamação categorizados
- Citações textuais representativas
- Copy sugerido para explorar cada fraqueza

Tempo estimado: 1-2 minutos

---

### Auditoria Técnica de SEO

```
"Auditoria técnica do meu site"
"Problemas de indexação do seunegocio.com.br"
"Meu site está com problemas no robots.txt?"
"Análise de links internos"
"Páginas órfãs no meu site"
```

O que entrega:
- Análise de robots.txt e sitemap
- Erros de cobertura do GSC
- Redirect chains problemáticas
- Problemas de canonical
- Páginas órfãs
- Profundidade de links internos
- Distribuição de PageRank interno

Tempo estimado: 2-3 minutos

---

### Local SEO

```
"Como está meu Google Meu Negócio?"
"Análise de SEO local para [negócio] em [cidade]"
"Estou aparecendo no Google Maps?"
"Reviews e avaliações do meu negócio"
```

O que entrega:
- Status do Google Business Profile
- Checklist de completude (fotos, horários, posts, Q&A)
- Performance em keywords locais (GSC)
- Comparativo vs concorrentes no Local Pack
- Plano de ação para subir no Local Pack

Tempo estimado: 1-2 minutos (ativa automaticamente se nicho local)

---

### Radar de Novos Entrantes

```
"Algum novo concorrente no mercado?"
"Novos players no nicho de [X]"
"Alguém novo está ranqueando para minhas keywords?"
```

O que entrega:
- Novos domínios ranqueando para suas keywords
- Tech stack e nível de risco de cada entrante
- Sinais de crescimento (reviews, backlinks novos)
- Recomendação de frequência de monitoramento

Tempo estimado: 1 minuto

---

### Backlinks (requer Ahrefs ou Semrush)

```
"Análise de backlinks do meu site"
"Quem linka para meus concorrentes?"
"Link gap vs rival1.com.br"
"Tenho links tóxicos?"
```

O que entrega:
- Domain Rating / Authority Score
- Domínios de referência e tendência
- Link gap vs concorrentes (oportunidades de link building)
- Links tóxicos detectados
- Distribuição de anchor text

Tempo estimado: 1-2 minutos

---

## Opções Avançadas

### Definir período de análise

```
"Analise os últimos 90 dias" (padrão: 30 dias)
"Análise do GSC da última semana"
"Dados de keywords do trimestre"
```

### Focar em URLs específicas

```
"Analise a performance da página /servicos"
"PageSpeed só da home e da página de preços"
"Problemas de indexação nas páginas /blog/*"
```

### Comparar múltiplos concorrentes

```
"Compare rival1.com.br, rival2.com.br e rival3.com.br"
"Benchmark dos 5 maiores players do mercado de [nicho]"
```

### Salvar e nomear baseline

```
"Salve este relatório como baseline de fevereiro"
"Guarde os dados de hoje para comparar no mês que vem"
```

### Forçar re-análise (ignorar cache)

```
"Analise sem usar cache"
"Atualização forçada — ignore os dados salvos"
```

---

## Entendendo o Output

### O relatório é sempre Markdown estruturado

O arquivo gerado segue a especificação em `references/output-spec.md`.
Está pronto para ser consumido por um agente downstream que vai formatar
no canal e formato que você precisar (PDF, email, Slack, Notion, etc.).

### Localização dos arquivos

```
reports/
├── relatorio-2026-02-24-seunegocio.com.br-full.md
├── relatorio-2026-02-24-rival1.com.br-competitor.md
└── relatorio-2026-02-24-seunegocio.com.br-delta.md

cache/
├── baseline-seunegocio.com.br.json      ← para modo delta
├── gsc-seunegocio.com.br-2026-02-24.json ← cache 24h do GSC
└── tavily-rival1.com.br-2026-02-22.json  ← cache 72h do Tavily
```

### Lendo os scores

| Score | Interpretação | Ação |
|---|---|---|
| 80-100 | Excelente | Manter e monitorar |
| 60-79 | Bom | Otimizações pontuais |
| 40-59 | Regular | Plano de melhoria ativo |
| 20-39 | Ruim | Prioridade alta |
| 0-19 | Crítico | Ação imediata |

### Lendo os prefixos de severidade

```
🔴 CRÍTICO  → Impacto alto + esforço baixo-médio → Faça primeiro
🟡 ALTO     → Impacto alto + esforço médio → Sprint 1 ou 2
🟢 MÉDIO    → Impacto médio → Backlog priorizado
⚪ BAIXO    → Nice-to-have → Quando tiver tempo
🏆          → Oportunidade única no mercado → Não perca
🎯          → Copy ou ação pronta para usar → Copie direto
```

### Entendendo as fontes

```
(fonte: GSC)          → Dado real, extraído da sua conta Google
(fonte: Tavily)       → Coletado via crawl/busca em tempo real
(fonte: PageSpeed API)→ Dado oficial do Google, não estimativa
(estimado)            → Calculado por fórmula, não dado exato
N/D                   → Não foi possível coletar — não foi inventado
```

---

## Perguntas Frequentes

**P: Quanto tempo leva uma análise completa?**
R: 3-5 minutos para modo `full`. 1-2 minutos para modos específicos.

**P: Com que frequência devo rodar?**
R: Modo `full` mensalmente. Modo `delta` semanalmente.
Para nichos competitivos: `full` quinzenal + `delta` semanal.

**P: Os dados de concorrentes são precisos?**
R: Dados via Tavily são coletados em tempo real e marcados como
`(fonte: Tavily)`. Volumes de tráfego de concorrentes são sempre
`(estimado)` — nenhuma ferramenta externa tem acesso ao GSC deles.

**P: O que acontece se o Tavily não conseguir crawlar um concorrente?**
R: O módulo executa com dados parciais e registra um `warning`
no bloco de metadados. O relatório informa: "análise parcial — site restritivo".

**P: Posso analisar um site que não é meu?**
R: Sim, para os módulos que usam Tavily (concorrentes, tech stack,
reclamações, iscas, preços, posicionamento, canais). Os módulos
que usam GSC (performance, indexação, keywords) só funcionam
para sites verificados na sua conta.

**P: O cache pode dar dados desatualizados?**
R: GSC é cacheado por 24h. Tavily por 72h. PageSpeed não tem cache
(cada chamada é fresh). Para forçar atualização: "analise sem cache".

**P: Posso usar para múltiplos sites?**
R: Sim. A skill detecta o site pelo domínio informado e
mantém baselines separados por domínio no cache.

---

## Limitações Conhecidas

| Limitação | Impacto | Workaround |
|---|---|---|
| GSC só para sites verificados | Análise de performance limitada a sites seus | Adicionar ao GSC antes de usar |
| Volumes de keywords de concorrentes são estimados | Não são dados exatos | Usar como referência relativa, não absoluta |
| Tavily pode ser bloqueado em alguns sites | Análise de concorrente parcial | Registrado como warning no relatório |
| Backlinks requerem API paga | Módulo 14 opcional | Usar Ahrefs/Semrush free trial quando precisar |
| Local SEO sem integração GBP API | Dados do GBP via Tavily (menos completos) | Complementar com verificação manual |

---

## Glossário Rápido

| Termo | Significado |
|---|---|
| SEO | Search Engine Optimization — ranquear no Google |
| AEO | Answer Engine Optimization — aparecer em featured snippets e respostas diretas |
| GEO | Generative Engine Optimization — ser citado por IAs como ChatGPT, Perplexity |
| GSC | Google Search Console — painel oficial do Google para webmasters |
| CWV | Core Web Vitals — métricas de performance do Google (LCP, CLS, INP) |
| LCP | Largest Contentful Paint — tempo até o maior elemento carregar |
| CLS | Cumulative Layout Shift — estabilidade visual da página |
| INP | Interaction to Next Paint — responsividade a interações |
| CTR | Click-Through Rate — % de impressões que viram cliques |
| SERP | Search Engine Results Page — página de resultados do Google |
| E-E-A-T | Experience, Expertise, Authoritativeness, Trustworthiness |
| PAA | People Also Ask — perguntas relacionadas no Google |
| GBP | Google Business Profile — Google Meu Negócio |
| DR | Domain Rating — métrica de autoridade do Ahrefs (0-100) |
| Modo delta | Relatório que mostra apenas o que mudou desde o baseline |
| Baseline | Snapshot salvo de uma análise anterior para comparação futura |
| Thin content | Página com conteúdo insuficiente para ranquear bem |
| Content decay | Queda gradual de tráfego em páginas que antes ranqueavam bem |
| Canibalização | Duas páginas do mesmo site competindo pela mesma keyword |
