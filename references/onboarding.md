# Onboarding — Configuração de Integrações

## Protocolo de Onboarding

### Fluxo completo

```
INÍCIO
  │
  ├─► Verificar credenciais existentes
  │     └─► Para cada integração:
  │           ├─► ✅ Presente e válida → marcar como ativa
  │           ├─► ❌ Ausente → oferecer configurar ou pular
  │           └─► ⚠️  Presente mas inválida → solicitar nova
  │
  ├─► Mostrar resumo de cobertura
  │     └─► Quais módulos estarão disponíveis
  │
  └─► Confirmar e prosseguir
```

### Mensagem de abertura do onboarding

```
🔧 CONFIGURAÇÃO — seo-aeo-geo-intel v2.2

Antes de iniciar a análise, vou verificar as integrações disponíveis.
Integrações marcadas como [opcional] podem ser puladas sem perda crítica.

Verificando...
```

---

## Integração 1 — Tavily API
**Tipo:** Obrigatória
**Usada em:** Módulos 2, 5, 6, 7, 8, 9, 10, 11, 13, 15, 16

### O que é
Tavily é uma API de busca e extração de conteúdo web otimizada para IA.
Usada para crawlar sites de concorrentes, buscar reclamações, detectar tech stack,
mapear preços, descobrir iscas e encontrar novos entrantes.

### Como obter a chave
1. Acesse: https://tavily.com
2. Crie uma conta gratuita
3. Vá em Dashboard → API Keys → Create New Key
4. Plano gratuito: 1.000 buscas/mês (suficiente para uso moderado)
5. Plano Researcher: $35/mês — recomendado para uso intenso

### Configuração
```bash
# Opção 1: variável de ambiente (recomendado)
export TAVILY_API_KEY="tvly-xxxxxxxxxxxxxxxxxxxx"

# Opção 2: arquivo .env na raiz do projeto
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
```

### Teste de conexão
```python
import os
from tavily import TavilyClient
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
result = client.search("test query", max_results=1)
# Se retornar resultado → ✅ conexão OK
```

### Mensagem se ausente
```
❌ Tavily API — não configurada

Esta é a principal fonte de inteligência competitiva da skill.
Sem ela, os seguintes módulos ficam indisponíveis:
• Espião de Concorrentes, Reclamações, Iscas, Tech Stack,
  Preços, Radar, Posicionamento, Canais, Links Internos,
  Saúde do Conteúdo, Local SEO

Para obter gratuitamente: https://tavily.com
Chave começa com "tvly-"

[C] Configurar agora   [S] Pular e continuar sem ela
```

---

## Integração 2 — Google Search Console API
**Tipo:** Obrigatória
**Usada em:** Módulos 1, 3, 9, 12, 13, 15

### O que é
API oficial do Google que fornece dados reais de performance do seu site:
clicks, impressões, CTR, posição média, cobertura de indexação, sitemaps e erros.

### Pré-requisito
O site precisa estar verificado no Google Search Console.
Acesse: https://search.google.com/search-console

### Método recomendado: Service Account (para automação)

**Passo a passo:**

**1. Criar projeto no Google Cloud**
```
1. Acesse: https://console.cloud.google.com
2. Crie um novo projeto (ex: "seo-intel-skill")
3. Ative a Search Console API:
   → APIs & Services → Library → "Google Search Console API" → Enable
```

**2. Criar Service Account**
```
1. APIs & Services → Credentials → Create Credentials → Service Account
2. Nome: "seo-intel-skill"
3. Role: Viewer (leitura apenas)
4. Criar e baixar chave JSON → salvar como gsc-credentials.json
```

**3. Adicionar Service Account no Search Console**
```
1. Abra o Search Console da sua propriedade
2. Configurações → Usuários e permissões → Adicionar usuário
3. Email: o email da service account (ex: seo-intel@projeto.iam.gserviceaccount.com)
4. Permissão: Proprietário ou Leitor completo
```

**4. Configurar**
```bash
# Opção 1: path para o arquivo JSON
export GSC_SERVICE_ACCOUNT_JSON="/path/to/gsc-credentials.json"

# Opção 2: conteúdo inline (para ambientes sem sistema de arquivos)
export GSC_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"..."}'
```

### Método alternativo: OAuth 2.0 (para uso pessoal)
```bash
# Gera token interativo na primeira execução
export GSC_OAUTH_TOKEN="ya29.xxxxxxxxxxxx"
# Renovação automática via refresh token
export GSC_OAUTH_REFRESH_TOKEN="1//xxxxxxxxxxxx"
```

### Teste de conexão
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'gsc-credentials.json',
    scopes=['https://www.googleapis.com/auth/webmasters.readonly']
)
service = build('searchconsole', 'v1', credentials=creds)
sites = service.sites().list().execute()
# Se retornar lista de sites → ✅ conexão OK
```

### Mensagem se ausente
```
❌ Google Search Console — não configurado

Sem o GSC, não é possível obter dados reais de performance do seu site.
Módulos afetados: Análise SEO/AEO/GEO, Monitor de Keywords,
  SEO Técnico, Links Internos, Saúde do Conteúdo.

A configuração leva ~10 minutos na primeira vez.
Para o guia completo: references/onboarding.md → Integração 2

[C] Configurar agora (vou guiar passo a passo)
[S] Pular — analisar apenas com Tavily
```

---

## Integração 3 — Google PageSpeed Insights API
**Tipo:** Recomendada (não bloqueia execução)
**Usada em:** Módulos 1, 2, 7, 12

### O que é
API oficial do Google que retorna métricas reais de performance (Core Web Vitals,
Lighthouse scores, oportunidades de melhoria). Gratuita com 25.000 req/dia.

### Como obter a chave
```
1. Acesse: https://console.developers.google.com
2. Selecione ou crie um projeto
3. APIs & Services → Library → "PageSpeed Insights API" → Enable
4. APIs & Services → Credentials → Create Credentials → API Key
5. (Recomendado) Restringir a chave para PageSpeed Insights API
```

### Configuração
```bash
export PAGESPEED_API_KEY="AIzaSy-xxxxxxxxxxxxxxxxxxxx"
```

### Teste de conexão
```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed\
?url=https://google.com&strategy=mobile&key=$PAGESPEED_API_KEY"
# Se retornar JSON com "lighthouseResult" → ✅ conexão OK
```

### Mensagem se ausente
```
⚠️  PageSpeed API — não configurada [recomendada]

Sem ela, dados de performance são estimados via Tavily (menos precisos).
Com ela, os dados vêm diretamente do Google (25.000 req/dia grátis).

Obter chave: https://console.developers.google.com (5 minutos)

[C] Configurar agora   [S] Pular — usar estimativas do Tavily
```

---

## Integração 4 — Ahrefs API (opcional)
**Tipo:** Opcional
**Usada em:** Módulo 14 (Backlinks)

### O que é
API do Ahrefs para dados de backlinks: Domain Rating, domínios de referência,
link gap vs concorrentes e detecção de links tóxicos.

### Plano necessário
Ahrefs API está disponível a partir do plano **Advanced** (~$449/mês).
Para uso esporádico, considerar o plano **Starter** e exportar manualmente.

### Configuração
```bash
export AHREFS_API_KEY="ahrefs_xxxxxxxxxxxxxxxxxxxx"
```

### Mensagem se ausente
```
⚙️  Ahrefs API — não configurada [opcional]

Módulo 14 (Backlinks) ficará indisponível.
Esta é a única funcionalidade que requer API paga.
Todos os outros 15 módulos funcionam sem ela.

[C] Configurar agora   [S] Pular — recomendado se não tem conta Ahrefs
```

---

## Integração 5 — Semrush API (opcional, alternativa ao Ahrefs)
**Tipo:** Opcional
**Usada em:** Módulo 14 (Backlinks) — alternativa ao Ahrefs

### Configuração
```bash
export SEMRUSH_API_KEY="xxxxxxxxxxxxxxxxxxxx"
```

### Mensagem se ausente
```
⚙️  Semrush API — não configurada [opcional]

Alternativa ao Ahrefs para dados de backlinks.
Se Ahrefs já estiver configurado, esta é redundante.

[C] Configurar agora   [S] Pular
```

---

## Resumo de Cobertura por Combinação

### Cenário 1: Apenas Tavily (mínimo viável para competidores)
```
✅ Disponíveis: 2, 4, 5, 6, 7*, 8, 9*, 10, 11, 15*
❌ Indisponíveis: 1*, 3, 12*, 13, 14, 16*
* parcialmente disponível
```

### Cenário 2: Tavily + GSC (recomendado para análise do seu site)
```
✅ Disponíveis: 1, 2, 3, 4, 5, 6, 7*, 8, 9, 10, 11, 12*, 13, 15, 16*
❌ Indisponíveis: 14
* sem dados de performance precisos
```

### Cenário 3: Tavily + GSC + PageSpeed (setup ideal)
```
✅ Disponíveis: 1-13, 15, 16
❌ Indisponíveis: 14 (requer Ahrefs/Semrush)
```

### Cenário 4: Setup completo
```
✅ Todos os 16 módulos disponíveis
```

---

## Armazenamento das Credenciais

### Arquivo .env (desenvolvimento local)
```bash
# .env — NÃO commitar no Git
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
GSC_SERVICE_ACCOUNT_JSON=/path/to/gsc-credentials.json
PAGESPEED_API_KEY=AIzaSy-xxxxxxxxxxxxxxxxxxxx
AHREFS_API_KEY=                    # deixar vazio se não tiver
SEMRUSH_API_KEY=                   # deixar vazio se não tiver

# Configurações
SEO_SKILL_CACHE_DIR=./cache
SEO_SKILL_OUTPUT_DIR=./reports
SEO_SKILL_TIMEZONE=America/Sao_Paulo
SEO_SKILL_LANGUAGE=pt-BR
SEO_SKILL_LOCAL_SEO=auto           # auto | on | off
```

### Verificação de saúde (executar antes de análises longas)
```bash
python scripts/check_integrations.py
# Output:
# ✅ Tavily API         — OK (987 créditos restantes)
# ✅ Google SC          — OK (3 propriedades encontradas)
# ✅ PageSpeed API      — OK
# ⏭️  Ahrefs API        — Não configurada (Módulo 14 desativado)
# ⏭️  Semrush API       — Não configurada
```
