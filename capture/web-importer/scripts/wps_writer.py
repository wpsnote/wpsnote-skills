#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
wps_writer.py — web-importer 专用 WPS 写入核心

封装 wpsnote-cli 的所有写入操作，供 web_to_md.py 和 twitter_import.py 使用。
此模块独立于 doc-importer，不依赖仓库中其他 skill 的任何文件。

核心稳定性规则（与 doc-importer 保持同步）：
  - BATCH_SIZE=4：每次 batch_edit 最大块数
  - INSERT_RETRIES=4：anchor 失效时最大重试次数
  - 翻页获取全部 blocks，解决 outline 默认只返回 100 条的限制
  - 插图前检查已有图片数，避免断点续跑重复插图
"""

import os
import re
import json
import base64
import subprocess
import time
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString


# ─── 常量 ──────────────────────────────────────────────────────────────────────

BATCH_SIZE     = 4
INSERT_RETRIES = 4
IMG_INTERVAL   = 0.8


# ─── CLI 基础封装 ───────────────────────────────────────────────────────────────

def cli(args: list) -> dict:
    """执行 wpsnote-cli 命令，返回 JSON 结果（bytes 模式读取，避免大数据截断）"""
    cmd = ['wpsnote-cli'] + args + ['--json']
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    raw = result.stdout.decode('utf-8', errors='ignore').strip()
    if not raw:
        return {'ok': False, 'message': result.stderr.decode('utf-8', errors='ignore').strip() or 'empty'}
    try:
        return json.loads(raw)
    except Exception:
        return {'ok': False, 'message': raw[:200]}


def cli_retry(args: list, retries: int = 3, sleep: float = 2.0) -> dict:
    """带重试的 CLI 调用"""
    res = {}
    for i in range(retries):
        res = cli(args)
        if res.get('ok') is not False:
            return res
        msg = res.get('message', '')
        if 'Block not found' in msg or 'not found' in msg.lower():
            break
        if i < retries - 1:
            time.sleep(sleep)
    return res


def cli_check() -> bool:
    """检查 wpsnote-cli 是否可用且已连接"""
    try:
        result = subprocess.run(['wpsnote-cli', 'status'], capture_output=True, timeout=10)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def cli_create_note(title: str) -> str | None:
    """创建笔记，返回 note_id"""
    r = cli(['create', '--title', title])
    return (r.get('data') or {}).get('fileId') or (r.get('data') or {}).get('note_id')


def cli_sync(note_id: str):
    """同步笔记（新建后等待初始化）"""
    cli(['sync', '--note_id', note_id])
    time.sleep(2.0)


def cli_get_outline(note_id: str) -> dict:
    """获取笔记大纲（第一页，最多 100 个 block）"""
    r = cli(['outline', '--note_id', note_id])
    return r.get('data') or {}


def cli_get_all_blocks(note_id: str) -> list:
    """翻页获取笔记全部 blocks"""
    data = cli_get_outline(note_id)
    total = data.get('block_count', 0)
    blocks = list(data.get('blocks', []))
    last_id = blocks[-1]['id'] if blocks else None
    fetched = len(blocks)

    while fetched < total and last_id:
        r2 = cli(['read-blocks', '--note_id', note_id,
                  '--block_id', last_id, '--after', '100',
                  '--include_anchor', 'false'])
        new_blocks = (r2.get('data') or {}).get('blocks', [])
        if not new_blocks:
            break
        blocks.extend(new_blocks)
        last_id = new_blocks[-1]['id']
        fetched += len(new_blocks)

    return blocks


def cli_get_last_block_id(note_id: str) -> str:
    """获取笔记最后一个 block 的 ID"""
    data = cli_get_outline(note_id)
    blocks = data.get('blocks', [])
    return blocks[-1]['id'] if blocks else ''


def cli_batch_edit(note_id: str, ops: list) -> dict:
    return cli_retry(['batch-edit', '--note_id', note_id,
                      '--operations', json.dumps(ops)])


# ─── HTML → WPS XML（内联样式解析）──────────────────────────────────────────────

# WPS 支持的字体颜色预设（含微信常见颜色的映射）
WPS_COLORS = {
    (194, 28, 19):   '#C21C13',
    (219, 120, 0):   '#DB7800',
    (7, 134, 84):    '#078654',
    (14, 82, 212):   '#0E52D4',
    (0, 128, 160):   '#0080A0',
    (117, 117, 117): '#757575',
    (218, 50, 107):  '#DA326B',
    (209, 163, 0):   '#D1A300',
    (88, 164, 1):    '#58A401',
    (17, 106, 240):  '#116AF0',
    (166, 57, 215):  '#A639D7',
    (255, 41, 65):   '#C21C13',
    (255, 76, 65):   '#C21C13',
    (0, 128, 255):   '#116AF0',
    (25, 156, 255):  '#116AF0',
    (36, 91, 219):   '#0E52D4',
    (255, 104, 39):  '#DB7800',
}


def rgb_to_wps_color(rgb_str: str) -> str | None:
    m = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str.strip())
    if not m:
        return None
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if max(abs(r-g), abs(g-b), abs(r-b)) < 20 and r > 40:
        return None
    if abs(r-100)+abs(g-106)+abs(b-115) < 25:
        return None
    if (r, g, b) in WPS_COLORS:
        return WPS_COLORS[(r, g, b)]
    best, best_dist = None, 999999
    for (pr, pg, pb), hx in WPS_COLORS.items():
        d = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if d < best_dist:
            best_dist, best = d, hx
    return best if best_dist < 8000 else None


def parse_span_fmt(style: str) -> dict:
    fmt = {}
    if 'font-weight: 700' in style or 'font-weight:700' in style or 'bold' in style:
        fmt['bold'] = True
    if 'font-style: italic' in style or 'font-style:italic' in style:
        fmt['italic'] = True
    m = re.search(r'(?:^|;)\s*color:\s*(rgb\([^)]+\)|#[\w]+)', style)
    if m:
        c = rgb_to_wps_color(m.group(1))
        if c:
            fmt['color'] = c
    return fmt


def inline_to_xml(el) -> str:
    if isinstance(el, NavigableString):
        return str(el)
    parts = []
    for child in el.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name in ('strong', 'b'):
            inner = inline_to_xml(child).strip()
            parts.append(f'<strong>{inner}</strong>' if inner else '')
        elif child.name in ('em', 'i'):
            inner = inline_to_xml(child).strip()
            parts.append(f'<em>{inner}</em>' if inner else '')
        elif child.name == 'a':
            href = child.get('href', '')
            inner = inline_to_xml(child)
            parts.append(f'<a href="{href}">{inner}</a>' if href and inner.strip() else inner)
        elif child.name == 'br':
            parts.append('<br/>')
        elif child.name == 'img':
            pass
        elif child.name == 'span':
            style = child.get('style', '')
            fmt = parse_span_fmt(style)
            inner = inline_to_xml(child)
            if not inner.strip():
                parts.append(inner)
                continue
            if fmt.get('color'):
                inner = f'<span fontColor="{fmt["color"]}">{inner}</span>'
            if fmt.get('bold'):
                inner = f'<strong>{inner}</strong>'
            if fmt.get('italic'):
                inner = f'<em>{inner}</em>'
            parts.append(inner)
        elif child.name in ('font', 'label'):
            parts.append(inline_to_xml(child))
        else:
            parts.append(inline_to_xml(child))
    return ''.join(parts)


def html_to_segments(html_path: Path, img_dir: Path) -> list:
    """
    解析 HTML 文件，返回 segments 列表。
    segments 格式：[('xml', xml_str), ('img', Path | None), ...]
    支持微信公众号 HTML（js_content 容器、data-src 图片、内联样式）。
    """
    html = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find(id='js_content')
    if not content:
        return []

    img_counter = [0]

    def get_next_img():
        img_counter[0] += 1
        idx = img_counter[0]
        for ext in ['jpg', 'png', 'jpeg', 'gif', 'webp']:
            p = img_dir / f'image_{idx:03d}.{ext}'
            if p.exists():
                return ('img', p)
        return ('img', None)

    segments = []

    def process_element(el):
        if isinstance(el, NavigableString):
            return
        real_imgs = [i for i in el.find_all('img')
                     if (i.get('data-src', '') or i.get('src', '')).startswith('http')]
        if real_imgs:
            el_copy = BeautifulSoup(str(el), 'html.parser').find()
            for img in el_copy.find_all('img'):
                img.decompose()
            text = el_copy.get_text(strip=True)
            if text:
                segments.append(('xml', f'<p>{text}</p>'))
            for _ in real_imgs:
                segments.append(get_next_img())
            return

        tag = el.name
        if not tag:
            return
        clean = el.get_text(strip=True)
        if not clean:
            return
        inline = inline_to_xml(el).strip()

        all_styles = ' '.join(s.get('style', '') for s in el.find_all('span'))
        big_font = re.search(r'font-size:\s*(\d+)px', all_styles)
        is_heading = big_font and int(big_font.group(1)) >= 18

        if tag in ('h1', 'h2') or (is_heading and len(clean) < 60):
            segments.append(('xml', f'<h2>{inline}</h2>'))
        elif tag in ('h3', 'h4'):
            segments.append(('xml', f'<h3>{inline}</h3>'))
        elif tag in ('h5', 'h6'):
            segments.append(('xml', f'<h4>{inline}</h4>'))
        elif tag == 'pre':
            code_el = el.find('code')
            lang = ''
            if code_el:
                cls = ' '.join(code_el.get('class', []))
                m = re.search(r'language-(\w+)', cls)
                if m:
                    lang = m.group(1)
                code_text = code_el.get_text()
            else:
                code_text = el.get_text()
            if code_text.strip():
                lang_attr = f' lang="{lang}"' if lang else ''
                escaped = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                segments.append(('xml', f'<codeblock{lang_attr}>{escaped}</codeblock>'))
            return
        elif tag == 'blockquote':
            inner_xml = inline_to_xml(el).strip()
            inner = (f'<p>{inner_xml}</p>' if '\n' not in inner_xml
                     else ''.join(f'<p>{l}</p>' for l in inner_xml.split('\n') if l.strip()))
            segments.append(('xml',
                f'<highlightBlock emoji="📌" '
                f'highlightBlockBackgroundColor="#E6EEFA" '
                f'highlightBlockBorderColor="#98C1FF">{inner}</highlightBlock>'))
        elif tag in ('ul', 'ol'):
            lt = 'bullet' if tag == 'ul' else 'ordered'
            for li in el.find_all('li', recursive=False):
                li_xml = inline_to_xml(li).strip()
                if li_xml:
                    segments.append(('xml', f'<p listType="{lt}" listLevel="0">{li_xml}</p>'))
        elif tag in ('p', 'section', 'div'):
            if inline:
                segments.append(('xml', f'<p>{inline}</p>'))

    def iter_top_elements(root):
        for el in root.children:
            if isinstance(el, NavigableString):
                continue
            if el.name == 'section':
                direct_children = [c for c in el.children if hasattr(c, 'name') and c.name]
                real_imgs = [i for i in el.find_all('img', recursive=False)
                             if (i.get('data-src', '') or i.get('src', '')).startswith('http')]
                if not real_imgs and len(direct_children) > 3:
                    yield from iter_top_elements(el)
                else:
                    yield el
            else:
                yield el

    for el in iter_top_elements(content):
        if el.name == 'section':
            bq = el.find('blockquote', recursive=False)
            if bq:
                process_element(bq)
                continue
            for list_tag in ('ul', 'ol'):
                lst = el.find(list_tag, recursive=False)
                if lst:
                    process_element(lst)
                    break
            else:
                process_element(el)
        else:
            process_element(el)

    return segments


# ─── 图片插入 ───────────────────────────────────────────────────────────────────

def insert_image_b64(note_id: str, anchor_id: str, img_path: Path,
                     position: str = 'after') -> str | None:
    """将图片 base64 编码后写入临时文件，用 --src_file 插入，返回新 block_id 或 None"""
    ext = img_path.suffix.lstrip('.').lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'gif': 'image/gif',
            'webp': 'image/webp'}.get(ext, 'image/jpeg')
    b64 = base64.b64encode(img_path.read_bytes()).decode()
    tmp = Path('/tmp/wps_img.txt')
    tmp.write_text(f'data:{mime};base64,{b64}')

    res = cli_retry(['insert-image',
                     '--note_id', note_id,
                     '--anchor_id', anchor_id,
                     '--position', position,
                     '--src_file', str(tmp)])
    tmp.unlink(missing_ok=True)

    if res.get('ok') is False:
        print(f'    ✗ 插图失败: {res.get("message", "")[:80]}')
        return None
    return (res.get('data') or {}).get('block_id')


# ─── 稳定写入核心 ───────────────────────────────────────────────────────────────

def write_content_with_placeholders(note_id: str, segments: list) -> list:
    """
    批量写入内容，图片位置先插占位符。
    返回 [{'idx': N, 'img_path': Path | None}, ...] 的图片列表。
    """
    anchor = cli_get_last_block_id(note_id)
    xml_batch = []
    img_segments = []
    img_n = 0
    write_errors = 0

    def do_insert(content: str) -> bool:
        nonlocal anchor, write_errors
        for attempt in range(INSERT_RETRIES):
            if attempt > 0:
                time.sleep(1.5 * attempt)
                # 重试时重新查询最新 anchor，避免用失效 id
                anchor = cli_get_last_block_id(note_id) or anchor
            res = cli_batch_edit(note_id, [
                {'op': 'insert', 'anchor_id': anchor, 'position': 'after', 'content': content}
            ])
            if res.get('ok') is not False:
                # 优先用返回的 last_block_id，避免竞态条件导致乱序
                new_anchor = (res.get('data') or {}).get('last_block_id')
                if new_anchor:
                    anchor = new_anchor
                else:
                    anchor = cli_get_last_block_id(note_id) or anchor
                return True
        print(f'    ✗ insert 最终失败（{write_errors+1}次）: {res.get("message", "")[:60]}')
        write_errors += 1
        return False

    def flush_batch():
        if xml_batch:
            combined = ''.join(xml_batch)
            xml_batch.clear()
            do_insert(combined)

    for seg_type, seg_val in segments:
        if seg_type == 'xml':
            xml_batch.append(seg_val)
            if len(xml_batch) >= BATCH_SIZE:
                flush_batch()
        else:
            flush_batch()
            img_n += 1
            img_path = seg_val if isinstance(seg_val, Path) else (
                Path(seg_val) if seg_val and os.path.exists(str(seg_val)) else None
            )
            if img_path and img_path.exists():
                placeholder = f'<p>[图片占位-{img_n:03d}:{img_path.name}]</p>'
            else:
                placeholder = f'<p>[图片占位-{img_n:03d}:缺失]</p>'
                img_path = None
            do_insert(placeholder)
            img_segments.append({'idx': img_n, 'img_path': img_path})

    flush_batch()
    return img_segments


def find_and_insert_images(note_id: str, img_segments: list) -> tuple[int, int]:
    """
    翻页查找所有占位符 block_id，逐个插入图片并删除占位符。
    返回 (inserted_count, failed_count)。
    """
    if not img_segments or all(s['img_path'] is None for s in img_segments):
        return 0, 0

    time.sleep(2)

    ph_pat_outline = re.compile(r'\[图片占位-(\d+):([^\]]+)\]')
    ph_pat_content = re.compile(r'id="([^"]+)"[^>]*>\[图片占位-(\d+):([^\]]+)\]')
    ph_map = {}
    img_count_existing = 0

    all_blocks = cli_get_all_blocks(note_id)
    for blk in all_blocks:
        m = ph_pat_outline.search(blk.get('preview', ''))
        if m:
            ph_map[int(m.group(1))] = (blk['id'], m.group(2))
            continue
        content = blk.get('content', '')
        m = ph_pat_content.search(content)
        if m:
            ph_map[int(m.group(2))] = (m.group(1), m.group(3))
        if '<img ' in content:
            img_count_existing += 1
        if blk.get('type') == 'image':
            img_count_existing += 1

    if img_count_existing > 0:
        print(f'  ⚠ 笔记已有 {img_count_existing} 张图片，跳过插图（避免重复）')
        return img_count_existing, 0

    inserted = failed = 0
    for seg in img_segments:
        idx = seg['idx']
        img_path = seg['img_path']
        if img_path is None:
            continue
        if idx not in ph_map:
            print(f'    ⚠ 占位符 [{idx:03d}] 未找到，跳过')
            failed += 1
            continue

        ph_block_id, img_name = ph_map[idx]
        print(f'    插入图片 [{idx:03d}]: {img_path.name} ({img_path.stat().st_size // 1024}KB)')

        new_block_id = insert_image_b64(note_id, ph_block_id, img_path, position='after')
        if new_block_id:
            cli_batch_edit(note_id, [{'op': 'delete', 'block_ids': [ph_block_id]}])
            inserted += 1
        else:
            failed += 1

        time.sleep(IMG_INTERVAL)

    return inserted, failed
