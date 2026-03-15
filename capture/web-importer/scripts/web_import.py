#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
web_import.py — 网页内容爬取统一入口
自动识别 URL 类型，分发给对应的爬取脚本：
  - 微信公众号 (mp.weixin.qq.com) → download_articles.py
  - X/Twitter (x.com, twitter.com) → twitter_import.py
  - 其他通用网页                   → web_to_md.py

用法：
  python3.11 web_import.py "https://mp.weixin.qq.com/s/xxxxx"
  python3.11 web_import.py "https://x.com/user/status/xxx" --wps
  python3.11 web_import.py "https://example.com/article"
  python3.11 web_import.py "URL" -o 自定义目录名
  python3.11 web_import.py "URL" -d /path/to/output/root
  python3.11 web_import.py "URL" -f 1   # 通用网页过滤级别 0/1/2（默认2）

输出：
  <输出目录>/
    ├── content.md      正文 Markdown（含来源、标题元信息）
    ├── original.html   原始 HTML 备份
    └── images/         下载的图片

依赖安装：
  pip3.11 install requests beautifulsoup4 readability-lxml markdownify lxml
  # X/Twitter 额外依赖：
  pip3.11 install playwright
  python3.11 -m playwright install chromium
"""

import sys
import os
import argparse
from urllib.parse import urlparse


def is_wechat_url(url: str) -> bool:
    """判断是否为微信公众号文章链接"""
    try:
        parsed = urlparse(url)
        return 'mp.weixin.qq.com' in parsed.netloc
    except Exception:
        return False


def is_twitter_url(url: str) -> bool:
    """判断是否为 X/Twitter 推文链接"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip('www.')
        return domain in ('x.com', 'twitter.com')
    except Exception:
        return False


def run_wechat(url: str, output_root: str, custom_dir: str | None,
               import_wps: bool = False) -> bool:
    """调用微信公众号爬取模块"""
    # 将 download_articles.py 的核心逻辑以模块方式引用
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)

    try:
        import download_articles as da
    except ImportError:
        print("[错误] 找不到 download_articles.py，请确认脚本在同一目录下")
        return False

    if not da.validate_wechat_url(url):
        print("[错误] 无效的微信公众号文章链接")
        return False

    os.makedirs(output_root, exist_ok=True)
    print(f"[微信] 检测到公众号文章，使用微信专用爬取模块")
    if import_wps:
        print(f"[微信] WPS 高质量模式：保留颜色/粗体/标题格式")
    print(f"[微信] 输出目录：{os.path.abspath(output_root)}\n")

    success = da.download_article_from_url(url, output_root, import_wps=import_wps)

    if success:
        # download_articles.py 使用 MMDD_标题 的子目录，找到它并重命名为 content.md
        # 兼容：将 终稿.md 复制一份为 content.md（方便 Skill 统一读取）
        _normalize_wechat_output(output_root)

    return success


def _normalize_wechat_output(output_root: str):
    """将微信模块的输出目录规范化，在根目录生成统一的 content.md 入口"""
    import glob

    # 找到最新创建的子目录
    subdirs = [
        d for d in os.listdir(output_root)
        if os.path.isdir(os.path.join(output_root, d))
    ]
    if not subdirs:
        return

    # 取最新修改的子目录
    latest = max(
        subdirs,
        key=lambda d: os.path.getmtime(os.path.join(output_root, d))
    )
    article_dir = os.path.join(output_root, latest)
    draft_md = os.path.join(article_dir, '终稿.md')

    if os.path.exists(draft_md):
        # 在文章子目录创建 content.md 软链接或副本
        content_md = os.path.join(article_dir, 'content.md')
        if not os.path.exists(content_md):
            import shutil
            shutil.copy2(draft_md, content_md)
        print(f"[微信] content.md 已创建：{content_md}")


def run_twitter(url: str, output_root: str, import_wps: bool = False) -> bool:
    """调用 X/Twitter 爬取模块"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)

    try:
        import twitter_import as ti
    except ImportError:
        print("[错误] 找不到 twitter_import.py，请确认脚本在同一目录下")
        return False

    os.makedirs(output_root, exist_ok=True)
    print(f"[X/Twitter] 检测到 X 推文链接，使用 Twitter 专用爬取模块")
    if import_wps:
        print(f"[X/Twitter] WPS 高质量模式：原样复制推文内容到笔记")
    print(f"[X/Twitter] 输出目录：{os.path.abspath(output_root)}\n")

    return ti.scrape_twitter(url, output_root=output_root, import_wps=import_wps)


def run_generic(url: str, output_root: str, custom_dir: str | None,
                filter_level: int, import_wps: bool = False) -> bool:
    """调用通用网页爬取模块"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)

    try:
        import web_to_md as wtm
    except ImportError:
        print("[错误] 找不到 web_to_md.py，请确认脚本在同一目录下")
        return False

    print(f"[通用] 使用通用网页爬取模块")
    print(f"[通用] 过滤级别：{filter_level}（0=最小 1=中等 2=激进）")
    if import_wps:
        print(f"[通用] WPS 高质量模式：保留颜色/粗体/标题格式\n")
    else:
        print()

    return wtm.scrape_url(
        url,
        output_root=output_root,
        custom_dir_name=custom_dir,
        filter_level=filter_level,
        import_wps=import_wps,
    )


def main():
    parser = argparse.ArgumentParser(
        description='网页内容爬取统一入口 — 自动识别微信公众号或通用网页',
        epilog=(
            '示例：\n'
            '  python3.11 web_import.py "https://mp.weixin.qq.com/s/xxxxx"\n'
            '  python3.11 web_import.py "https://example.com/article" -f 1\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('url', help='要爬取的网页 URL')
    parser.add_argument('-o', '--output', help='自定义输出目录名（可选）', default=None)
    parser.add_argument('-d', '--dir', help='输出根目录路径（可选）', default=None)
    parser.add_argument(
        '-f', '--filter',
        type=int, choices=[0, 1, 2], default=2,
        help='通用网页内容过滤级别：0=最小 1=中等 2=激进（默认2，仅通用网页有效）'
    )
    parser.add_argument(
        '--wps', action='store_true',
        help='高质量模式：保留颜色/粗体/标题格式直接导入 WPS 笔记（需要 wpsnote-cli）'
    )

    args = parser.parse_args()
    url = args.url.strip()

    if not url.startswith(('http://', 'https://')):
        print("[错误] 请提供有效的 URL（以 http:// 或 https:// 开头）")
        sys.exit(1)

    # 默认输出根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.join(script_dir, '..', '..', '..', '爬取内容')
    output_root = args.dir or default_root

    if is_wechat_url(url):
        success = run_wechat(url, output_root, args.output, import_wps=args.wps)
    elif is_twitter_url(url):
        success = run_twitter(url, output_root, import_wps=args.wps)
    else:
        success = run_generic(url, output_root, args.output, args.filter, import_wps=args.wps)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
