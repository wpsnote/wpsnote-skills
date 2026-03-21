#!/usr/bin/env python3
"""
paper.py - 论文搜索与下载命令行工具

用法：
    python3 paper.py search "transformer attention"
    python3 paper.py search "LoRA fine-tuning" --source openalex --top 5
    python3 paper.py get 1706.03762
    python3 paper.py get 1706.03762 --output ~/Desktop

依赖：
    pip install arxiv markitdown pymupdf
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
# arXiv 搜索
# ─────────────────────────────────────────────

def search_arxiv(query: str, top: int = 10, category: Optional[str] = None) -> list:
    try:
        import arxiv
    except ImportError:
        print("❌ 缺少依赖：pip install arxiv")
        sys.exit(1)

    search_query = f"cat:{category} AND ({query})" if category else query
    fetch = min(top * 3, 50)

    client = arxiv.Client(page_size=20, delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=search_query,
        max_results=fetch,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    now = datetime.now()
    for idx, paper in enumerate(client.results(search)):
        arxiv_id = paper.entry_id.split("/")[-1]
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.rsplit("v", 1)[0]

        days_ago = (now - paper.published.replace(tzinfo=None)).days
        relevance = 1.0 / (1.0 + idx * 0.1)
        time_score = 1.0 / (1.0 + days_ago / 180)
        score = 0.6 * relevance + 0.4 * time_score

        results.append({
            "id": arxiv_id,
            "title": paper.title.replace("\n", " "),
            "abstract": paper.summary.replace("\n", " "),
            "authors": [a.name for a in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d"),
            "categories": paper.categories,
            "pdf_url": paper.pdf_url,
            "source": "arxiv",
            "_score": score,
        })

    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:top]


# ─────────────────────────────────────────────
# OpenAlex 搜索
# ─────────────────────────────────────────────

_OA_HEADERS = {
    "User-Agent": "paper-cli/1.0 (https://github.com/itshen/paper_reader)",
    "Accept": "application/json",
}


def _oa_get(url: str) -> dict:
    req = urllib.request.Request(url, headers=_OA_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _rebuild_abstract(inverted: Optional[dict]) -> str:
    if not inverted:
        return ""
    positions = []
    for word, pos_list in inverted.items():
        for pos in pos_list:
            positions.append((pos, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in positions)


def search_openalex(query: str, top: int = 10) -> list:
    fields = (
        "id,ids,title,abstract_inverted_index,authorships,"
        "publication_date,open_access,primary_location,"
        "best_oa_location,cited_by_count,topics"
    )
    params = urllib.parse.urlencode({
        "search": query,
        "filter": "open_access.is_oa:true",
        "sort": "relevance_score:desc",
        "per-page": min(top * 3, 100),
        "select": fields,
    })
    url = f"https://api.openalex.org/works?{params}"

    try:
        data = _oa_get(url)
    except Exception as e:
        print(f"❌ OpenAlex 请求失败: {e}")
        return []

    now = datetime.now()
    results_raw = data.get("results") or []
    results = []
    max_cite = max((w.get("cited_by_count") or 0 for w in results_raw), default=1) or 1

    for idx, w in enumerate(results_raw):
        ids = w.get("ids", {}) or {}
        arxiv_raw = ids.get("arxiv", "") or ""
        oa_id = w.get("id", "").split("/")[-1]
        paper_id = arxiv_raw.replace("https://arxiv.org/abs/", "").strip() if arxiv_raw else f"oa_{oa_id}"

        pdf_url = ""
        for loc_key in ("primary_location", "best_oa_location"):
            loc = w.get(loc_key) or {}
            if loc.get("pdf_url"):
                pdf_url = loc["pdf_url"]
                break
        if not pdf_url:
            oa = w.get("open_access") or {}
            pdf_url = oa.get("oa_url") or ""
        if not pdf_url and arxiv_raw:
            aid = arxiv_raw.replace("https://arxiv.org/abs/", "").strip()
            pdf_url = f"https://arxiv.org/pdf/{aid}"

        pub_date = w.get("publication_date") or str(w.get("publication_year", ""))
        try:
            pub_dt = datetime.strptime(pub_date[:10], "%Y-%m-%d")
            days_ago = (now - pub_dt).days
            time_score = 1.0 / (1.0 + days_ago / 180)
        except Exception:
            time_score = 0.5

        relevance = 1.0 / (1.0 + idx * 0.1)
        cite = (w.get("cited_by_count") or 0) / max_cite
        score = 0.5 * relevance + 0.3 * time_score + 0.2 * cite

        topics = w.get("topics") or []
        domains = list(dict.fromkeys(
            t.get("domain", {}).get("display_name", "")
            for t in topics if t.get("domain")
        ))

        results.append({
            "id": paper_id,
            "title": (w.get("title") or "").replace("\n", " ").strip(),
            "abstract": _rebuild_abstract(w.get("abstract_inverted_index")),
            "authors": [
                a.get("author", {}).get("display_name", "")
                for a in w.get("authorships", [])
                if a.get("author", {}).get("display_name")
            ],
            "published": pub_date[:10] if pub_date else "",
            "categories": domains[:3] or ["unknown"],
            "pdf_url": pdf_url,
            "citation_count": w.get("cited_by_count"),
            "source": "openalex",
            "_score": score,
        })

    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:top]


# ─────────────────────────────────────────────
# PDF 下载
# ─────────────────────────────────────────────

def _verify_pdf(path: str) -> bool:
    if not os.path.exists(path):
        return False
    if os.path.getsize(path) < 10000:
        return False
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            if not header.startswith(b"%PDF"):
                return False
            f.seek(-128, 2)
            return b"%%EOF" in f.read()
    except Exception:
        return False


def download_pdf(paper_id: str, pdf_url: str, output_dir: str) -> Optional[str]:
    os.makedirs(output_dir, exist_ok=True)
    safe_id = paper_id.replace("/", "_").replace(":", "_")
    save_path = os.path.join(output_dir, f"{safe_id}.pdf")

    if _verify_pdf(save_path):
        print(f"✅ 已存在: {save_path}")
        return save_path

    if not paper_id.startswith("oa_") and not pdf_url.startswith("http"):
        pdf_url = f"https://arxiv.org/pdf/{paper_id}"

    print(f"⬇️  下载中: {pdf_url}")

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                pdf_url,
                headers={
                    **_OA_HEADERS,
                    "User-Agent": "Mozilla/5.0 (compatible; paper-cli/1.0)",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()

            if len(content) < 10000:
                print(f"   内容太小 ({len(content)} bytes)，跳过")
                return None

            with open(save_path, "wb") as f:
                f.write(content)

            if _verify_pdf(save_path):
                print(f"✅ 已保存: {save_path}")
                return save_path
            else:
                os.remove(save_path)
                print(f"   PDF 校验失败，重试...")

        except Exception as e:
            print(f"   下载失败 (尝试 {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep((attempt + 1) * 2)

    return None


# ─────────────────────────────────────────────
# PDF → Markdown
# ─────────────────────────────────────────────

def convert_pdf(pdf_path: str) -> str:
    # 方法 1: markitdown
    try:
        from markitdown import MarkItDown
        result = MarkItDown().convert(pdf_path)
        text = result.text_content
        if text and len(text.strip()) > 100:
            return text
    except Exception:
        pass

    # 方法 2: pymupdf
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        parts = []
        for i, page in enumerate(doc, 1):
            t = page.get_text()
            if t.strip():
                parts.append(f"## Page {i}\n\n{t}")
        doc.close()
        if parts:
            return "\n\n---\n\n".join(parts)
    except Exception:
        pass

    print("⚠️  无法提取文本（可能是扫描版 PDF）")
    return ""


# ─────────────────────────────────────────────
# 命令：search
# ─────────────────────────────────────────────

def cmd_search(args):
    query = args.query
    source = args.source
    top = args.top

    print(f"\n🔍 搜索：{query!r}  来源：{source}  数量：{top}\n")

    if source == "openalex":
        papers = search_openalex(query, top=top)
    else:
        papers = search_arxiv(query, top=top, category=args.category)

    if not papers:
        print("未找到相关论文，换个关键词试试。")
        return

    for i, p in enumerate(papers, 1):
        authors = p["authors"][:3]
        if len(p["authors"]) > 3:
            authors.append(f"等 {len(p['authors'])} 人")

        print(f"{'─'*60}")
        print(f"[{i}] {p['title']}")
        print(f"    ID      : {p['id']}")
        print(f"    作者    : {', '.join(authors)}")
        print(f"    日期    : {p['published']}")
        print(f"    分类    : {', '.join(p['categories'][:3])}")
        if p.get("citation_count") is not None:
            print(f"    引用数  : {p['citation_count']}")
        abstract = p["abstract"]
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        print(f"    摘要    : {abstract}")
        print()

    print(f"{'─'*60}")
    print(f"💡 下载全文：python3 paper.py get <ID>")
    if source == "openalex":
        print(f"   示例：python3 paper.py get {papers[0]['id']} --source openalex")
    else:
        print(f"   示例：python3 paper.py get {papers[0]['id']}")


# ─────────────────────────────────────────────
# 命令：get
# ─────────────────────────────────────────────

def cmd_get(args):
    paper_id = args.paper_id
    output_dir = os.path.expanduser(args.output)
    source = args.source
    to_md = args.markdown

    print(f"\n📄 获取论文：{paper_id}  来源：{source}\n")

    pdf_url = ""
    if source == "openalex":
        print("🔎 查询 OpenAlex 元数据...")
        try:
            url = f"https://api.openalex.org/works/https://doi.org/10.48550/arXiv.{paper_id}"
            data = _oa_get(url)
            loc = data.get("primary_location") or data.get("best_oa_location") or {}
            pdf_url = loc.get("pdf_url") or (data.get("open_access") or {}).get("oa_url") or ""
        except Exception:
            pass
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{paper_id}"
    else:
        pdf_url = f"https://arxiv.org/pdf/{paper_id}"

    pdf_path = download_pdf(paper_id, pdf_url, output_dir)
    if not pdf_path:
        print("❌ 下载失败")
        sys.exit(1)

    if to_md:
        print("📝 转换为 Markdown...")
        text = convert_pdf(pdf_path)
        if text:
            md_path = pdf_path.replace(".pdf", ".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ Markdown 已保存: {md_path}")
        else:
            print("❌ 转换失败")


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="paper",
        description="论文搜索与下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 paper.py search "transformer attention"
  python3 paper.py search "LoRA" --source openalex --top 5
  python3 paper.py search "diffusion model" --category cs.CV
  python3 paper.py get 1706.03762
  python3 paper.py get 1706.03762 --output ~/Desktop --markdown
        """,
    )

    sub = parser.add_subparsers(dest="cmd")

    p_search = sub.add_parser("search", help="搜索论文")
    p_search.add_argument("query", help="搜索关键词（建议英文）")
    p_search.add_argument("--source", choices=["arxiv", "openalex"], default="arxiv",
                          help="数据来源，默认 arxiv")
    p_search.add_argument("--top", type=int, default=10, help="返回数量，默认 10")
    p_search.add_argument("--category", help="arXiv 分类过滤，如 cs.AI cs.LG cs.CV（仅 arxiv 有效）")

    p_get = sub.add_parser("get", help="下载论文 PDF")
    p_get.add_argument("paper_id", help="论文 ID，如 1706.03762")
    p_get.add_argument("--source", choices=["arxiv", "openalex"], default="arxiv",
                       help="数据来源，默认 arxiv")
    p_get.add_argument("--output", default="./papers", help="保存目录，默认 ./papers")
    p_get.add_argument("--markdown", action="store_true", help="同时转换为 Markdown 文本")

    args = parser.parse_args()

    if args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "get":
        cmd_get(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
