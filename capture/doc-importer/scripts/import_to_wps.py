#!/usr/bin/env python3
"""
import_to_wps.py - 使用 wpsnote-cli 将转换好的文档批量导入到 WPS 笔记

这是导入流水线的最后一步，使用 wpsnote-cli 直接操作 WPS 笔记，
比通过 MCP 更快（减少来回通信），适合批量导入。

用法：
    python3 import_to_wps.py <文件路径> [选项]
    python3 import_to_wps.py <目录路径> [选项]   # 批量导入整个目录

选项：
    --resume                断点续跑（跳过标题已存在于 WPS 的笔记）
    --on-conflict STR       冲突处理：ask | overwrite | skip | append（默认 ask）
    --dry-run               只打印操作，不实际执行
    --tag STR               为导入的笔记打额外标签（如 "#项目A"）
    --source TYPE           来源类型：obsidian|siyuan|wechat_mp|generic（默认 auto）
    --no-tag                不自动打来源标签
    --days N                只导入最近 N 天内修改的文件
    --formats STR           只导入指定格式，逗号分隔（如 md,pdf）
    --select STR            预先选择文件编号，如 1,3,5-10（跳过交互）

前置要求：
    wpsnote-cli 已安装并配置好 API Key
    （运行 wpsnote-cli status 确认连接正常）

核心稳定性说明：
    1. cli() 使用 bytes 模式读取输出，避免大数据截断（text=True 下 list 等接口会截断）
    2. BATCH_SIZE=4：每次 batch_edit 最大块数，越小越稳定
    3. do_insert 带 4 次重试 + anchor 刷新，防止 anchor 失效导致内容静默丢失
    4. get_all_blocks 翻页获取全部 blocks，解决 outline 默认只返回 100 条的限制
    5. insert_image 前检查已有图片数，避免断点续跑时重复插图
"""

import os
import sys
import json
import re
import base64
import subprocess
import argparse
import datetime
import tempfile
import time
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

# ─── 常量 ──────────────────────────────────────────────────────────────────────

BATCH_SIZE   = 4      # 每次 batch_edit 最大块数（越小越稳定，不要超过 8）
INSERT_RETRIES = 4    # anchor 失效时最大重试次数
IMG_INTERVAL = 0.8    # 图片插入间隔（秒），避免速率限制


# ─── CLI 基础封装 ───────────────────────────────────────────────────────────────

def cli(args: list) -> dict:
    """
    执行 wpsnote-cli 命令，返回 JSON 结果。
    使用 bytes 模式读取输出（避免 text=True 在大数据下截断）。
    """
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
    """带重试的 CLI 调用（遇到 Block not found 直接放弃）"""
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


def cli_find_note_by_title(title: str) -> str | None:
    """按标题搜索笔记，返回 note_id 或 None（用 find 而非 list，避免大数据截断）"""
    r = cli(['find', '--keyword', title[:20], '--limit', '5'])
    notes = (r.get('data') or {}).get('notes', [])
    return next((n['note_id'] for n in notes if n.get('title') == title), None)


def cli_create_note(title: str) -> str | None:
    """创建笔记，返回 note_id"""
    r = cli(['create', '--title', title])
    return (r.get('data') or {}).get('fileId') or (r.get('data') or {}).get('note_id')


def cli_sync(note_id: str):
    """同步笔记（新建后需要等待初始化）"""
    cli(['sync', '--note_id', note_id])
    time.sleep(2.0)


def cli_get_outline(note_id: str) -> dict:
    """获取笔记大纲（第一页，最多 100 个 block）"""
    r = cli(['outline', '--note_id', note_id])
    return r.get('data') or {}


def cli_get_all_blocks(note_id: str) -> list:
    """
    翻页获取笔记全部 blocks，解决 outline 默认只返回 100 条的限制。
    第一页用 outline（有 preview 字段），后续翻页用 read-blocks（有 content 字段）。
    """
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
    """获取笔记最后一个 block 的 ID（用作插入 anchor）"""
    data = cli_get_outline(note_id)
    blocks = data.get('blocks', [])
    return blocks[-1]['id'] if blocks else ''


def cli_batch_edit(note_id: str, ops: list) -> dict:
    return cli_retry(['batch-edit', '--note_id', note_id,
                      '--operations', json.dumps(ops)])


# ─── HTML → WPS XML（从 import_with_images.py 移植）──────────────────────────

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
    (255, 41, 65):   '#C21C13',   # 微信红 → WPS红
    (255, 76, 65):   '#C21C13',
    (0, 128, 255):   '#116AF0',   # 微信蓝 → WPS蓝
    (25, 156, 255):  '#116AF0',
    (36, 91, 219):   '#0E52D4',
    (255, 104, 39):  '#DB7800',   # 橙色
}


def rgb_to_wps_color(rgb_str: str) -> str | None:
    m = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str.strip())
    if not m:
        return None
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    # 跳过正文灰色（色差 < 20 且不是纯黑）
    if max(abs(r-g), abs(g-b), abs(r-b)) < 20 and r > 40:
        return None
    # 跳过微信正文常用的 rgb(100,106,115)
    if abs(r-100)+abs(g-106)+abs(b-115) < 25:
        return None
    # 精确匹配
    if (r, g, b) in WPS_COLORS:
        return WPS_COLORS[(r, g, b)]
    # 最近邻（欧氏距离，阈值 8000 ≈ 色差约 28）
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
            pass  # 图片在块级处理，内联忽略
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
        return ('img', None)  # 图片文件缺失

    segments = []

    def process_element(el):
        if isinstance(el, NavigableString):
            return
        real_imgs = [i for i in el.find_all('img')
                     if (i.get('data-src', '') or i.get('src', '')).startswith('http')]
        if real_imgs:
            # 段落中有真实图片：先写文字，再写图片
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

        # 检测标题：原生 h 标签或大字体 section/p
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
            # 代码块：提取语言标注和纯文本内容
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
        """扁平化迭代：自动展开只含子 section/p 的容器 section"""
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
    """
    将图片 base64 编码后写入临时文件，用 --src_file 插入。
    返回新 block_id 或 None。
    使用固定临时文件路径避免频繁创建/删除文件。
    """
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
                anchor = cli_get_last_block_id(note_id) or anchor
            res = cli_batch_edit(note_id, [
                {'op': 'insert', 'anchor_id': anchor, 'position': 'after', 'content': content}
            ])
            if res.get('ok') is not False:
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
            img_path = seg_val if isinstance(seg_val, Path) else None
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
    插入前检查笔记已有图片数，避免断点续跑时重复插图。
    返回 (inserted_count, failed_count)。
    """
    if not img_segments or all(s['img_path'] is None for s in img_segments):
        return 0, 0

    time.sleep(2)

    ph_pat_outline = re.compile(r'\[图片占位-(\d+):([^\]]+)\]')
    ph_pat_content = re.compile(r'id="([^"]+)"[^>]*>\[图片占位-(\d+):([^\]]+)\]')
    ph_map = {}
    img_count_existing = 0

    # 翻页获取全部 blocks
    all_blocks = cli_get_all_blocks(note_id)
    for blk in all_blocks:
        # outline block 有 preview
        m = ph_pat_outline.search(blk.get('preview', ''))
        if m:
            ph_map[int(m.group(1))] = (blk['id'], m.group(2))
            continue
        # read-blocks block 有 content
        content = blk.get('content', '')
        m = ph_pat_content.search(content)
        if m:
            ph_map[int(m.group(2))] = (m.group(1), m.group(3))
        if '<img ' in content:
            img_count_existing += 1
        if blk.get('type') == 'image':
            img_count_existing += 1

    # 防重复：笔记已有图片时跳过
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


# ─── 导入单篇笔记 ───────────────────────────────────────────────────────────────

def import_one(
    convert_dir: Path,
    on_conflict: str = 'ask',
    extra_tags: list = None,
    source_type: str = 'generic',
    auto_tag: bool = True,
    dry_run: bool = False,
    verbose: bool = True,
    tag_id: str = None,
) -> dict:
    """
    将一个 convert.py 输出目录导入到 WPS 笔记。

    convert_dir 须包含：
      - meta.json：{note_title, publish_time?, source_type?, ...}
      - segments.json 或 content.xml：正文内容
      - images/：图片文件目录（可选）
    """
    meta_path = convert_dir / 'meta.json'
    if not meta_path.exists():
        return {'success': False, 'error': f'缺少 meta.json：{convert_dir}'}

    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    note_title = meta.get('note_title') or meta.get('title') or convert_dir.name
    publish_time = meta.get('publish_time', '')
    source = meta.get('source_type', source_type)
    img_dir = convert_dir / 'images'

    # 加载 segments（优先新格式 segments.json，兼容旧格式 content.xml）
    segments_path = convert_dir / 'segments.json'
    xml_path = convert_dir / 'content.xml'

    if segments_path.exists():
        raw_segs = json.loads(segments_path.read_text(encoding='utf-8'))
        segments = []
        for t, v in raw_segs:
            if t == 'img':
                p = (img_dir / v) if v else None
                segments.append(('img', p))
            else:
                segments.append(('xml', v))
    elif xml_path.exists():
        # 旧格式：转换为 segments 格式（图片以占位符形式）
        xml_content = xml_path.read_text(encoding='utf-8')
        images_path = convert_dir / 'images.json'
        images = json.loads(images_path.read_text(encoding='utf-8')) if images_path.exists() else {}
        segments = []
        last_pos = 0
        for ph in sorted(images, key=lambda x: xml_content.find(x)):
            pos = xml_content.find(ph)
            if pos < 0:
                continue
            if xml_content[last_pos:pos].strip():
                segments.append(('xml', xml_content[last_pos:pos].strip()))
            img_data = images[ph]
            if img_data.startswith('data:'):
                import base64 as b64mod
                _, b64 = img_data.split(',', 1)
                ext = 'jpg' if 'jpeg' in img_data else 'png'
                tmp = img_dir / f'inline_{len(segments)}.{ext}'
                tmp.parent.mkdir(exist_ok=True)
                tmp.write_bytes(b64mod.b64decode(b64))
                segments.append(('img', tmp))
            else:
                segments.append(('img', None))
            last_pos = pos + len(ph)
        if xml_content[last_pos:].strip():
            segments.append(('xml', xml_content[last_pos:].strip()))
    else:
        return {'success': False, 'error': '缺少内容文件（segments.json 或 content.xml）'}

    img_count = sum(1 for t, _ in segments if t == 'img')
    xml_count = sum(1 for t, _ in segments if t == 'xml')
    if verbose:
        print(f'  解析完成: {xml_count} 段文字, {img_count} 张图片')

    # ── 冲突检测 ──────────────────────────────────────────
    existing_id = cli_find_note_by_title(note_title)
    action = 'create'

    if existing_id:
        if on_conflict == 'skip':
            if verbose:
                print(f'  ⏭ 跳过（已存在）：《{note_title}》')
            return {'success': True, 'skipped': True, 'note_title': note_title}
        elif on_conflict == 'ask':
            print(f'\n  ⚠  WPS 中已存在《{note_title}》')
            print('     [O] 覆盖  [S] 跳过  [A] 追加  > ', end='', flush=True)
            choice = input().strip().upper()
            if choice == 'S':
                return {'success': True, 'skipped': True, 'note_title': note_title}
            action = 'append' if choice == 'A' else 'overwrite'
        else:
            action = on_conflict

    if dry_run:
        print(f'  [DRY RUN] {"创建" if not existing_id else action}：《{note_title}》')
        return {'success': True, 'dry_run': True, 'note_title': note_title}

    # ── 创建笔记 ──────────────────────────────────────────
    if action in ('create', 'overwrite') and not existing_id:
        note_id = cli_create_note(note_title)
        if not note_id:
            return {'success': False, 'error': '创建笔记失败'}
        cli_sync(note_id)
        if verbose:
            print(f'  ✓ 创建笔记: {note_id}')
    else:
        note_id = existing_id

    # ── 获取初始 blocks ────────────────────────────────────
    outline_data = cli_get_outline(note_id)
    blocks = outline_data.get('blocks', [])
    if not blocks:
        return {'success': False, 'error': '无法获取初始 blocks'}
    first_id = blocks[0]['id']

    # ── 写入标题 + meta 行 ─────────────────────────────────
    if source == 'wechat_mp' and publish_time:
        tag_xml = (f'<tag id="{tag_id}">{meta.get("tag", "#导入")}</tag>'
                   if tag_id else f'<tag>{meta.get("tag", "#导入")}</tag>')
        meta_line = f'<p>{publish_time} | {tag_xml}</p>'
    else:
        today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        source_label = {'obsidian': 'Obsidian', 'siyuan': '思源笔记',
                        'wechat_mp': '微信公众号', 'generic': '本地文档'}.get(source, source)
        meta_line = (
            f'<blockquote>'
            f'<p>📄 <strong>来源</strong>：{meta.get("rel_path", note_title)}</p>'
            + (f'<p>🕒 <strong>原始时间</strong>：{publish_time}</p>' if publish_time else '')
            + f'<p>🔄 <strong>导入时间</strong>：{today}</p>'
            f'<p>📂 <strong>来源类型</strong>：{source_label}</p>'
            f'</blockquote>'
        )

    res = cli_batch_edit(note_id, [
        {'op': 'replace', 'block_id': first_id, 'content': f'<h1>{note_title}</h1>'},
        {'op': 'insert', 'anchor_id': first_id, 'position': 'after', 'content': meta_line},
    ])
    if res.get('ok') is False:
        return {'success': False, 'error': f'写入标题失败: {res.get("message")}'}

    # ── 写入正文 ───────────────────────────────────────────
    img_list = write_content_with_placeholders(note_id, segments)
    if verbose:
        print(f'  ✓ 文字写入完成，共 {len(img_list)} 个图片占位符')

    # ── 插入图片 ───────────────────────────────────────────
    images_ok = images_fail = 0
    if img_list:
        images_ok, images_fail = find_and_insert_images(note_id, img_list)
        if verbose:
            print(f'  ✓ 图片插入完成: {images_ok}/{len(img_list)}')

    # ── 打标签 ─────────────────────────────────────────────
    if auto_tag and source not in ('wechat_mp',):
        today_str = datetime.date.today().isoformat()
        source_label = {'obsidian': 'Obsidian', 'siyuan': '思源',
                        'generic': '文档'}.get(source, '文档')
        last_id = cli_get_last_block_id(note_id)
        if last_id:
            cli_batch_edit(note_id, [{
                'op': 'insert', 'anchor_id': last_id, 'position': 'after',
                'content': f'<p><tag>#导入//{source_label}//{today_str}</tag></p>',
            }])

    for tag in (extra_tags or []):
        last_id = cli_get_last_block_id(note_id)
        if last_id:
            wps_tag = ('#' + tag.lstrip('#')).replace('/', '//')
            cli_batch_edit(note_id, [{
                'op': 'insert', 'anchor_id': last_id, 'position': 'after',
                'content': f'<p><tag>{wps_tag}</tag></p>',
            }])

    return {
        'success': True,
        'note_id': note_id,
        'note_title': note_title,
        'images_ok': images_ok,
        'images_fail': images_fail,
        'action': action,
    }


# ─── 批量导入入口 ───────────────────────────────────────────────────────────────

def import_batch(
    input_path: Path,
    on_conflict: str = 'ask',
    extra_tags: list = None,
    source_type: str = 'generic',
    auto_tag: bool = True,
    dry_run: bool = False,
    resume: bool = False,
    convert_dir_root: Path = None,
) -> dict:
    """批量导入，input_path 可以是单个 convert 输出目录、多目录父级，或单个文档文件"""

    if input_path.is_dir() and (input_path / 'meta.json').exists():
        dirs_to_import = [input_path]
    elif input_path.is_dir():
        dirs_to_import = [d for d in sorted(input_path.iterdir())
                          if d.is_dir() and (d / 'meta.json').exists()]
    else:
        if not convert_dir_root:
            convert_dir_root = Path(tempfile.mkdtemp(prefix='doc_import_'))
        out_dir = convert_dir_root / input_path.stem
        print(f'📄 转换：{input_path.name} ...')
        r = subprocess.run(
            ['python3', str(Path(__file__).parent / 'convert.py'),
             str(input_path), '--output-dir', str(out_dir), '--source', source_type],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f'  ❌ 转换失败：{r.stderr}')
            return {'total': 0, 'success': 0, 'failed': 1, 'skipped': 0}
        dirs_to_import = [out_dir]

    total = len(dirs_to_import)
    success = skip = fail = 0
    fail_list = []

    for i, d in enumerate(dirs_to_import, 1):
        print(f'\n[{i}/{total}] {d.name}')

        if resume:
            meta = json.loads((d / 'meta.json').read_text(encoding='utf-8'))
            title = meta.get('note_title') or meta.get('title') or d.name
            if cli_find_note_by_title(title):
                print(f'  ⏭ 已存在，跳过')
                skip += 1
                continue

        try:
            r = import_one(
                convert_dir=d, on_conflict=on_conflict, extra_tags=extra_tags,
                source_type=source_type, auto_tag=auto_tag, dry_run=dry_run,
            )
            if r.get('skipped'):
                skip += 1
            elif r.get('success'):
                success += 1
            else:
                fail += 1
                fail_list.append((d.name, r.get('error', '未知')))
                print(f'  ❌ 失败：{r.get("error")}')
        except Exception as e:
            fail += 1
            fail_list.append((d.name, str(e)))
            print(f'  ❌ 异常：{e}')

    print(f'\n━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'✓ 成功：{success}  ⏭ 跳过：{skip}  ✗ 失败：{fail}')
    if fail_list:
        for name, err in fail_list:
            print(f'  - {name}：{err}')

    return {'total': total, 'success': success, 'failed': fail, 'skipped': skip}


# ─── 完整扫描→转换→导入一体化流程 ─────────────────────────────────────────────

def full_pipeline(
    scan_dir: Path,
    on_conflict: str = 'ask',
    extra_tags: list = None,
    source_type: str = 'auto',
    auto_tag: bool = True,
    dry_run: bool = False,
    days: int = None,
    formats: list = None,
    selected_indices: list = None,
    resume: bool = False,
):
    """完整流水线：扫描 → 展示 → 用户选择 → 转换 → 导入"""
    import importlib.util

    scripts_dir = Path(__file__).parent

    def load_mod(name):
        spec = importlib.util.spec_from_file_location(name, scripts_dir / f'{name}.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    scan_mod = load_mod('scan_docs')
    convert_mod = load_mod('convert')

    print(f'\n🔍 扫描目录：{scan_dir}')
    scan_result = scan_mod.scan_directory(
        root_path=scan_dir, days=days,
        source_type=source_type, formats=formats,
    )
    if 'error' in scan_result:
        print(f'❌ 扫描失败：{scan_result["error"]}')
        return

    detected_source = scan_result['source_type']
    files = scan_result['files']
    print(scan_mod.format_file_list_for_display(scan_result))

    if selected_indices is None:
        choice = input('\n请输入选项 > ').strip().upper()
        if choice == 'A':
            selected_files = files
        elif choice.replace(',', '').replace('-', '').isdigit():
            selected_files = []
            for part in choice.split(','):
                part = part.strip()
                if '-' in part:
                    s, e = part.split('-', 1)
                    selected_files += [files[i-1] for i in range(int(s), int(e)+1)
                                       if 1 <= i <= len(files)]
                elif part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(files):
                        selected_files.append(files[idx-1])
        else:
            selected_files = files
    else:
        selected_files = [files[i-1] for i in selected_indices if 1 <= i <= len(files)]

    if not selected_files:
        print('⚠  没有选择任何文件，退出。')
        return

    print(f'\n✅ 已选择 {len(selected_files)} 个文件，开始转换并导入...')

    tmp_root = Path(tempfile.mkdtemp(prefix='doc_import_'))
    success = skip = fail = 0
    fail_list = []

    for i, file_info in enumerate(selected_files, 1):
        file_path = Path(file_info['path'])
        safe_stem = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', file_path.stem)
        out_dir = tmp_root / f"{i:04d}_{safe_stem}"
        print(f'\n[{i}/{len(selected_files)}] {file_info["rel_path"]}')

        if resume:
            title = file_info.get('title') or file_path.stem
            if cli_find_note_by_title(title):
                print(f'  ⏭ 已存在，跳过')
                skip += 1
                continue

        print(f'  ▸ 转换中...', end='', flush=True)
        try:
            cr = convert_mod.convert_file(
                file_path=file_path, output_dir=out_dir,
                source_type=detected_source, root_path=scan_dir,
            )
            if not cr.get('success'):
                raise RuntimeError(cr.get('error', '未知错误'))
            print(f' ✓ (图片:{cr["image_count"]})')
        except Exception as e:
            fail += 1
            fail_list.append((file_info['rel_path'], str(e)))
            print(f' ❌ {e}')
            continue

        print(f'  ▸ 导入中...')
        try:
            r = import_one(
                convert_dir=out_dir,
                on_conflict=on_conflict, extra_tags=extra_tags,
                source_type=detected_source, auto_tag=auto_tag, dry_run=dry_run,
            )
            if r.get('skipped'):
                skip += 1
            elif r.get('success'):
                success += 1
            else:
                fail += 1
                fail_list.append((file_info['rel_path'], r.get('error', '未知')))
        except Exception as e:
            fail += 1
            fail_list.append((file_info['rel_path'], str(e)))
            print(f'  ❌ 导入失败：{e}')

    source_label = {'obsidian': 'Obsidian', 'siyuan': '思源',
                    'wechat_mp': '微信公众号', 'generic': '文档'}.get(detected_source, '文档')
    today = datetime.date.today().isoformat()
    print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'📊 导入完成！  ✓ {success}  ⏭ {skip}  ✗ {fail}')
    if fail_list:
        for name, err in fail_list:
            print(f'  - {name}：{err}')
    if auto_tag and not dry_run:
        print(f'\n  WPS 笔记中搜索标签 #导入//{source_label}//{today} 可查看所有导入笔记。')


# ─── CLI 入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='使用 wpsnote-cli 将文档导入到 WPS 笔记')
    parser.add_argument('input', help='文档文件、convert 输出目录，或要扫描的目录')
    parser.add_argument('--resume', action='store_true', help='跳过标题已存在于 WPS 的笔记')
    parser.add_argument('--on-conflict', default='ask',
                        choices=['ask', 'overwrite', 'skip', 'append'])
    parser.add_argument('--tag', action='append', dest='tags', help='额外标签（可多次传入）')
    parser.add_argument('--no-tag', action='store_true', help='不自动打来源标签')
    parser.add_argument('--source', default='auto',
                        choices=['auto', 'obsidian', 'siyuan', 'wechat_mp', 'generic'])
    parser.add_argument('--days', type=int)
    parser.add_argument('--formats', help='逗号分隔，如 md,pdf')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--select', help='预选文件编号，如 1,3,5-10')
    args = parser.parse_args()

    if not cli_check():
        print('❌ wpsnote-cli 未连接，请运行：wpsnote-cli status')
        sys.exit(1)

    input_path = Path(args.input).resolve()
    formats = [f.strip().lower() for f in args.formats.split(',')] if args.formats else None

    selected = None
    if args.select:
        selected = []
        for part in args.select.split(','):
            part = part.strip()
            if '-' in part:
                s, e = part.split('-', 1)
                selected.extend(range(int(s), int(e) + 1))
            elif part.isdigit():
                selected.append(int(part))

    if input_path.is_dir() and (input_path / 'meta.json').exists():
        r = import_one(
            convert_dir=input_path,
            on_conflict=args.on_conflict,
            extra_tags=args.tags,
            source_type=args.source if args.source != 'auto' else 'generic',
            auto_tag=not args.no_tag,
            dry_run=args.dry_run,
        )
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        full_pipeline(
            scan_dir=input_path,
            on_conflict=args.on_conflict,
            extra_tags=args.tags,
            source_type=args.source,
            auto_tag=not args.no_tag,
            dry_run=args.dry_run,
            days=args.days,
            formats=formats,
            selected_indices=selected,
            resume=args.resume,
        )


if __name__ == '__main__':
    main()
