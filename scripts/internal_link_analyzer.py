#!/usr/bin/env python3
"""
internal_link_analyzer.py
Módulo 13 — Arquitetura e Links Internos.
Detecta: páginas órfãs, profundidade de cliques, distribuição de PageRank interno.
"""

import os
import re
import json
import hashlib
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from pathlib import Path
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.getenv("SEO_SKILL_CACHE_DIR", "./cache"))
CACHE_TTL = 86400

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOIntelBot/1.0)"}


def _cache_path(site: str) -> Path:
    key = hashlib.md5(site.encode()).hexdigest()[:12]
    return CACHE_DIR / f"internal-links-{key}.json"


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


def _normalize(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def _same_domain(url: str, base_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        return base_domain in parsed.netloc
    except Exception:
        return False


def _extract_links(html: str, base_url: str, base_domain: str) -> list[tuple[str, str]]:
    """Extrai links internos com anchor text."""
    from html.parser import HTMLParser

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
            self._current_href = None
            self._current_text = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                attrs_dict = dict(attrs)
                href = attrs_dict.get("href", "")
                if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                    self._current_href = href
                    self._current_text = []

        def handle_data(self, data):
            if self._current_href:
                self._current_text.append(data.strip())

        def handle_endtag(self, tag):
            if tag == "a" and self._current_href:
                anchor = " ".join(self._current_text).strip()[:80]
                self.links.append((self._current_href, anchor))
                self._current_href = None
                self._current_text = []

    parser = LinkParser()
    parser.feed(html)

    resolved = []
    for href, anchor in parser.links:
        try:
            full_url = urljoin(base_url, href).rstrip("/")
            if _same_domain(full_url, base_domain):
                # Remover fragmentos
                full_url = full_url.split("#")[0]
                if full_url:
                    resolved.append((full_url, anchor))
        except Exception:
            pass
    return resolved


def crawl_site(base_url: str, max_pages: int = 60) -> dict:
    """
    Mini-crawler para mapear links internos.
    Limita a max_pages para ser gentil com o servidor.
    """
    base_url    = _normalize(base_url)
    base_domain = urlparse(base_url).netloc

    visited      = {}   # url → {links_out, links_in, depth, anchors_in}
    queue        = deque([(base_url, 0)])
    seen         = {base_url}
    links_in     = defaultdict(list)   # url → [(from_url, anchor)]
    links_out    = defaultdict(list)   # url → [to_url]

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()

        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code != 200:
                visited[url] = {"depth": depth, "status": resp.status_code,
                                "links_out": [], "links_in_count": 0}
                continue

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                continue

            page_links = _extract_links(resp.text, url, base_domain)
            out_urls   = [l[0] for l in page_links]

            visited[url] = {
                "depth":    depth,
                "status":   200,
                "links_out": list(set(out_urls))[:50],
            }
            links_out[url] = out_urls

            for to_url, anchor in page_links:
                links_in[to_url].append({"from": url, "anchor": anchor})
                if to_url not in seen:
                    seen.add(to_url)
                    queue.append((to_url, depth + 1))

        except requests.Timeout:
            visited[url] = {"depth": depth, "status": "timeout", "links_out": []}
        except Exception as e:
            visited[url] = {"depth": depth, "status": "error", "links_out": []}

    return {
        "base_url":   base_url,
        "pages_crawled": len(visited),
        "visited":    visited,
        "links_in":   dict(links_in),
        "links_out":  dict(links_out),
    }


def analyze(site: str, gsc_pages: list[str] = None, use_cache: bool = True) -> dict:
    """
    Análise completa de links internos.
    gsc_pages: lista de páginas indexadas (do GSC) para detectar órfãs.
    """
    cache_path = _cache_path(site)
    if use_cache:
        cached = _load_cache(cache_path)
        if cached:
            cached["_from_cache"] = True
            return cached

    crawl = crawl_site(site, max_pages=60)
    visited  = crawl["visited"]
    links_in = crawl["links_in"]

    base_url = _normalize(site)

    # ── Páginas órfãs (crawled mas sem links internos chegando)
    orphans = []
    for url, data in visited.items():
        if url == base_url:
            continue  # Home nunca é órfã
        in_count = len(links_in.get(url, []))
        if in_count == 0 and data.get("status") == 200:
            orphans.append({"url": url, "depth": data.get("depth", 0)})

    # Adicionar páginas do GSC não encontradas no crawl (também órfãs ou pouco linkadas)
    gsc_orphans = []
    if gsc_pages:
        crawled_set = set(visited.keys())
        for page in gsc_pages:
            page_norm = page.rstrip("/")
            if page_norm not in crawled_set and page_norm != base_url:
                gsc_orphans.append({"url": page, "source": "GSC — não encontrada no crawl"})

    # ── Páginas por profundidade
    depth_dist = defaultdict(int)
    deep_pages = []
    for url, data in visited.items():
        d = data.get("depth", 0)
        depth_dist[d] += 1
        if d > 3 and data.get("status") == 200:
            deep_pages.append({"url": url, "depth": d})

    deep_pages.sort(key=lambda p: -p["depth"])

    # ── Top páginas por links internos recebidos
    top_linked = sorted(
        [(url, len(ins)) for url, ins in links_in.items()],
        key=lambda x: -x[1]
    )[:15]

    # ── Análise de anchor texts
    all_anchors = []
    for ins in links_in.values():
        for link in ins:
            all_anchors.append(link.get("anchor", "").lower())

    generic_terms = ["clique aqui", "saiba mais", "leia mais", "veja mais",
                     "acesse", "aqui", "click here", "read more", "here", "link"]
    generic_count  = sum(1 for a in all_anchors if any(g in a for g in generic_terms))
    total_anchors  = len(all_anchors)
    generic_pct    = round(generic_count / total_anchors * 100) if total_anchors else 0

    # ── Score de arquitetura
    orphan_penalty  = min(40, len(orphans) * 3)
    deep_penalty    = min(20, len(deep_pages) * 4)
    anchor_penalty  = min(20, generic_pct // 4)
    arch_score      = max(0, 100 - orphan_penalty - deep_penalty - anchor_penalty)

    issues = []
    if orphans or gsc_orphans:
        total_orphans = len(orphans) + len(gsc_orphans)
        issues.append({
            "severity": "🔴 CRÍTICO",
            "message":  f"{total_orphans} páginas órfãs (sem links internos apontando)",
            "action":   "Mapear e adicionar links internos relevantes para cada uma",
        })
    if deep_pages:
        issues.append({
            "severity": "🟡 ALTO",
            "message":  f"{len(deep_pages)} páginas com profundidade > 3 cliques do home",
            "action":   "Adicionar links diretos da home ou seções principais",
        })
    if generic_pct > 40:
        issues.append({
            "severity": "🟡 ALTO",
            "message":  f"{generic_pct}% dos anchor texts são genéricos ('clique aqui', 'saiba mais')",
            "action":   "Reescrever anchors dos 20 links mais importantes com texto descritivo",
        })

    result = {
        "site":           site,
        "arch_score":     arch_score,
        "pages_crawled":  len(visited),
        "orphan_pages":   orphans[:20],
        "gsc_orphans":    gsc_orphans[:10],
        "deep_pages":     deep_pages[:10],
        "depth_dist":     dict(depth_dist),
        "top_linked":     [{"url": u, "links_in": c} for u, c in top_linked],
        "anchor_stats": {
            "total":        total_anchors,
            "generic":      generic_count,
            "generic_pct":  generic_pct,
        },
        "issues":         issues,
        "status":         "ok",
    }

    _save_cache(cache_path, result)
    return result


def to_markdown(data: dict) -> str:
    score = data.get("arch_score", 0)
    lines = ["## MÓDULO 13 — ARQUITETURA E LINKS INTERNOS", "",
             f"### Score de Arquitetura: {score}/100", ""]

    issues = data.get("issues", [])
    if issues:
        lines += ["### Issues Identificados", ""]
        for issue in issues:
            lines.append(f"{issue['severity']} — {issue['message']}")
            if issue.get("action"):
                lines.append(f"  → Ação: {issue['action']}")
        lines.append("")

    # Profundidade
    depth_dist = data.get("depth_dist", {})
    if depth_dist:
        lines += ["### Distribuição por Profundidade (cliques do home)", "",
                  "| Profundidade | Páginas |",
                  "|---|---|"]
        for depth in sorted(depth_dist.keys()):
            flag = " ⚠️" if int(depth) > 3 else ""
            lines.append(f"| {depth} cliques | {depth_dist[depth]} páginas{flag} |")
        lines.append("")

    # Top linkadas
    top = data.get("top_linked", [])
    if top:
        lines += ["### Top 10 Páginas Mais Linkadas Internamente", "",
                  "| URL | Links Recebidos |",
                  "|---|---|"]
        for item in top[:10]:
            lines.append(f"| {item['url'][:60]} | {item['links_in']} |")
        lines.append("")

    # Órfãs
    orphans = data.get("orphan_pages", []) + data.get("gsc_orphans", [])
    if orphans:
        lines += ["### Páginas Órfãs (sem links internos)", "",
                  "| URL | Profundidade |",
                  "|---|---|"]
        for o in orphans[:10]:
            depth = o.get("depth", "N/D")
            lines.append(f"| {o['url'][:60]} | {depth} |")
        lines.append("")

    # Anchors
    anchors = data.get("anchor_stats", {})
    if anchors:
        lines += ["### Qualidade dos Anchor Texts", "",
                  f"| Total de links analisados | {anchors.get('total', 0)} |",
                  "|---|---|",
                  f"| Anchors genéricos | {anchors.get('generic', 0)} ({anchors.get('generic_pct', 0)}%) |",
                  f"| Anchors descritivos | {anchors.get('total',0) - anchors.get('generic',0)} ({100 - anchors.get('generic_pct',0)}%) |",
                  ""]

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Internal Link Analyzer")
    parser.add_argument("--site",     required=True)
    parser.add_argument("--max-pages", type=int, default=60)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--md",       action="store_true")
    args = parser.parse_args()

    data = analyze(args.site, use_cache=not args.no_cache)
    print(to_markdown(data) if args.md else json.dumps(data, ensure_ascii=False, indent=2))
