#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
twitter_import.py — X (Twitter) 推文 / Thread 专用爬取模块

X 的内容是 JS 动态渲染的，普通 requests 抓取只能拿到空壳。
本模块使用 Playwright 渲染完整页面，然后提取推文正文。

支持：
  - 单条推文
  - 长文 Thread（自动展开同一作者的回复链）
  - 嵌入图片（下载到本地）
  - 原样复制到 WPS 笔记（--wps 模式）

用法：
  python3.11 twitter_import.py "https://x.com/user/status/xxx" --wps
  python3.11 twitter_import.py "https://twitter.com/user/status/xxx" --wps

依赖安装：
  pip3.11 install playwright beautifulsoup4 requests
  python3.11 -m playwright install chromium
"""

import sys
import os
import re
import time
import datetime
import argparse
import requests
from urllib.parse import urlparse, urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[错误] 请安装: pip3.11 install beautifulsoup4")
    sys.exit(1)


# ============================================================
# 配置
# ============================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 等待主推文加载的超时（毫秒）
PAGE_TIMEOUT = 30000
# 展开 Thread 时每次滚动后的等待（秒）
THREAD_SCROLL_WAIT = 2
# 最多爬取 Thread 中的推文数量
MAX_THREAD_TWEETS = 50


# ============================================================
# URL 工具
# ============================================================

def is_twitter_url(url: str) -> bool:
    """判断是否为 X/Twitter 推文链接"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip('www.')
        return domain in ('x.com', 'twitter.com')
    except Exception:
        return False


def normalize_twitter_url(url: str) -> str:
    """将 twitter.com 链接统一转为 x.com"""
    return url.replace('twitter.com', 'x.com', 1)


def extract_tweet_id(url: str) -> str | None:
    """从 URL 提取 tweet id"""
    m = re.search(r'/status/(\d+)', url)
    return m.group(1) if m else None


def extract_username(url: str) -> str | None:
    """从 URL 提取用户名"""
    m = re.search(r'x\.com/([^/]+)/status', url)
    if not m:
        m = re.search(r'twitter\.com/([^/]+)/status', url)
    return m.group(1) if m else None


# ============================================================
# 图片下载
# ============================================================

def sanitize_filename(name: str, max_length: int = 80) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name or 'untitled'


def download_image(img_url: str, save_path: str, referer: str = None) -> str | None:
    """下载图片，返回实际保存路径"""
    headers = HEADERS.copy()
    if referer:
        headers['Referer'] = referer

    # X 图片 URL 处理：去掉 :large/:small 参数，用 format=jpg&name=large 获取最大尺寸
    # 例: https://pbs.twimg.com/media/xxx?format=jpg&name=large
    clean_url = re.sub(r':(large|small|medium|thumb|orig)$', '', img_url)
    if 'pbs.twimg.com/media/' in clean_url and '?' not in clean_url:
        clean_url += '?format=jpg&name=large'

    try:
        resp = requests.get(clean_url, headers=headers, timeout=30, stream=True)
        if resp.status_code == 200:
            ct = resp.headers.get('Content-Type', '')
            ext_map = {
                'image/jpeg': '.jpg', 'image/png': '.png',
                'image/gif': '.gif', 'image/webp': '.webp',
            }
            ext = next((v for k, v in ext_map.items() if k in ct), '.jpg')
            base, _ = os.path.splitext(save_path)
            actual_path = base + ext
            with open(actual_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_kb = os.path.getsize(actual_path) / 1024
            if size_kb < 1:
                os.remove(actual_path)
                return None
            return actual_path
    except Exception as e:
        print(f"      [失败] 图片下载: {e}")
    return None


# ============================================================
# Playwright 爬取核心
# ============================================================

def fetch_with_playwright(url: str) -> tuple[str, str]:
    """
    用 Playwright 渲染 X 页面，返回 (page_title, rendered_html)。
    如果 Playwright 未安装，抛出 ImportError。
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        raise ImportError(
            "请安装 Playwright:\n"
            "  pip3.11 install playwright\n"
            "  python3.11 -m playwright install chromium"
        )

    print(f"   [Playwright] 正在启动浏览器...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ],
        )
        context = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/125.0.0.0 Safari/537.36'
            ),
            viewport={'width': 1280, 'height': 900},
            locale='zh-CN',
        )
        page = context.new_page()

        # 屏蔽不必要的资源，加快加载
        page.route('**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,eot}',
                   lambda route: route.abort()
                   if 'pbs.twimg.com' not in route.request.url and
                      'abs.twimg.com' not in route.request.url
                   else route.continue_())
        page.route('**/analytics*', lambda r: r.abort())
        page.route('**/tracking*', lambda r: r.abort())

        print(f"   [Playwright] 正在加载页面: {url}")
        try:
            page.goto(url, timeout=PAGE_TIMEOUT, wait_until='domcontentloaded')
        except PWTimeout:
            print("   [警告] 页面加载超时，尝试读取已有内容")

        # 等待推文主体出现
        try:
            page.wait_for_selector(
                'article[data-testid="tweet"]',
                timeout=15000
            )
            print("   [Playwright] 推文内容已加载")
        except PWTimeout:
            print("   [警告] 未找到 article[data-testid=tweet]，尝试继续解析")

        # 处理登录弹窗：X 可能弹出登录提示，尝试关闭
        try:
            close_btn = page.query_selector('[aria-label="关闭"]') or \
                        page.query_selector('[data-testid="app-bar-close"]')
            if close_btn:
                close_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        # 等待更多 Thread 推文加载（向下滚动）
        print("   [Playwright] 正在展开 Thread...")
        for _ in range(5):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(THREAD_SCROLL_WAIT)
            # 检查是否有"显示更多回复"按钮
            try:
                show_more = page.query_selector('[data-testid="tweet"] ~ [role="button"]')
                if show_more:
                    show_more.click()
                    time.sleep(1.5)
            except Exception:
                pass

        title = page.title()
        html = page.content()

        context.close()
        browser.close()

    return title, html


# ============================================================
# X Article 解析（longform 长文格式）
# ============================================================

def is_article_page(html: str) -> bool:
    """判断是否为 X Article（长文）页面"""
    return 'data-testid="twitterArticleRichTextView"' in html or \
           'data-testid="longformRichTextComponent"' in html


def _xml_escape_inline(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _span_to_xml(span_el) -> str:
    """将单个 span 转换为 WPS XML 内联片段，保留 bold"""
    text = span_el.get_text()
    if not text:
        return ''
    text_esc = _xml_escape_inline(text)
    style = span_el.get('style', '')
    if 'bold' in style.lower() or '700' in style:
        return f'<strong>{text_esc}</strong>'
    return text_esc


def _inline_el_to_xml(el) -> str:
    """递归处理内联元素，保留粗体、链接"""
    from bs4 import NavigableString, Tag
    if isinstance(el, NavigableString):
        return _xml_escape_inline(str(el))
    if not isinstance(el, Tag):
        return ''
    if el.name == 'br':
        return '<br/>'
    if el.name == 'a':
        href = el.get('href', '')
        text = el.get_text()
        if href and text:
            return f'<a href="{_xml_escape_inline(href)}">{_xml_escape_inline(text)}</a>'
        return _xml_escape_inline(text)
    if el.name == 'span':
        style = el.get('style', '')
        inner = ''.join(_inline_el_to_xml(c) for c in el.children)
        if 'bold' in style.lower() or '700' in style:
            return f'<strong>{inner}</strong>'
        return inner
    # 其他标签递归
    return ''.join(_inline_el_to_xml(c) for c in el.children)


def _p_el_to_xml(p_el) -> str:
    """将段落 div/p 元素转为 WPS <p> XML，保留内联格式"""
    inner = ''.join(_inline_el_to_xml(c) for c in p_el.children)
    inner = inner.strip()
    if not inner:
        return ''
    return f'<p>{inner}</p>'


def _collect_article_blocks(el) -> list[dict]:
    """
    递归提取 X Article longformRichTextComponent 内所有块。
    返回 [{type: h1/h2/h2/p/code/img, el: BeautifulSoup element}]
    """
    results = []
    for child in el.children:
        if not hasattr(child, 'name') or not child.name:
            continue
        tag = child.name
        testid = child.get('data-testid', '')

        if tag in ('h1', 'h2', 'h3'):
            results.append({'type': tag, 'el': child})
        elif testid == 'tweetPhoto':
            results.append({'type': 'img', 'el': child})
        elif testid == 'markdown-code-block':
            results.append({'type': 'code', 'el': child})
        elif tag == 'section':
            code = child.find(attrs={'data-testid': 'markdown-code-block'})
            photo = child.find(attrs={'data-testid': 'tweetPhoto'})
            if code:
                results.append({'type': 'code', 'el': code})
            elif photo:
                results.append({'type': 'img', 'el': photo})
            else:
                results.extend(_collect_article_blocks(child))
        elif tag == 'div':
            # 含子结构节点 → 继续递归
            has_structural = (
                child.find(['h1', 'h2', 'h3']) or
                child.find(attrs={'data-testid': 'markdown-code-block'}) or
                child.find(attrs={'data-testid': 'tweetPhoto'}) or
                child.find('section')
            )
            if has_structural:
                results.extend(_collect_article_blocks(child))
            else:
                text = child.get_text(strip=True)
                if text:
                    results.append({'type': 'p', 'el': child})
        else:
            results.extend(_collect_article_blocks(child))
    return results


def parse_article_from_html(html: str) -> tuple[str, list[dict], list[str]]:
    """
    解析 X Article 页面。

    Returns:
        (title, blocks, image_urls)
        blocks: [{type: h1/h2/h3/p/code/img, content: str, img_url: str}]
        image_urls: 按顺序排列的图片 URL 列表
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 提取文章标题
    title_el = soup.find(attrs={'data-testid': 'twitter-article-title'})
    title = title_el.get_text(strip=True) if title_el else ''

    # 提取正文容器
    lrtc = soup.find(attrs={'data-testid': 'longformRichTextComponent'})
    if not lrtc:
        lrtc = soup.find(attrs={'data-testid': 'twitterArticleRichTextView'})
    if not lrtc:
        print("   [Article] 未找到 longformRichTextComponent，解析失败")
        return title, [], []

    raw_blocks = _collect_article_blocks(lrtc)
    print(f"   [Article] 提取到 {len(raw_blocks)} 个原始块")

    # 转换为结构化 blocks
    blocks = []
    image_urls = []

    for rb in raw_blocks:
        btype = rb['type']
        el = rb['el']

        if btype in ('h1', 'h2', 'h3'):
            text = el.get_text(strip=True)
            if text:
                blocks.append({'type': btype, 'content': text, 'img_url': ''})

        elif btype == 'p':
            xml = _p_el_to_xml(el)
            if xml:
                blocks.append({'type': 'p', 'content': xml, 'img_url': ''})

        elif btype == 'code':
            pre = el.find('pre')
            code_text = pre.get_text() if pre else el.get_text()
            if code_text.strip():
                blocks.append({'type': 'code', 'content': code_text, 'img_url': ''})

        elif btype == 'img':
            imgs = el.find_all('img')
            for img in imgs:
                src = img.get('src', '')
                if 'pbs.twimg.com/media/' in src:
                    image_urls.append(src)
                    blocks.append({'type': 'img', 'content': '', 'img_url': src})
                    break  # 每个 tweetPhoto 只取一张

    print(f"   [Article] 有效块: {len(blocks)}（含 {len(image_urls)} 张图片）")
    return title, blocks, image_urls


def article_blocks_to_segments(
    blocks: list[dict],
    img_mapping: dict[str, str],
) -> list[tuple]:
    """
    将 Article blocks 转为 write_content_with_placeholders 所需的 segments。
    segments: [(type, content)] — type 为 'xml' 或 'img'
    每个 block 单独成一个 xml segment，避免超大 xml 导致 WPS 乱序。
    """
    segments = []

    for b in blocks:
        btype = b['type']

        if btype == 'h1':
            segments.append(('xml', f'<h2>{_xml_escape_inline(b["content"])}</h2>'))
        elif btype in ('h2', 'h3'):
            segments.append(('xml', f'<h3>{_xml_escape_inline(b["content"])}</h3>'))
        elif btype == 'p':
            segments.append(('xml', b['content']))
        elif btype == 'code':
            escaped = _xml_escape_inline(b['content'])
            segments.append(('xml', f'<codeblock>{escaped}</codeblock>'))
        elif btype == 'img':
            local_path = img_mapping.get(b['img_url'])
            if local_path and os.path.exists(local_path):
                segments.append(('img', local_path))

    return segments


def import_article_to_wps(
    url: str,
    title: str,
    author_name: str,
    author_handle: str,
    blocks: list[dict],
    img_mapping: dict[str, str],
) -> bool:
    """将 X Article 导入 WPS 笔记"""
    mod = _load_wps_writer()
    if not mod:
        print("   [WPS] 找不到 wps_writer.py")
        return False
    if not mod.cli_check():
        print("   [WPS] wpsnote-cli 未连接")
        return False

    note_id = mod.cli_create_note(title)
    if not note_id:
        print("   [WPS] 创建笔记失败")
        return False
    mod.cli_sync(note_id)
    print(f"   [WPS] 创建笔记: {note_id}")

    outline_data = mod.cli_get_outline(note_id)
    first_id = outline_data.get('blocks', [{}])[0].get('id')
    if not first_id:
        print("   [WPS] 无法获取初始 block")
        return False

    author_info = f'{author_name} (@{author_handle})' if author_name else f'@{author_handle}'
    header_xml = f'<h1>{_xml_escape_inline(title)}</h1>'
    meta_xml = (
        f'<p>{_xml_escape_inline(author_info)} | '
        f'<a href="{url}">原文链接</a></p>'
    )

    res = mod.cli_batch_edit(note_id, [
        {'op': 'replace', 'block_id': first_id, 'content': header_xml},
        {'op': 'insert', 'anchor_id': first_id, 'position': 'after', 'content': meta_xml},
    ])
    if res.get('ok') is False:
        print(f"   [WPS] 写标题失败: {res.get('message')}")
        return False

    segments = article_blocks_to_segments(blocks, img_mapping)
    xml_count = sum(1 for t, _ in segments if t == 'xml')
    img_count = sum(1 for t, _ in segments if t == 'img')
    print(f"   [WPS] segments: {xml_count} 段文字, {img_count} 张图片")

    img_list = mod.write_content_with_placeholders(note_id, segments)
    print(f"   [WPS] 文字写入完成，{len(img_list)} 个图片占位符")

    if img_list:
        ok, fail = mod.find_and_insert_images(note_id, img_list)
        print(f"   [WPS] 图片插入: {ok}/{len(img_list)}")

    print(f"   ✅ WPS 导入完成：《{title}》")
    return True


# ============================================================
# HTML 解析：提取推文结构
# ============================================================

class Tweet:
    """单条推文数据结构"""
    def __init__(self):
        self.author_name: str = ''
        self.author_handle: str = ''
        self.text: str = ''
        self.time: str = ''
        self.images: list[str] = []
        self.tweet_id: str = ''

    def __repr__(self):
        return f"Tweet(@{self.author_handle}: {self.text[:40]}...)"


def parse_tweets_from_html(html: str, main_username: str) -> list[Tweet]:
    """
    从渲染后的 HTML 中提取推文列表。
    只保留主作者的推文（过滤掉其他人的回复）。
    """
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('article', {'data-testid': 'tweet'})

    if not articles:
        print(f"   [解析] 未找到 article[data-testid=tweet]，尝试备用选择器")
        articles = soup.find_all('article')

    print(f"   [解析] 发现 {len(articles)} 个推文块")
    tweets = []
    seen_ids = set()

    for article in articles:
        tweet = Tweet()

        # 提取作者信息
        user_name_el = article.find('[data-testid="User-Name"]') or \
                       article.find(attrs={'data-testid': 'User-Name'})
        if user_name_el:
            spans = user_name_el.find_all('span')
            for span in spans:
                t = span.get_text(strip=True)
                if t and not t.startswith('@') and tweet.author_name == '':
                    tweet.author_name = t
                if t.startswith('@') and tweet.author_handle == '':
                    tweet.author_handle = t.lstrip('@')

        # 从链接中提取作者（备用）
        if not tweet.author_handle:
            links = article.find_all('a', href=re.compile(r'^/[^/]+/status/'))
            for link in links:
                m = re.match(r'^/([^/]+)/status/(\d+)', link.get('href', ''))
                if m:
                    tweet.author_handle = m.group(1)
                    tweet.tweet_id = m.group(2)
                    break

        # 过滤：只保留主作者的推文（Thread 中其他人的回复排除）
        if main_username and tweet.author_handle.lower() != main_username.lower():
            continue

        # 提取推文文字
        text_el = article.find(attrs={'data-testid': 'tweetText'})
        if text_el:
            # 保留换行，将 span 中的文字提取出来
            parts = []
            for elem in text_el.children:
                if hasattr(elem, 'get_text'):
                    parts.append(elem.get_text())
                else:
                    parts.append(str(elem))
            tweet.text = ''.join(parts).strip()
        else:
            tweet.text = article.get_text(separator='\n', strip=True)

        # 提取时间
        time_el = article.find('time')
        if time_el:
            tweet.time = time_el.get('datetime', '') or time_el.get_text(strip=True)

        # 提取图片 URL
        for img in article.find_all('img'):
            src = img.get('src', '')
            if 'pbs.twimg.com/media/' in src or 'pbs.twimg.com/ext_tw_video' in src:
                if src not in tweet.images:
                    tweet.images.append(src)

        # 去重（避免同一推文被重复抓）
        dedup_key = tweet.tweet_id or tweet.text[:50]
        if dedup_key in seen_ids:
            continue
        if tweet.text:
            seen_ids.add(dedup_key)
            tweets.append(tweet)

    return tweets[:MAX_THREAD_TWEETS]


# ============================================================
# 下载推文图片
# ============================================================

def download_tweet_images(tweets: list[Tweet], images_dir: str, base_url: str) -> dict[str, str]:
    """下载所有推文中的图片，返回 {原始URL: 本地路径} 映射"""
    os.makedirs(images_dir, exist_ok=True)
    mapping = {}
    counter = 0

    for tweet in tweets:
        for img_url in tweet.images:
            if img_url in mapping:
                continue
            counter += 1
            save_path = os.path.join(images_dir, f'img_{counter:03d}.jpg')
            print(f"      [{counter}] 下载图片: {img_url[:80]}...")
            actual = download_image(img_url, save_path, referer=base_url)
            if actual:
                mapping[img_url] = actual
                print(f"             → 已保存: {os.path.basename(actual)}")
            time.sleep(0.3)

    return mapping


# ============================================================
# 组装内容为 WPS XML / Markdown
# ============================================================

def tweets_to_xml(tweets: list[Tweet], img_mapping: dict[str, str],
                  images_dir: str, original_url: str) -> str:
    """将推文列表组装成 WPS XML 格式"""
    parts = []

    for i, tweet in enumerate(tweets):
        if i > 0:
            parts.append('<hr/>')

        # 推文正文：保留换行
        lines = tweet.text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 简单转义 XML 特殊字符
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            parts.append(f'<p>{line}</p>')

        # 图片
        for img_url in tweet.images:
            local_path = img_mapping.get(img_url)
            if local_path and os.path.exists(local_path):
                parts.append(f'__IMG_PLACEHOLDER__{local_path}__')

    return '\n'.join(parts)


def tweets_to_markdown(tweets: list[Tweet], img_mapping: dict[str, str],
                       original_url: str) -> str:
    """将推文列表组装成 Markdown 格式"""
    parts = []

    for i, tweet in enumerate(tweets):
        if i > 0:
            parts.append('\n---\n')
        if tweet.text:
            parts.append(tweet.text)
        for img_url in tweet.images:
            local_path = img_mapping.get(img_url)
            if local_path and os.path.exists(local_path):
                parts.append(f'\n![图片]({local_path})\n')
        parts.append('')

    return '\n'.join(parts)


# ============================================================
# WPS 导入
# ============================================================

def _load_wps_writer():
    """加载同目录下的 wps_writer 模块"""
    import importlib.util
    this_dir = os.path.dirname(os.path.abspath(__file__))
    wps_script = os.path.join(this_dir, 'wps_writer.py')
    if not os.path.exists(wps_script):
        return None
    spec = importlib.util.spec_from_file_location('wps_writer', wps_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def import_to_wps(url: str, title: str, tweets: list,
                  img_mapping: dict, images_dir: str) -> bool:
    """将推文内容导入 WPS 笔记"""
    mod = _load_wps_writer()
    if not mod:
        print("   [WPS] 找不到 wps_writer.py，请确认脚本在同一目录下")
        return False
    if not mod.cli_check():
        print("   [WPS] wpsnote-cli 未连接")
        return False

    note_id = mod.cli_create_note(title)
    if not note_id:
        print("   [WPS] 创建笔记失败")
        return False
    mod.cli_sync(note_id)
    print(f"   [WPS] 创建笔记: {note_id}")

    # 写标题 + 来源
    outline_data = mod.cli_get_outline(note_id)
    blocks = outline_data.get('blocks', [])
    if not blocks:
        print("   [WPS] 无法获取初始 blocks")
        return False

    first_id = blocks[0]['id']
    first_tweet = tweets[0] if tweets else None
    author_info = ''
    if first_tweet and first_tweet.author_name:
        author_info = f'{first_tweet.author_name} (@{first_tweet.author_handle})'
    elif first_tweet and first_tweet.author_handle:
        author_info = f'@{first_tweet.author_handle}'

    header_xml = f'<h1>{_xml_escape(title)}</h1>'
    meta_xml = (
        f'<p>'
        f'{_xml_escape(author_info)} | '
        f'<a href="{url}">原文链接</a>'
        f'</p>'
    )

    res = mod.cli_batch_edit(note_id, [
        {'op': 'replace', 'block_id': first_id, 'content': header_xml},
        {'op': 'insert', 'anchor_id': first_id, 'position': 'after', 'content': meta_xml},
    ])
    if res.get('ok') is False:
        print(f"   [WPS] 写标题失败: {res.get('message')}")
        return False

    # 将推文组装成 segments（xml 块 + img 占位符）
    segments = _tweets_to_segments(tweets, img_mapping)

    xml_count = sum(1 for t, _ in segments if t == 'xml')
    img_count = sum(1 for t, _ in segments if t == 'img')
    print(f"   [WPS] 解析完成: {xml_count} 段文字, {img_count} 张图片")

    img_list = mod.write_content_with_placeholders(note_id, segments)
    print(f"   [WPS] 文字写入完成，{len(img_list)} 个图片占位符")

    if img_list:
        ok, fail = mod.find_and_insert_images(note_id, img_list)
        print(f"   [WPS] 图片插入: {ok}/{len(img_list)}")

    print(f"   ✅ WPS 导入完成：《{title}》")
    return True


def _xml_escape(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _tweets_to_segments(tweets: list[Tweet], img_mapping: dict[str, str]) -> list[tuple]:
    """将推文列表转为 (type, content) segments，供 write_content_with_placeholders 使用"""
    segments = []

    for i, tweet in enumerate(tweets):
        # 分隔线（非第一条）
        if i > 0:
            segments.append(('xml', '<hr/>'))

        # 正文段落
        if tweet.text:
            lines = tweet.text.split('\n')
            xml_parts = []
            for line in lines:
                line = line.strip()
                if line:
                    xml_parts.append(f'<p>{_xml_escape(line)}</p>')
                else:
                    xml_parts.append('<p> </p>')
            if xml_parts:
                segments.append(('xml', '\n'.join(xml_parts)))

        # 图片
        for img_url in tweet.images:
            local_path = img_mapping.get(img_url)
            if local_path and os.path.exists(local_path):
                segments.append(('img', local_path))

    return segments


# ============================================================
# 主流程
# ============================================================

def scrape_twitter(url: str, output_root: str = None, import_wps: bool = False) -> bool:
    """
    爬取 X/Twitter 推文/Thread 并保存。

    Args:
        url: X/Twitter 推文 URL
        output_root: 输出根目录
        import_wps: 是否导入到 WPS 笔记

    Returns:
        bool: 是否成功
    """
    if not output_root:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_root = os.path.join(script_dir, '..', '..', '..', '爬取内容')

    url = normalize_twitter_url(url.strip())
    username = extract_username(url)

    print(f"\n{'=' * 70}")
    print(f"  X/Twitter 推文爬取工具")
    print(f"{'=' * 70}")
    print(f"  目标: {url}")
    if username:
        print(f"  作者: @{username}")
    print(f"{'=' * 70}\n")

    # 1. 用 Playwright 渲染
    try:
        page_title, html = fetch_with_playwright(url)
    except ImportError as e:
        print(f"\n[错误] {e}")
        return False
    except Exception as e:
        print(f"\n[错误] 页面渲染失败: {e}")
        return False

    # 2. 判断是否为 X Article（长文）
    if is_article_page(html):
        print("   [检测] 识别为 X Article（长文）格式")
        return _handle_article(url, username, html, output_root, import_wps)

    # 3. 普通推文解析
    tweets = parse_tweets_from_html(html, username or '')

    if not tweets:
        print("\n[警告] 未能提取到推文内容")
        print("  可能原因：")
        print("  1. X 要求登录才能查看此推文")
        print("  2. 推文已被删除")
        print("  3. Playwright 版本不兼容，请更新: python3.11 -m playwright install chromium")
        return False

    print(f"   [提取] 共提取 {len(tweets)} 条推文")

    # 4. 确定标题
    title_text = tweets[0].text if tweets else '推文'
    title_text = re.sub(r'\s+', ' ', title_text).strip()
    title = title_text[:50] + ('...' if len(title_text) > 50 else '')
    if not title:
        title = page_title or f'@{username} 推文'

    print(f"   [标题] {title}")

    # 5. 创建输出目录
    today = datetime.datetime.now().strftime('%Y%m%d')
    dir_name = sanitize_filename(f"{today}_{title}", max_length=60)
    output_dir = os.path.join(output_root, dir_name)
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'images')
    print(f"   [输出] 目录: {os.path.abspath(output_dir)}")

    # 6. 下载图片
    total_images = sum(len(t.images) for t in tweets)
    if total_images > 0:
        print(f"\n   [图片] 共发现 {total_images} 张图片，开始下载...")
        img_mapping = download_tweet_images(tweets, images_dir, url)
    else:
        print(f"   [图片] 无图片")
        img_mapping = {}

    # 7. 保存原始 HTML
    html_path = os.path.join(output_dir, 'original.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 8. WPS 模式 or Markdown 模式
    if import_wps:
        print(f"\n   [WPS] 启用高质量导入模式...")
        wps_ok = import_to_wps(
            url=url, title=title, tweets=tweets,
            img_mapping=img_mapping, images_dir=images_dir,
        )
        if wps_ok:
            print(f"\n{'=' * 70}")
            print(f"  导入完成（WPS 模式）!")
            print(f"{'=' * 70}")
            print(f"  标题: {title}")
            print(f"  推文数: {len(tweets)}")
            print(f"{'=' * 70}")
            return True
        print("   [WPS] 导入失败，降级为 Markdown")

    # Markdown 模式
    md_content = tweets_to_markdown(tweets, img_mapping, url)
    header = [
        f"# {title}\n",
        f"> 来源: {url}",
    ]
    if tweets and tweets[0].author_name:
        header.append(f"> 作者: {tweets[0].author_name} (@{tweets[0].author_handle})")
    if tweets and tweets[0].time:
        header.append(f"> 时间: {tweets[0].time}")
    header.append(f"> 爬取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    header.append('')
    header.append('---\n')

    final_md = '\n'.join(header) + md_content
    md_path = os.path.join(output_dir, 'content.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(final_md)

    img_count = len(img_mapping)
    print(f"\n{'=' * 70}")
    print(f"  爬取完成!")
    print(f"{'=' * 70}")
    print(f"  标题: {title}")
    print(f"  推文数: {len(tweets)}")
    print(f"  图片数: {img_count} 张")
    print(f"  保存目录: {os.path.abspath(output_dir)}")
    print(f"{'=' * 70}")

    return True


def _handle_article(url: str, username: str, html: str,
                    output_root: str, import_wps: bool) -> bool:
    """处理 X Article 长文格式"""
    title, blocks, image_urls = parse_article_from_html(html)

    if not blocks:
        print("\n[警告] X Article 未能提取到任何内容")
        return False

    if not title:
        title = f'@{username} Article'

    print(f"   [Article] 标题: {title}")

    # 创建输出目录
    today = datetime.datetime.now().strftime('%Y%m%d')
    dir_name = sanitize_filename(f"{today}_{title}", max_length=60)
    output_dir = os.path.join(output_root, dir_name)
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    print(f"   [输出] 目录: {os.path.abspath(output_dir)}")

    # 保存原始 HTML
    html_path = os.path.join(output_dir, 'original.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 下载图片（去重）
    img_mapping = {}
    if image_urls:
        print(f"\n   [图片] 共发现 {len(image_urls)} 张图片，开始下载...")
        counter = 0
        for img_url in image_urls:
            if img_url in img_mapping:
                continue
            counter += 1
            save_path = os.path.join(images_dir, f'img_{counter:03d}.jpg')
            print(f"      [{counter}] 下载图片: {img_url[:80]}...")
            actual = download_image(img_url, save_path, referer=url)
            if actual:
                img_mapping[img_url] = actual
                size_kb = os.path.getsize(actual) // 1024
                print(f"             → 已保存: {os.path.basename(actual)} ({size_kb}KB)")
            time.sleep(0.3)
    else:
        print("   [图片] 无图片")

    if import_wps:
        print(f"\n   [WPS] 启用高质量导入模式...")
        # 提取作者信息
        soup = BeautifulSoup(html, 'html.parser')
        user_name_el = soup.find(attrs={'data-testid': 'User-Name'})
        author_name, author_handle = '', username or ''
        if user_name_el:
            for span in user_name_el.find_all('span'):
                t = span.get_text(strip=True)
                if t and not t.startswith('@') and not author_name:
                    author_name = t
                if t.startswith('@') and not author_handle:
                    author_handle = t.lstrip('@')

        wps_ok = import_article_to_wps(
            url=url, title=title,
            author_name=author_name, author_handle=author_handle,
            blocks=blocks, img_mapping=img_mapping,
        )
        if wps_ok:
            print(f"\n{'=' * 70}")
            print(f"  导入完成（WPS 模式 · X Article）!")
            print(f"{'=' * 70}")
            print(f"  标题: {title}")
            print(f"  块数: {len(blocks)}（图片 {len(img_mapping)} 张）")
            print(f"{'=' * 70}")
            return True
        print("   [WPS] 导入失败，降级为 Markdown")

    # Markdown 降级
    md_lines = [f"# {title}\n", f"> 来源: {url}\n", "---\n"]
    for b in blocks:
        btype = b['type']
        if btype == 'h1':
            md_lines.append(f"\n## {b['content']}\n")
        elif btype == 'h2':
            md_lines.append(f"\n### {b['content']}\n")
        elif btype == 'p':
            from bs4 import BeautifulSoup as BS
            md_lines.append(BS(b['content'], 'html.parser').get_text() + "\n")
        elif btype == 'code':
            md_lines.append(f"\n```\n{b['content']}\n```\n")
        elif btype == 'img':
            lp = img_mapping.get(b['img_url'], '')
            if lp:
                md_lines.append(f"\n![图片]({lp})\n")
    md_path = os.path.join(output_dir, 'content.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n{'=' * 70}")
    print(f"  爬取完成（X Article · Markdown 模式）!")
    print(f"{'=' * 70}")
    print(f"  标题: {title}")
    print(f"  块数: {len(blocks)}")
    print(f"  保存目录: {os.path.abspath(output_dir)}")
    print(f"{'=' * 70}")
    return True


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='X/Twitter 推文 / Thread 爬取工具',
        epilog='示例: python3.11 twitter_import.py "https://x.com/user/status/xxx" --wps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('url', help='X/Twitter 推文 URL')
    parser.add_argument('-d', '--dir', help='输出根目录路径（可选）', default=None)
    parser.add_argument(
        '--wps', action='store_true',
        help='高质量模式：直接导入 WPS 笔记（需要 wpsnote-cli）',
    )

    args = parser.parse_args()
    url = args.url.strip()

    if not is_twitter_url(url):
        print("[错误] 请提供有效的 X/Twitter URL（x.com 或 twitter.com）")
        sys.exit(1)

    success = scrape_twitter(url, output_root=args.dir, import_wps=args.wps)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
