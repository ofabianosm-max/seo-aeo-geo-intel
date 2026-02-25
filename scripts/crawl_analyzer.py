#!/usr/bin/env python3
"""
crawl_analyzer.py
Módulo 12 — SEO Técnico: análise de robots.txt, sitemap, redirects e canonicals.
"""

import os
import re
import json
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400  # 24h

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SEOIntelBot/1.0; "
        "+https://github.com/seo-intel)"
    )
}


def _cache_path(site: str, report: str) -> Path:
    key = hashlib.md5(f"{site}:{report}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"crawl-{key}.json"


def _load_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(seconds=CACHE_TTL):
            return data
    except Exception:
        pass
    return None


def _save_cache(path: Path, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def _get(url: str, timeout: int = 10, follow_redirects: bool = True) -> requests.Response | None:
    try:
        return requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=follow_redirects,
        )
    except Exception:
        return None


# ──────────────────────────────────────────
# robots.txt
# ──────────────────────────────────────────

def analyze_robots(site: str) -> dict:
    base = _normalize_url(site)
    url  = f"{base}/robots.txt"
    resp = _get(url)

    result = {
        "url":     url,
        "exists":  False,
        "issues":  [],
        "sitemap_declared": False,
        "sitemap_urls": [],
        "disallowed_paths": [],
        "blocks_css_js": False,
        "blocks_important_paths": [],
        "raw": "",
    }

    if not resp or resp.status_code != 200:
        result["issues"].append({
            "severity": "🟡 ALTO",
            "message":  "robots.txt não encontrado — Google usa permissões padrão",
        })
        return result

    result["exists"] = True
    content = resp.text
    result["raw"] = content[:3000]

    lines = content.splitlines()
    current_agent = "*"
    disallowed = []

    for line in lines:
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            current_agent = line.split(":", 1)[1].strip()
        elif line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path and (current_agent == "*" or "googlebot" in current_agent.lower()):
                disallowed.append(path)
        elif line.lower().startswith("sitemap:"):
            sm_url = line.split(":", 1)[1].strip()
            result["sitemap_declared"] = True
            result["sitemap_urls"].append(sm_url)

    result["disallowed_paths"] = disallowed

    # Verificar bloqueio de CSS/JS (erro clássico)
    css_js_blocked = any(
        any(p in path for p in ["/css", "/js", "/assets", "/static", "*.css", "*.js"])
        for path in disallowed
    )
    result["blocks_css_js"] = css_js_blocked

    if css_js_blocked:
        result["issues"].append({
            "severity": "🔴 CRÍTICO",
            "message":  "robots.txt bloqueia CSS e/ou JS — Google não consegue renderizar corretamente",
            "action":   "Remover regras Disallow para /css, /js, /assets ou *.css *.js",
        })

    # Verificar se não declarou sitemap
    if not result["sitemap_declared"]:
        result["issues"].append({
            "severity": "🟡 ALTO",
            "message":  "Sitemap não declarado no robots.txt",
            "action":   "Adicionar linha: Sitemap: https://seusite.com/sitemap.xml",
        })

    # Verificar bloqueio total (Disallow: /)
    if "/" in disallowed:
        result["issues"].append({
            "severity": "🔴 CRÍTICO",
            "message":  "Disallow: / bloqueia todo o site para rastreamento!",
            "action":   "Remover ou corrigir imediatamente",
        })

    return result


# ──────────────────────────────────────────
# Sitemap
# ──────────────────────────────────────────

def analyze_sitemap(site: str, robots_data: dict = None) -> dict:
    base = _normalize_url(site)

    # Encontrar URL do sitemap
    sitemap_urls = []
    if robots_data and robots_data.get("sitemap_urls"):
        sitemap_urls = robots_data["sitemap_urls"]
    else:
        sitemap_urls = [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/sitemap-index.xml",
        ]

    result = {
        "found_at":         None,
        "total_urls":       0,
        "issues":           [],
        "urls_redirect":    0,
        "urls_404":         0,
        "urls_noindex":     0,
        "last_modified":    None,
        "sample_urls":      [],
    }

    for sm_url in sitemap_urls:
        resp = _get(sm_url)
        if resp and resp.status_code == 200:
            result["found_at"] = sm_url
            content = resp.text

            # Extrair URLs
            urls = re.findall(r'<loc>(.*?)</loc>', content, re.IGNORECASE)
            result["total_urls"] = len(urls)
            result["sample_urls"] = urls[:5]

            # Última modificação
            lastmod = re.findall(r'<lastmod>(.*?)</lastmod>', content, re.IGNORECASE)
            if lastmod:
                result["last_modified"] = lastmod[0]

            # Verificar amostra de URLs (até 10) por status
            import random
            sample = random.sample(urls, min(10, len(urls)))
            for u in sample:
                r = _get(u, follow_redirects=False)
                if r:
                    if r.status_code in (301, 302, 307, 308):
                        result["urls_redirect"] += 1
                    elif r.status_code == 404:
                        result["urls_404"] += 1

            # Issues
            if result["urls_redirect"] > 0:
                result["issues"].append({
                    "severity": "🔴 CRÍTICO",
                    "message":  f"Sitemap contém ~{result['urls_redirect']} URLs com redirect (extrapolado da amostra)",
                    "action":   "Atualizar sitemap com URLs finais (sem redirects)",
                })
            if result["urls_404"] > 0:
                result["issues"].append({
                    "severity": "🔴 CRÍTICO",
                    "message":  f"Sitemap contém ~{result['urls_404']} URLs retornando 404",
                    "action":   "Remover URLs 404 do sitemap ou restaurar as páginas",
                })
            if result["total_urls"] == 0:
                result["issues"].append({
                    "severity": "🟡 ALTO",
                    "message":  "Sitemap encontrado mas está vazio",
                    "action":   "Verificar geração do sitemap",
                })

            break

    if not result["found_at"]:
        result["issues"].append({
            "severity": "🟡 ALTO",
            "message":  "Sitemap não encontrado nos caminhos padrão",
            "action":   "Criar sitemap.xml e submeter no GSC",
        })

    return result


# ──────────────────────────────────────────
# Redirects
# ──────────────────────────────────────────

def analyze_redirects(site: str, urls_to_check: list[str] = None) -> dict:
    base = _normalize_url(site)

    # URLs padrão para verificar redirect chains
    if not urls_to_check:
        # Versões HTTP e www
        parsed = urlparse(base)
        domain = parsed.netloc
        urls_to_check = [
            f"http://{domain}/",
            f"http://www.{domain}/",
            f"https://www.{domain}/",
            base + "/",
        ]

    result = {
        "https_active":         False,
        "http_to_https":        False,
        "www_redirect_correct": False,
        "chains": [],
        "issues": [],
    }

    for url in urls_to_check:
        chain = [url]
        resp  = _get(url, follow_redirects=False)

        if not resp:
            continue

        hops = 0
        current = url
        while resp and resp.status_code in (301, 302, 307, 308) and hops < 10:
            location = resp.headers.get("Location", "")
            if not location:
                break
            if location.startswith("/"):
                location = urljoin(current, location)
            chain.append(location)
            current = location
            resp    = _get(current, follow_redirects=False)
            hops   += 1

        if len(chain) > 2:
            result["chains"].append({
                "origin": url,
                "chain":  chain,
                "depth":  len(chain) - 1,
                "final":  chain[-1],
            })
            result["issues"].append({
                "severity": "🟡 ALTO",
                "message":  f"Redirect chain com {len(chain)-1} saltos: {url}",
                "action":   f"Redirecionar diretamente de {url} para {chain[-1]}",
            })

        # Verificar HTTPS
        if url.startswith("http://") and chain[-1].startswith("https://"):
            result["http_to_https"] = True

    # Verificar HTTPS ativo
    resp = _get(base)
    if resp and resp.url.startswith("https://"):
        result["https_active"] = True

    if not result["https_active"]:
        result["issues"].append({
            "severity": "🔴 CRÍTICO",
            "message":  "HTTPS não ativo",
            "action":   "Ativar SSL/TLS imediatamente",
        })

    if not result["http_to_https"] and result["https_active"]:
        result["issues"].append({
            "severity": "🟡 ALTO",
            "message":  "HTTP não redireciona para HTTPS",
            "action":   "Configurar redirect 301 de HTTP → HTTPS",
        })

    return result


# ──────────────────────────────────────────
# Canonicals e segurança básica
# ──────────────────────────────────────────

def analyze_page_basics(url: str) -> dict:
    """Analisa uma URL: canonical, noindex, title, meta description, H1."""
    resp = _get(url)
    if not resp or resp.status_code != 200:
        return {"url": url, "status": resp.status_code if resp else "timeout"}

    from html.parser import HTMLParser

    class HeadParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.canonical    = None
            self.noindex      = False
            self.title        = ""
            self.description  = ""
            self.h1           = ""
            self._in_title    = False
            self._in_body     = False

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "link" and attrs.get("rel") == "canonical":
                self.canonical = attrs.get("href")
            if tag == "meta":
                if attrs.get("name", "").lower() == "robots":
                    if "noindex" in attrs.get("content", "").lower():
                        self.noindex = True
                if attrs.get("name", "").lower() == "description":
                    self.description = attrs.get("content", "")
            if tag == "title":
                self._in_title = True
            if tag == "body":
                self._in_body = True
            if tag == "h1" and self._in_body:
                self._in_h1 = True

        def handle_data(self, data):
            if self._in_title:
                self.title += data
            if getattr(self, "_in_h1", False):
                self.h1 += data

        def handle_endtag(self, tag):
            if tag == "title":
                self._in_title = False
            if tag == "h1":
                self._in_h1 = False

    parser = HeadParser()
    parser.feed(resp.text[:50000])

    issues = []
    if not parser.canonical:
        issues.append({"severity": "🟢 MÉDIO", "message": "Sem canonical tag"})
    if parser.noindex:
        issues.append({"severity": "⚪ INFO", "message": "Página com noindex"})
    if not parser.title:
        issues.append({"severity": "🟡 ALTO", "message": "Sem title tag"})
    if not parser.description:
        issues.append({"severity": "🟡 ALTO", "message": "Sem meta description"})
    if not parser.h1:
        issues.append({"severity": "🟢 MÉDIO", "message": "Sem H1"})

    return {
        "url":         url,
        "status_code": resp.status_code,
        "canonical":   parser.canonical,
        "noindex":     parser.noindex,
        "title":       parser.title.strip()[:80],
        "description": parser.description[:160],
        "h1":          parser.h1.strip()[:100],
        "issues":      issues,
    }


# ──────────────────────────────────────────
# Análise completa (Módulo 12)
# ──────────────────────────────────────────

def full_analysis(site: str, use_cache: bool = True) -> dict:
    cache_path = _cache_path(site, "full")
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    robots   = analyze_robots(site)
    sitemap  = analyze_sitemap(site, robots)
    redirects = analyze_redirects(site)
    page     = analyze_page_basics(_normalize_url(site))

    all_issues = (
        robots.get("issues", []) +
        sitemap.get("issues", []) +
        redirects.get("issues", []) +
        page.get("issues", [])
    )

    # Score técnico
    critical = sum(1 for i in all_issues if "CRÍTICO" in i.get("severity", ""))
    high     = sum(1 for i in all_issues if "ALTO" in i.get("severity", ""))
    medium   = sum(1 for i in all_issues if "MÉDIO" in i.get("severity", ""))

    score = max(0, 100 - (critical * 20) - (high * 8) - (medium * 3))

    result = {
        "site":           site,
        "technical_score": score,
        "robots":         robots,
        "sitemap":        sitemap,
        "redirects":      redirects,
        "homepage":       page,
        "all_issues":     all_issues,
        "counts": {
            "critical": critical,
            "high":     high,
            "medium":   medium,
        },
        "status": "ok",
    }

    _save_cache(cache_path, result)
    return result


def to_markdown(data: dict) -> str:
    """Formata análise técnica como Markdown."""
    site  = data.get("site", "")
    score = data.get("technical_score", 0)
    lines = [f"## MÓDULO 12 — SEO TÉCNICO", ""]
    lines.append(f"### Score Técnico: {score}/100")
    lines.append("")

    all_issues = data.get("all_issues", [])
    if not all_issues:
        lines.append("✅ Nenhum problema técnico crítico identificado.")
    else:
        lines.append("### Issues Identificados")
        lines.append("")
        for issue in sorted(all_issues, key=lambda i: (
            0 if "CRÍTICO" in i.get("severity","") else
            1 if "ALTO" in i.get("severity","") else
            2 if "MÉDIO" in i.get("severity","") else 3
        )):
            lines.append(f"{issue['severity']} — {issue['message']}")
            if issue.get("action"):
                lines.append(f"  → Ação: {issue['action']}")
        lines.append("")

    # robots.txt
    robots = data.get("robots", {})
    lines.append("### robots.txt")
    lines.append("")
    lines.append(f"| Item | Status |")
    lines.append(f"|---|---|")
    lines.append(f"| Existe | {'✅' if robots.get('exists') else '❌'} |")
    lines.append(f"| Sitemap declarado | {'✅' if robots.get('sitemap_declared') else '❌'} |")
    lines.append(f"| Bloqueia CSS/JS | {'🔴 Sim' if robots.get('blocks_css_js') else '✅ Não'} |")
    lines.append("")

    # Sitemap
    sm = data.get("sitemap", {})
    lines.append("### Sitemap")
    lines.append("")
    lines.append(f"| Item | Valor |")
    lines.append(f"|---|---|")
    lines.append(f"| Encontrado em | {sm.get('found_at') or '❌ Não encontrado'} |")
    lines.append(f"| Total de URLs | {sm.get('total_urls', 0)} |")
    lines.append(f"| URLs com redirect | {sm.get('urls_redirect', 0)} {'🔴' if sm.get('urls_redirect',0) > 0 else '✅'} |")
    lines.append(f"| URLs 404 | {sm.get('urls_404', 0)} {'🔴' if sm.get('urls_404',0) > 0 else '✅'} |")
    lines.append(f"| Última modificação | {sm.get('last_modified', 'N/D')} |")
    lines.append("")

    # HTTPS
    rd = data.get("redirects", {})
    lines.append("### HTTPS & Redirects")
    lines.append("")
    lines.append(f"| Item | Status |")
    lines.append(f"|---|---|")
    lines.append(f"| HTTPS ativo | {'✅' if rd.get('https_active') else '🔴 Não'} |")
    lines.append(f"| HTTP → HTTPS | {'✅' if rd.get('http_to_https') else '⚠️ Verificar'} |")
    chains = rd.get("chains", [])
    lines.append(f"| Redirect chains | {'🔴 ' + str(len(chains)) + ' detectadas' if chains else '✅ Nenhuma'} |")
    lines.append("")

    # Homepage
    hp = data.get("homepage", {})
    lines.append("### Homepage — Elementos Básicos")
    lines.append("")
    lines.append(f"| Elemento | Status | Valor |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Title | {'✅' if hp.get('title') else '❌'} | {hp.get('title','N/D')[:60]} |")
    lines.append(f"| Meta Description | {'✅' if hp.get('description') else '❌'} | {hp.get('description','N/D')[:80]} |")
    lines.append(f"| Canonical | {'✅' if hp.get('canonical') else '⚠️'} | {hp.get('canonical','N/D')[:60]} |")
    lines.append(f"| H1 | {'✅' if hp.get('h1') else '❌'} | {hp.get('h1','N/D')[:60]} |")
    lines.append(f"| Noindex | {'⚠️ Sim' if hp.get('noindex') else '✅ Não'} | — |")
    lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SEO Technical Analyzer")
    parser.add_argument("--site",     required=True)
    parser.add_argument("--report",   default="full",
                        choices=["full","robots","sitemap","redirects","page"])
    parser.add_argument("--url",      help="URL específica para análise de página")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--md",       action="store_true", help="Output em Markdown")
    args = parser.parse_args()

    use_cache = not args.no_cache

    if args.report == "full":
        data = full_analysis(args.site, use_cache)
        if args.md:
            print(to_markdown(data))
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    elif args.report == "robots":
        print(json.dumps(analyze_robots(args.site), ensure_ascii=False, indent=2))
    elif args.report == "sitemap":
        print(json.dumps(analyze_sitemap(args.site), ensure_ascii=False, indent=2))
    elif args.report == "redirects":
        print(json.dumps(analyze_redirects(args.site), ensure_ascii=False, indent=2))
    elif args.report == "page":
        url = args.url or _normalize_url(args.site)
        print(json.dumps(analyze_page_basics(url), ensure_ascii=False, indent=2))
