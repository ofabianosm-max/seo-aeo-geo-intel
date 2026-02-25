#!/usr/bin/env python3
"""
tech_stack_detector.py — Módulo 7
Detecta o tech stack de concorrentes (CMS, frameworks, CDN, analytics)
e correlaciona com dados de performance da PageSpeed API.
"""

import os
import re
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))

# ── Assinaturas de tecnologias ──
# Cada tech tem: padrões para detectar via HTML/headers, classificação e peso de performance
TECH_SIGNATURES = {
    # CMS e Frameworks
    "WordPress": {
        "patterns": ["wp-content/", "wp-includes/", "wp-json/", "/xmlrpc.php", "WordPress"],
        "type": "cms", "tier": "legacy", "perf_impact": "negativo",
        "description": "CMS mais popular do mundo — performance depende muito de plugins e hospedagem",
    },
    "WordPress + Elementor": {
        "patterns": ["elementor/", "elementor-frontend", "e-con-inner"],
        "type": "page_builder", "tier": "legacy", "perf_impact": "muito negativo",
        "description": "Page builder pesado — frequentemente causa scores de performance < 60",
    },
    "WordPress + Divi": {
        "patterns": ["divi/", "et-pb-section", "et_pb_"],
        "type": "page_builder", "tier": "legacy", "perf_impact": "muito negativo",
        "description": "Similar ao Elementor — JS/CSS pesados afetam CWV",
    },
    "Webflow": {
        "patterns": ["webflow.com/css", "webflow.io", "data-wf-page", "Webflow"],
        "type": "no_code", "tier": "médio", "perf_impact": "neutro",
        "description": "Ferramenta no-code com boa estrutura — performance variada",
    },
    "Wix": {
        "patterns": ["wix.com", "wixstatic.com", "parastorage.com", "_wix_"],
        "type": "saas_builder", "tier": "básico", "perf_impact": "negativo",
        "description": "Builder fechado — limitado em customização e performance",
    },
    "Squarespace": {
        "patterns": ["squarespace.com", "sqspcdn.com", "squarespace-cdn"],
        "type": "saas_builder", "tier": "básico", "perf_impact": "neutro",
        "description": "Design bonito mas customização limitada",
    },
    "Next.js": {
        "patterns": ["__NEXT_DATA__", "_next/static", "_next/image", "next/dist"],
        "type": "framework", "tier": "elite", "perf_impact": "muito positivo",
        "description": "Framework React com SSR/SSG — alto potencial de performance",
    },
    "Nuxt.js": {
        "patterns": ["__NUXT__", "_nuxt/", "nuxt-link"],
        "type": "framework", "tier": "elite", "perf_impact": "muito positivo",
        "description": "Framework Vue equivalente ao Next.js",
    },
    "Gatsby": {
        "patterns": ["___gatsby", "gatsby-", "page-data.json"],
        "type": "framework", "tier": "elite", "perf_impact": "positivo",
        "description": "SSG React — ótimo para sites de conteúdo",
    },
    "Shopify": {
        "patterns": ["cdn.shopify.com", "Shopify.theme", "myshopify.com", "shopify-section"],
        "type": "ecommerce", "tier": "médio", "perf_impact": "neutro",
        "description": "Plataforma e-commerce — performance depende do tema",
    },
    "HubSpot CMS": {
        "patterns": ["hubspot.net", "hs-scripts.com", "hbspt.forms"],
        "type": "cms", "tier": "médio", "perf_impact": "neutro",
        "description": "CMS integrado ao CRM HubSpot",
    },
    "Ghost": {
        "patterns": ["ghost.io", "ghost/", "ghost.min.js"],
        "type": "cms", "tier": "médio", "perf_impact": "positivo",
        "description": "CMS minimalista para publicações — boa performance padrão",
    },

    # Hospedagem / CDN
    "Cloudflare": {
        "patterns": ["__cfduid", "cf-ray", "cloudflare-nginx", "cdn-cgi/"],
        "type": "cdn", "tier": None, "perf_impact": "positivo",
        "description": "CDN + proteção DDoS — melhora performance e segurança",
    },
    "Vercel": {
        "patterns": ["vercel.app", "x-vercel-id", "vercel-og"],
        "type": "hosting", "tier": None, "perf_impact": "muito positivo",
        "description": "Deploy automático com edge network global",
    },
    "Netlify": {
        "patterns": ["netlify.com", "netlify.app", "netlify-identity"],
        "type": "hosting", "tier": None, "perf_impact": "positivo",
        "description": "JAMstack hosting com CDN",
    },

    # Analytics e Marketing
    "Google Analytics 4": {
        "patterns": ["gtag/js?id=G-", "googletagmanager.com", "ga4"],
        "type": "analytics", "tier": None, "perf_impact": "leve negativo",
        "description": "Analytics principal do Google",
    },
    "Meta Pixel": {
        "patterns": ["connect.facebook.net/en_US/fbevents.js", "fbq(", "_fbp"],
        "type": "ads_pixel", "tier": None, "perf_impact": "leve negativo",
        "description": "Rastreamento de conversões para Meta Ads",
    },
    "Google Ads": {
        "patterns": ["googleadservices.com", "gtag('config', 'AW-", "google_conversion"],
        "type": "ads_pixel", "tier": None, "perf_impact": "neutro",
        "description": "Rastreamento de conversões para Google Ads",
    },
    "TikTok Pixel": {
        "patterns": ["analytics.tiktok.com", "tiktok-pixel", "_ttp"],
        "type": "ads_pixel", "tier": None, "perf_impact": "leve negativo",
        "description": "Rastreamento para TikTok Ads",
    },
    "LinkedIn Insight": {
        "patterns": ["snap.licdn.com", "linkedin.com/px", "_li_"],
        "type": "ads_pixel", "tier": None, "perf_impact": "leve negativo",
        "description": "Rastreamento para LinkedIn Ads",
    },
    "Hotjar": {
        "patterns": ["hotjar.com/", "hjSetting", "_hjid"],
        "type": "heatmap", "tier": None, "perf_impact": "negativo",
        "description": "Heatmaps e gravação de sessão — impacto na performance",
    },
    "Intercom": {
        "patterns": ["intercomcdn.com", "app.intercom.io", "intercom-"],
        "type": "chat", "tier": None, "perf_impact": "negativo",
        "description": "Chat e suporte ao cliente — JS pesado",
    },
    "ActiveCampaign": {
        "patterns": ["trackcmp.net", "activecampaign.com/ac/"],
        "type": "crm", "tier": None, "perf_impact": "leve negativo",
        "description": "CRM e automação de marketing",
    },
    "RD Station": {
        "patterns": ["d335luupugsy8c.cloudfront.net", "rdstation", "rd_station"],
        "type": "crm", "tier": None, "perf_impact": "leve negativo",
        "description": "CRM de marketing brasileiro",
    },
}

TIER_LABELS = {
    "elite":  "🏆 Elite (stack moderno)",
    "médio":  "✅ Médio (stack funcional)",
    "básico": "🟡 Básico (limitações evidentes)",
    "legacy": "🔴 Legacy (stack ultrapassado)",
}

TIER_SALES_ANGLE = {
    "legacy": "Stack desatualizado detectado. Enquanto eles batalham com Elementor lento, você pode ter um site 3x mais rápido.",
    "básico": "Usam uma plataforma fechada com customização limitada — vantagem para quem tem solução mais flexível.",
    "médio":  "Stack funcional, sem diferencial técnico marcante — oportunidade em performance ou features específicas.",
    "elite":  "Stack técnico forte — foco na diferenciação em UX, conteúdo ou proposta de valor.",
}


def fetch_page_html(url: str) -> tuple[str, dict]:
    """Busca o HTML e headers de uma URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SEOBot/1.0; +https://seunegocio.com.br/bot)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        return r.text, dict(r.headers)
    except Exception as e:
        return "", {}


def detect_technologies(html: str, headers: dict, response_headers_str: str = "") -> list[dict]:
    """Detecta tecnologias via assinaturas no HTML e headers HTTP."""
    detected = []
    content = html + " " + " ".join(f"{k}: {v}" for k, v in headers.items())

    for tech, sig in TECH_SIGNATURES.items():
        for pattern in sig["patterns"]:
            if pattern.lower() in content.lower():
                detected.append({
                    "name": tech,
                    "type": sig["type"],
                    "tier": sig.get("tier"),
                    "perf_impact": sig["perf_impact"],
                    "description": sig["description"],
                })
                break  # evitar duplicatas da mesma tech

    return detected


def classify_stack(detected: list[dict]) -> dict:
    """Classifica o stack geral baseado nas tecnologias detectadas."""
    cms_tech = [t for t in detected if t["type"] in ("cms", "framework", "no_code", "saas_builder", "ecommerce")]
    ads = [t for t in detected if t["type"] == "ads_pixel"]
    has_cdn = any(t["type"] == "cdn" for t in detected)
    has_heatmap = any(t["type"] == "heatmap" for t in detected)

    # Tier principal baseado no CMS/framework
    main_tier = "desconhecido"
    main_cms = None
    if cms_tech:
        main_cms = cms_tech[0]
        main_tier = main_cms.get("tier", "desconhecido")

    # Canais de anúncio ativos
    active_ad_channels = [t["name"] for t in ads]

    return {
        "main_cms": main_cms["name"] if main_cms else "Não identificado",
        "tier": main_tier,
        "tier_label": TIER_LABELS.get(main_tier, f"Desconhecido ({main_tier})"),
        "has_cdn": has_cdn,
        "has_heatmap": has_heatmap,
        "active_ad_channels": active_ad_channels,
        "sales_angle": TIER_SALES_ANGLE.get(main_tier, ""),
    }


def analyze(url: str, pagespeed_data: dict = None) -> dict:
    """
    Ponto de entrada. Analisa o tech stack e integra com PageSpeed.
    pagespeed_data: resultado do pagespeed_fetcher.analyze() (opcional mas recomendado)
    """
    domain = url.replace("https://","").replace("http://","").split("/")[0]
    print(f"  ⚡ Tech Stack: {domain}")

    # Buscar HTML
    html, resp_headers = fetch_page_html(url if url.startswith("http") else f"https://{url}")

    if not html:
        return {
            "status": "error",
            "reason": "Não foi possível acessar o site",
            "domain": domain,
        }

    # Detectar tecnologias
    detected = detect_technologies(html, resp_headers)
    stack = classify_stack(detected)

    # Performance (da PageSpeed API se disponível, senão estimativa)
    perf = {}
    if pagespeed_data and pagespeed_data.get("mobile", {}).get("status") == "ok":
        mobile = pagespeed_data["mobile"]
        perf = {
            "source": "PageSpeed API",
            "mobile_score": mobile["scores"]["performance"],
            "mobile_label": mobile["performance_label"],
            "cwv_lcp": mobile["lab"]["lcp"]["display"],
            "cwv_cls": mobile["lab"]["cls"]["display"],
            "cwv_inp": mobile["lab"]["inp"]["display"],
            "total_kb": mobile["weight"]["total_kb"],
        }
    else:
        # Estimativa baseada no CMS
        tier_estimates = {
            "legacy": {"score_range": "30-55", "estimate": True},
            "básico": {"score_range": "45-65", "estimate": True},
            "médio":  {"score_range": "60-80", "estimate": True},
            "elite":  {"score_range": "80-98", "estimate": True},
        }
        est = tier_estimates.get(stack.get("tier", ""), {"score_range": "N/D", "estimate": True})
        perf = {
            "source": "estimado",
            "mobile_score_range": est["score_range"],
            "note": "Configure PAGESPEED_API_KEY para dados reais",
        }

    result = {
        "status": "ok",
        "domain": domain,
        "fetched_at": datetime.now().isoformat(),
        "stack": stack,
        "technologies_detected": detected,
        "performance": perf,
        "total_technologies": len(detected),
    }

    # Cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"techstack-{domain}-{datetime.now().strftime('%Y-%m-%d')}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"     → {stack['tier_label']} | CMS: {stack['main_cms']} | {len(detected)} tecnologias detectadas")
    return result


def to_markdown(results: list[dict]) -> str:
    """Gera seção Markdown do Módulo 7."""
    lines = ["## MÓDULO 7 — RAIO-X TECNOLÓGICO", ""]

    # Tabela comparativa
    lines.append("### Comparativo de Tech Stack")
    lines.append("")
    lines.append("| Domínio | CMS / Framework | Tier | Performance | CDN | Pixels Ativos |")
    lines.append("|---|---|---|---|---|---|")

    for r in results:
        if r.get("status") != "ok":
            lines.append(f"| {r.get('domain','?')} | N/D | N/D | N/D | N/D | N/D |")
            continue

        stack = r["stack"]
        perf = r["performance"]

        if perf.get("source") == "PageSpeed API":
            perf_str = f"{perf['mobile_score']}/100 {perf['mobile_label']}"
        else:
            perf_str = f"{perf.get('mobile_score_range','N/D')} (estimado)"

        cdn = "✅" if stack["has_cdn"] else "❌"
        pixels = ", ".join(stack["active_ad_channels"]) or "Nenhum detectado"

        lines.append(f"| {r['domain']} | {stack['main_cms']} | {stack['tier_label']} | {perf_str} | {cdn} | {pixels} |")

    lines.append("")

    # Detalhes por concorrente
    for r in results:
        if r.get("status") != "ok":
            continue

        stack = r["stack"]
        lines.append(f"### {r['domain']}")
        lines.append("")

        # Todas as tecnologias detectadas agrupadas
        by_type = {}
        for t in r.get("technologies_detected", []):
            by_type.setdefault(t["type"], []).append(t["name"])

        type_labels = {
            "cms": "🖥️ CMS / Framework",
            "page_builder": "🔧 Page Builder",
            "no_code": "🎨 No-code",
            "saas_builder": "📦 Builder SaaS",
            "ecommerce": "🛒 E-commerce",
            "framework": "⚡ Framework",
            "cdn": "🌐 CDN",
            "hosting": "☁️ Hospedagem",
            "analytics": "📊 Analytics",
            "ads_pixel": "🎯 Pixels de Ads",
            "heatmap": "🔥 Heatmap / UX",
            "crm": "📧 CRM / E-mail",
            "chat": "💬 Chat",
        }

        for t_type, techs in by_type.items():
            label = type_labels.get(t_type, t_type)
            lines.append(f"**{label}:** {', '.join(techs)}")

        lines.append("")
        if stack.get("sales_angle"):
            lines.append(f"🎯 **Ângulo de vendas:** {stack['sales_angle']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tech Stack Detector — Módulo 7")
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", default="json", choices=["json","markdown"])
    args = parser.parse_args()

    result = analyze(args.url)
    if args.output == "markdown":
        print(to_markdown([result]))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
