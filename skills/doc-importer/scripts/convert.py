#!/usr/bin/env python3
"""
convert.py - 将各种文档格式转换为 WPS 笔记 XML

用法：
    python3 convert.py <文件路径> [选项]

选项：
    --output-dir DIR    输出目录（默认：/tmp/doc_import_<timestamp>）
    --source TYPE       来源类型：obsidian | siyuan | generic（默认 generic）
    --vault-root DIR    Obsidian Vault 根目录（用于解析图片相对路径）
    --workspace-root DIR 思源笔记工作空间根目录（用于解析 assets 图片）
    --ocr               对扫描版 PDF 启用 OCR（需要 pytesseract）

输出（--output-dir 下）：
    content.xml     - WPS 笔记 XML 内容（可直接写入 WPS 笔记）
    images.json     - 图片列表 {placeholder: base64_data_uri}
    meta.json       - 文档元数据
"""

import os
import sys
import json
import base64
import argparse
import datetime
import re
import subprocess
import tempfile
import shutil
import zipfile
import html
from pathlib import Path


# ─── 颜色常量 ────────────────────────────────────────────────────────────────

# WPS 笔记 highlightBlock 颜色映射（Obsidian Callout → WPS）
CALLOUT_STYLES = {
    'note':    ('💡', '#FAF1E6', '#FEC794'),
    'info':    ('ℹ️', '#E6EEFA', '#98C1FF'),
    'tip':     ('✅', '#E6FAEB', '#AFE3BB'),
    'warning': ('⚠️', '#FAE6E6', '#F2A7A7'),
    'danger':  ('🚨', '#FAE6E6', '#F2A7A7'),
    'success': ('✅', '#E6FAEB', '#AFE3BB'),
    'question': ('❓', '#E6EEFA', '#98C1FF'),
    'example': ('📝', '#F5EBFA', '#E5B5FD'),
    'quote':   ('💬', '#EBEBEB', '#C5C5C5'),
    'abstract': ('📋', '#EBEBEB', '#C5C5C5'),
}


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def read_image_as_base64(image_path: Path) -> str:
    """读取图片文件，返回 base64 data URI"""
    if not image_path.exists():
        return ''
    suffix = image_path.suffix.lower()
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.bmp': 'image/bmp',
    }
    mime = mime_map.get(suffix, 'image/png')
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode('ascii')
    return f"data:{mime};base64,{b64}"


def escape_xml(text: str) -> str:
    """转义 XML 特殊字符"""
    return html.escape(str(text), quote=False)


def human_size(size_bytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def make_placeholder(index: int) -> str:
    return f"__IMAGE_PLACEHOLDER_{index}__"


# ─── Markdown → WPS XML ───────────────────────────────────────────────────────

def markdown_to_wps_xml(
    content: str,
    source_type: str = 'generic',
    base_dir: Path = None,
    vault_root: Path = None,
) -> tuple:
    """
    将 Markdown 内容转换为 WPS XML 字符串

    Returns:
        (xml_content: str, images: dict[placeholder -> abs_path_or_url])
    """
    images = {}  # placeholder -> 图片绝对路径或 URL
    img_counter = [0]

    def register_image(src: str) -> str:
        """注册图片，返回占位符"""
        img_counter[0] += 1
        placeholder = make_placeholder(img_counter[0])
        images[placeholder] = src
        return placeholder

    def resolve_image_path(src: str) -> str:
        """解析图片路径，返回绝对路径或 URL"""
        if src.startswith(('http://', 'https://', 'data:')):
            return src
        # 本地路径
        if base_dir:
            candidate = (base_dir / src).resolve()
            if candidate.exists():
                return str(candidate)
        # Obsidian：在 Vault 中搜索
        if vault_root:
            fname = Path(src).name
            # 搜索 attachments/ 和 Vault 根目录
            for search_dir in [vault_root / 'attachments', vault_root]:
                candidate = search_dir / fname
                if candidate.exists():
                    return str(candidate)
            # 全 Vault 搜索（较慢）
            for found in vault_root.rglob(fname):
                return str(found)
        return src

    lines = content.split('\n')
    xml_parts = []
    i = 0

    # 提取 Frontmatter
    frontmatter = {}
    if lines and lines[0].strip() == '---':
        end = next((j for j, l in enumerate(lines[1:], 1) if l.strip() == '---'), None)
        if end:
            for line in lines[1:end]:
                if ':' in line:
                    k, _, v = line.partition(':')
                    frontmatter[k.strip()] = v.strip()
            lines = lines[end + 1:]
            i = 0

    # 处理 Obsidian Callout
    def parse_callout_block(callout_lines: list) -> str:
        header = callout_lines[0].strip().lstrip('>')
        m = re.match(r'\[!(\w+)\]\s*(.*)', header, re.I)
        if not m:
            return None
        ctype = m.group(1).lower()
        title = m.group(2).strip()
        style = CALLOUT_STYLES.get(ctype, ('💡', '#FAF1E6', '#FEC794'))
        emoji, bg, border = style

        body_lines = []
        for l in callout_lines[1:]:
            body_lines.append(l.lstrip('>').strip())

        inner = f'<p><strong>{escape_xml(title)}</strong></p>' if title else ''
        for bl in body_lines:
            if bl:
                inner += f'<p>{convert_inline(bl)}</p>'

        return (
            f'<highlightBlock emoji="{emoji}" '
            f'highlightBlockBackgroundColor="{bg}" '
            f'highlightBlockBorderColor="{border}">'
            f'{inner}</highlightBlock>'
        )

    def convert_inline(text: str) -> str:
        """处理行内 Markdown 语法"""
        # 代码（行内）
        text = re.sub(r'`([^`]+)`', lambda m: f'<code>{escape_xml(m.group(1))}</code>', text)
        # 粗体 + 斜体
        text = re.sub(r'\*\*\*(.+?)\*\*\*', lambda m: f'<strong><em>{escape_xml(m.group(1))}</em></strong>', text)
        # 粗体
        text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', lambda m: f'<strong>{escape_xml(m.group(1) or m.group(2))}</strong>', text)
        # 斜体
        text = re.sub(r'\*(.+?)\*|_(.+?)_', lambda m: f'<em>{escape_xml(m.group(1) or m.group(2))}</em>', text)
        # 删除线
        text = re.sub(r'~~(.+?)~~', lambda m: f'<s>{escape_xml(m.group(1))}</s>', text)
        # 链接
        text = re.sub(r'\[(.+?)\]\((.+?)\)', lambda m: f'<a href="{escape_xml(m.group(2))}">{escape_xml(m.group(1))}</a>', text)
        # Obsidian Wiki 链接
        text = re.sub(r'\[\[(.+?)\|(.+?)\]\]', lambda m: escape_xml(m.group(2)), text)
        text = re.sub(r'\[\[(.+?)\]\]', lambda m: escape_xml(m.group(1)), text)
        # Obsidian 图片嵌入
        def handle_obs_img(m):
            src = resolve_image_path(m.group(1))
            ph = register_image(src)
            return f'<p>{ph}</p>'
        text = re.sub(r'!\[\[(.+?)\]\]', handle_obs_img, text)
        # 普通图片
        def handle_img(m):
            src = resolve_image_path(m.group(2))
            ph = register_image(src)
            return f'<p>{ph}</p>'
        text = re.sub(r'!\[.*?\]\((.+?)\)', handle_img, text)
        # Obsidian 标签 #tag（保留纯文本；文件级标签在导入阶段通过 add-note-tags 写入）
        def handle_tag(m):
            return f'#{escape_xml(m.group(1))}'
        text = re.sub(r'(?<!\w)#([\w/\u4e00-\u9fa5]+)', handle_tag, text)
        return text

    # 有序列表 ID 计数器
    ordered_list_ids = {}

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # 跳过空行（转换为空段落分隔）
        if not stripped:
            xml_parts.append('<p></p>')
            i += 1
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.+)', stripped)
        if m:
            level = len(m.group(1))
            text = convert_inline(m.group(2))
            xml_parts.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue

        # 水平线
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
            xml_parts.append('<hr/>')
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].rstrip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = escape_xml('\n'.join(code_lines))
            xml_parts.append(f'<codeblock lang="{escape_xml(lang)}">{code}</codeblock>')
            i += 1
            continue

        # Obsidian Callout 块引用
        if stripped.startswith('>') and re.match(r'>\s*\[!', stripped):
            callout_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                callout_lines.append(lines[i])
                i += 1
            result = parse_callout_block(callout_lines)
            if result:
                xml_parts.append(result)
                continue

        # 普通引用
        if stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                quote_lines.append(lines[i].lstrip('>').strip())
                i += 1
            inner = ''.join(f'<p>{convert_inline(l)}</p>' for l in quote_lines if l)
            xml_parts.append(f'<blockquote>{inner}</blockquote>')
            continue

        # 表格
        if '|' in stripped and i + 1 < len(lines) and re.match(r'^\|[\s\-|:]+\|$', lines[i + 1].strip()):
            table_lines = [stripped]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i].strip())
                i += 1
            # 解析表格
            xml = '<table>'
            for ti, tl in enumerate(table_lines):
                if re.match(r'^\|[\s\-|:]+\|$', tl):
                    continue  # 跳过分隔行
                cells = [c.strip() for c in tl.strip('|').split('|')]
                xml += '<tr>'
                for cell in cells:
                    content = f'<strong>{convert_inline(cell)}</strong>' if ti == 0 else convert_inline(cell)
                    xml += f'<td><p>{content}</p></td>'
                xml += '</tr>'
            xml += '</table>'
            xml_parts.append(xml)
            continue

        # 无序列表
        m = re.match(r'^(\s*)([-*+])\s+(.*)', stripped if not line[0] == ' ' else line)
        if not m:
            m = re.match(r'^(\s*)([-*+])\s+(.*)', line)
        if m:
            indent = len(m.group(1))
            level = indent // 2
            text = m.group(3)
            # 检测 Todo
            todo_m = re.match(r'\[([ x])\]\s+(.*)', text)
            if todo_m:
                checked = '1' if todo_m.group(1) == 'x' else '0'
                text = convert_inline(todo_m.group(2))
                xml_parts.append(f'<p listType="todo" listLevel="{level}" checked="{checked}">{text}</p>')
            else:
                xml_parts.append(f'<p listType="bullet" listLevel="{level}">{convert_inline(text)}</p>')
            i += 1
            continue

        # 有序列表
        m = re.match(r'^(\s*)(\d+)\.\s+(.*)', line)
        if m:
            indent = len(m.group(1))
            level = indent // 2
            text = convert_inline(m.group(3))
            list_id = f'ol_{level}'
            if list_id not in ordered_list_ids:
                ordered_list_ids[list_id] = f'list{len(ordered_list_ids) + 1}'
            xml_parts.append(
                f'<p listType="ordered" listLevel="{level}" '
                f'listId="{ordered_list_ids[list_id]}">{text}</p>'
            )
            i += 1
            continue

        # 普通段落
        xml_parts.append(f'<p>{convert_inline(stripped)}</p>')
        i += 1

    return '\n'.join(xml_parts), images, frontmatter


# ─── PDF → WPS XML ────────────────────────────────────────────────────────────

def pdf_to_wps_xml(file_path: Path, use_ocr: bool = False) -> tuple:
    """PDF 转换为 WPS XML"""
    images = {}
    img_counter = [0]

    try:
        import pdfplumber
    except ImportError:
        return '<p>❌ 请先安装 pdfplumber：pip3 install pdfplumber</p>', {}, {}

    xml_parts = []

    with pdfplumber.open(str(file_path)) as pdf:
        # 检测是否为扫描版
        first_text = pdf.pages[0].extract_text() if pdf.pages else ''
        is_scanned = not first_text or len(first_text.strip()) < 50

        if is_scanned and not use_ocr:
            xml_parts.append(
                '<highlightBlock emoji="⚠️" highlightBlockBackgroundColor="#FAE6E6" '
                'highlightBlockBorderColor="#F2A7A7">'
                '<p>此 PDF 为扫描版，文字提取可能不完整。如需完整内容，请使用 --ocr 参数启用 OCR。</p>'
                '</highlightBlock>'
            )

        for page_num, page in enumerate(pdf.pages, 1):
            xml_parts.append(f'<h3>第 {page_num} 页</h3>')

            if is_scanned and use_ocr:
                # OCR 处理
                try:
                    from pdf2image import convert_from_path
                    import pytesseract
                    imgs = convert_from_path(str(file_path), first_page=page_num, last_page=page_num)
                    if imgs:
                        text = pytesseract.image_to_string(imgs[0], lang='chi_sim+eng')
                        for line in text.strip().split('\n'):
                            if line.strip():
                                xml_parts.append(f'<p>{escape_xml(line)}</p>')
                except ImportError:
                    xml_parts.append('<p>❌ OCR 需要安装：pip3 install pytesseract pdf2image</p>')
            else:
                # 提取文字
                text = page.extract_text(x_tolerance=3, y_tolerance=3) or ''
                for line in text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    xml_parts.append(f'<p>{escape_xml(line)}</p>')

            # 提取表格
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                xml = '<table>'
                for row in table:
                    xml += '<tr>'
                    for cell in row:
                        xml += f'<td><p>{escape_xml(cell or "")}</p></td>'
                    xml += '</tr>'
                xml += '</table>'
                xml_parts.append(xml)

    # 提取 PDF 图片
    tmp_img_dir = Path(tempfile.mkdtemp(prefix='pdf_imgs_'))
    try:
        result = subprocess.run(
            ['pdfimages', '-j', str(file_path), str(tmp_img_dir / 'img')],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            for img_file in sorted(tmp_img_dir.glob('img-*')):
                img_counter[0] += 1
                placeholder = make_placeholder(img_counter[0])
                b64 = read_image_as_base64(img_file)
                if b64:
                    images[placeholder] = b64
                    # 在 XML 末尾追加图片（PDF 图片无位置信息）
                    xml_parts.append(f'<p>{placeholder}</p>')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    finally:
        shutil.rmtree(tmp_img_dir, ignore_errors=True)

    return '\n'.join(xml_parts), images, {}


# ─── DOCX → WPS XML ──────────────────────────────────────────────────────────

def docx_to_wps_xml(file_path: Path) -> tuple:
    """DOCX 转换为 WPS XML（优先 pandoc，失败则解包）"""
    tmp_dir = Path(tempfile.mkdtemp(prefix='docx_'))

    try:
        # 先尝试 pandoc
        md_output = tmp_dir / 'content.md'
        media_dir = tmp_dir / 'media'

        result = subprocess.run(
            [
                'pandoc',
                '--track-changes=accept',
                f'--extract-media={media_dir}',
                str(file_path),
                '-o', str(md_output)
            ],
            capture_output=True, timeout=120
        )

        if result.returncode == 0 and md_output.exists():
            content = md_output.read_text(encoding='utf-8', errors='ignore')
            xml, images, frontmatter = markdown_to_wps_xml(
                content,
                base_dir=tmp_dir,
                vault_root=None,
            )
            # 解析图片路径（pandoc 提取的媒体文件）
            resolved_images = {}
            for ph, src in images.items():
                if not src.startswith(('http', 'data:')):
                    img_path = Path(src)
                    if not img_path.is_absolute():
                        img_path = tmp_dir / src
                    if img_path.exists():
                        resolved_images[ph] = read_image_as_base64(img_path)
                    else:
                        resolved_images[ph] = src
                else:
                    resolved_images[ph] = src
            return xml, resolved_images, frontmatter

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback：直接解包 ZIP
    try:
        with zipfile.ZipFile(str(file_path), 'r') as z:
            z.extractall(str(tmp_dir))

        media_dir = tmp_dir / 'word' / 'media'
        images = {}
        img_counter = [0]

        if media_dir.exists():
            for img_file in sorted(media_dir.iterdir()):
                img_counter[0] += 1
                placeholder = make_placeholder(img_counter[0])
                b64 = read_image_as_base64(img_file)
                if b64:
                    images[placeholder] = b64

        # 简单文本提取（不解析 XML）
        xml_parts = ['<p>❌ pandoc 未安装，以下为 DOCX 基础文本提取（格式可能丢失）</p>']
        doc_xml_path = tmp_dir / 'word' / 'document.xml'
        if doc_xml_path.exists():
            try:
                import defusedxml.ElementTree as ET
                tree = ET.parse(str(doc_xml_path))
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                for para in tree.findall('.//w:p', ns):
                    texts = [t.text or '' for t in para.findall('.//w:t', ns)]
                    text = ''.join(texts).strip()
                    if text:
                        xml_parts.append(f'<p>{escape_xml(text)}</p>')
            except Exception:
                xml_parts.append('<p>XML 解析失败，请安装 pandoc 后重试。</p>')

        for ph in images:
            xml_parts.append(f'<p>{ph}</p>')

        return '\n'.join(xml_parts), images, {}

    except Exception as e:
        return f'<p>❌ DOCX 转换失败：{escape_xml(str(e))}</p>', {}, {}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─── PPTX → WPS XML ──────────────────────────────────────────────────────────

def pptx_to_wps_xml(file_path: Path) -> tuple:
    """PPTX 转换为 WPS XML"""
    tmp_dir = Path(tempfile.mkdtemp(prefix='pptx_'))
    images = {}
    img_counter = [0]
    xml_parts = []

    try:
        # 提取图片
        with zipfile.ZipFile(str(file_path), 'r') as z:
            for name in z.namelist():
                if name.startswith('ppt/media/'):
                    z.extract(name, str(tmp_dir))
            z.extractall(str(tmp_dir))

        media_dir = tmp_dir / 'ppt' / 'media'

        # 提取文本（markitdown）
        try:
            result = subprocess.run(
                ['python3', '-m', 'markitdown', str(file_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and result.stdout:
                md_content = result.stdout
                # markitdown 输出按幻灯片分段，包含 ## Slide N 标题
                xml, slide_images, _ = markdown_to_wps_xml(
                    md_content,
                    base_dir=tmp_dir,
                )
                xml_parts.append(xml)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback：直接解析 PPTX XML
            slides_dir = tmp_dir / 'ppt' / 'slides'
            if slides_dir.exists():
                import glob
                slide_files = sorted(glob.glob(str(slides_dir / 'slide*.xml')))
                for si, slide_file in enumerate(slide_files, 1):
                    try:
                        import defusedxml.ElementTree as ET
                        tree = ET.parse(slide_file)
                        ns = {
                            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                        }
                        texts = [t.text or '' for t in tree.findall('.//a:t', ns) if t.text]
                        if texts:
                            xml_parts.append(f'<h2>幻灯片 {si}</h2>')
                            for t in texts:
                                xml_parts.append(f'<p>{escape_xml(t)}</p>')
                    except Exception:
                        pass

        # 注册提取的图片
        if media_dir.exists():
            for img_file in sorted(media_dir.iterdir()):
                img_counter[0] += 1
                placeholder = make_placeholder(img_counter[0])
                b64 = read_image_as_base64(img_file)
                if b64:
                    images[placeholder] = b64
                    xml_parts.append(f'<p>{placeholder}</p>')

    except Exception as e:
        xml_parts.append(f'<p>❌ PPTX 转换失败：{escape_xml(str(e))}</p>')
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return '\n'.join(xml_parts), images, {}


# ─── XLSX → WPS XML ──────────────────────────────────────────────────────────

def xlsx_to_wps_xml(file_path: Path) -> tuple:
    """XLSX 转换为 WPS XML"""
    try:
        import pandas as pd
    except ImportError:
        return '<p>❌ 请先安装 pandas：pip3 install pandas openpyxl</p>', {}, {}

    xml_parts = []

    try:
        all_sheets = pd.read_excel(str(file_path), sheet_name=None, dtype=str)

        for sheet_name, df in all_sheets.items():
            xml_parts.append(f'<h2>{escape_xml(sheet_name)}</h2>')

            # 过滤空行
            df = df.dropna(how='all')

            if df.empty:
                xml_parts.append('<p>（此工作表为空）</p>')
                continue

            # 超大表格警告
            if len(df.columns) > 10:
                xml_parts.append(
                    '<highlightBlock emoji="⚠️" highlightBlockBackgroundColor="#FAE6E6" '
                    'highlightBlockBorderColor="#F2A7A7">'
                    f'<p>此表格有 {len(df.columns)} 列，在 WPS 笔记中可能显示不佳。</p>'
                    '</highlightBlock>'
                )

            if len(df) > 100:
                xml_parts.append(
                    '<highlightBlock emoji="ℹ️" highlightBlockBackgroundColor="#E6EEFA" '
                    'highlightBlockBorderColor="#98C1FF">'
                    f'<p>此表格有 {len(df)} 行，只导入前 100 行。</p>'
                    '</highlightBlock>'
                )
                df = df.head(100)

            # 转换为 WPS table
            xml = '<table><tr>'
            for col in df.columns:
                xml += f'<td><p><strong>{escape_xml(str(col))}</strong></p></td>'
            xml += '</tr>'
            for _, row in df.iterrows():
                xml += '<tr>'
                for val in row:
                    cell_val = '' if (val is None or (isinstance(val, float) and str(val) == 'nan')) else str(val)
                    xml += f'<td><p>{escape_xml(cell_val)}</p></td>'
                xml += '</tr>'
            xml += '</table>'
            xml_parts.append(xml)

    except Exception as e:
        xml_parts.append(f'<p>❌ XLSX 读取失败：{escape_xml(str(e))}</p>')

    return '\n'.join(xml_parts), {}, {}


# ─── 思源笔记 .sy → WPS XML ──────────────────────────────────────────────────

def siyuan_to_wps_xml(file_path: Path, workspace_root: Path = None) -> tuple:
    """思源笔记 .sy 文件转换为 WPS XML"""
    images = {}
    img_counter = [0]

    assets_dir = None
    if workspace_root:
        assets_dir = workspace_root / 'data' / 'assets'
        if not assets_dir.exists():
            assets_dir = workspace_root / 'assets'

    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        return f'<p>❌ 思源笔记文件解析失败：{escape_xml(str(e))}</p>', {}, {}

    def parse_inline(children: list) -> str:
        """解析行内节点"""
        result = []
        for child in children:
            ntype = child.get('Type', '')
            data = escape_xml(child.get('Data', ''))
            if ntype == 'NodeText':
                result.append(data)
            elif ntype == 'NodeStrong':
                inner = parse_inline(child.get('Children', []))
                result.append(f'<strong>{inner}</strong>')
            elif ntype == 'NodeEmphasis':
                inner = parse_inline(child.get('Children', []))
                result.append(f'<em>{inner}</em>')
            elif ntype == 'NodeStrikethrough':
                inner = parse_inline(child.get('Children', []))
                result.append(f'<s>{inner}</s>')
            elif ntype == 'NodeLink':
                inner = parse_inline(child.get('Children', []))
                href = child.get('Data', '')
                result.append(f'<a href="{escape_xml(href)}">{inner}</a>')
            elif ntype == 'NodeCodeSpan':
                result.append(data)
            else:
                result.append(data)
        return ''.join(result)

    def parse_node(node: dict) -> str:
        ntype = node.get('Type', '')
        children = node.get('Children', [])

        if ntype in ('NodeDocument',):
            return '\n'.join(parse_node(c) for c in children)

        elif ntype == 'NodeHeading':
            level = node.get('HeadingLevel', 1)
            text = parse_inline([c for c in children if c.get('Type') == 'NodeText']
                                 or children)
            if not text:
                text = escape_xml(node.get('Data', ''))
            return f'<h{level}>{text}</h{level}>'

        elif ntype == 'NodeParagraph':
            content = parse_inline(children)
            return f'<p>{content}</p>' if content else '<p></p>'

        elif ntype == 'NodeBlockquote':
            inner = '\n'.join(parse_node(c) for c in children)
            return f'<blockquote>{inner}</blockquote>'

        elif ntype == 'NodeCodeBlock':
            lang = node.get('CodeBlockInfo', '') or ''
            code = escape_xml(node.get('Data', ''))
            return f'<codeblock lang="{escape_xml(lang)}">{code}</codeblock>'

        elif ntype == 'NodeList':
            return '\n'.join(parse_node(c) for c in children)

        elif ntype == 'NodeListItem':
            list_data = node.get('ListData', {})
            btype = list_data.get('BType', 0)
            indent = list_data.get('Indent', 0)
            list_type = 'bullet' if btype == 0 else 'ordered'
            # 找第一个段落子节点的内容
            content = ''
            for c in children:
                if c.get('Type') == 'NodeParagraph':
                    content = parse_inline(c.get('Children', []))
                    break
            # 子列表
            sub_items = [parse_node(c) for c in children if c.get('Type') == 'NodeList']
            result = f'<p listType="{list_type}" listLevel="{indent}">{content}</p>'
            result += '\n'.join(sub_items)
            return result

        elif ntype == 'NodeTable':
            rows_xml = '<table>'
            for row in children:
                if row.get('Type') != 'NodeTableRow':
                    continue
                rows_xml += '<tr>'
                for cell in row.get('Children', []):
                    if cell.get('Type') not in ('NodeTableCell',):
                        continue
                    cell_content = parse_inline(cell.get('Children', []))
                    rows_xml += f'<td><p>{cell_content}</p></td>'
                rows_xml += '</tr>'
            rows_xml += '</table>'
            return rows_xml

        elif ntype == 'NodeImage':
            asset_path = node.get('Data', '')
            if assets_dir and asset_path:
                full_path = assets_dir / Path(asset_path).name
                img_counter[0] += 1
                placeholder = make_placeholder(img_counter[0])
                if full_path.exists():
                    b64 = read_image_as_base64(full_path)
                    images[placeholder] = b64
                else:
                    images[placeholder] = asset_path
                return f'<p>{placeholder}</p>'
            return ''

        elif ntype == 'NodeThematicBreak':
            return '<hr/>'

        elif ntype in ('NodeHTMLBlock', 'NodeInlineHTML'):
            return ''

        return ''

    xml = parse_node(data)

    # 提取文档属性作为 frontmatter
    props = data.get('Properties', {})
    frontmatter = {k: v for k, v in props.items() if k not in ('id',)}

    return xml, images, frontmatter


# ─── Meta 信息块生成 ──────────────────────────────────────────────────────────

def build_meta_blockquote(
    file_path: Path,
    root_path: Path,
    source_type: str,
    frontmatter: dict = None,
    siyuan_id: str = '',
    notebook_name: str = '',
) -> str:
    """生成导入 meta 信息的 blockquote XML"""
    stat = file_path.stat()
    modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    import_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    size = human_size(stat.st_size)

    try:
        rel_path = str(file_path.relative_to(root_path))
    except ValueError:
        rel_path = str(file_path)

    source_labels = {
        'obsidian': 'Obsidian Vault',
        'siyuan': '思源笔记',
        'generic': '通用目录',
    }
    source_label = source_labels.get(source_type, source_type)

    lines = [
        f'<p>📄 <strong>导入来源</strong>：<code>{escape_xml(rel_path)}</code></p>',
        f'<p>📁 <strong>原始路径</strong>：<code>{escape_xml(str(file_path))}</code></p>',
        f'<p>🕒 <strong>文件修改时间</strong>：{modified}</p>',
        f'<p>📦 <strong>文件大小</strong>：{size}</p>',
        f'<p>🔄 <strong>导入时间</strong>：{import_time}</p>',
        f'<p>📂 <strong>来源类型</strong>：{source_label}</p>',
    ]

    if siyuan_id:
        lines.append(f'<p>🆔 <strong>思源 ID</strong>：<code>{escape_xml(siyuan_id)}</code></p>')
    if notebook_name:
        lines.append(f'<p>📓 <strong>所属笔记本</strong>：{escape_xml(notebook_name)}</p>')

    if frontmatter:
        lines.append('<p>📝 <strong>文档属性：</strong></p>')
        for k, v in frontmatter.items():
            if k not in ('created', 'updated'):
                lines.append(f'<p>　{escape_xml(k)}：{escape_xml(str(v))}</p>')

    return '<blockquote>' + ''.join(lines) + '</blockquote>'


# ─── 主转换入口 ───────────────────────────────────────────────────────────────

def convert_file(
    file_path: Path,
    output_dir: Path,
    source_type: str = 'generic',
    vault_root: Path = None,
    workspace_root: Path = None,
    use_ocr: bool = False,
    root_path: Path = None,
) -> dict:
    """
    转换单个文件，输出到 output_dir

    Returns:
        dict: {success, note_title, xml_path, images_path, meta_path, error}
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = file_path.suffix.lower().lstrip('.')
    note_title = file_path.stem

    frontmatter = {}
    siyuan_id = ''
    notebook_name = ''

    # 根据格式转换
    if ext in ('md', 'markdown'):
        xml, images, frontmatter = markdown_to_wps_xml(
            file_path.read_text(encoding='utf-8', errors='ignore'),
            source_type=source_type,
            base_dir=file_path.parent,
            vault_root=vault_root,
        )
    elif ext == 'pdf':
        xml, images, frontmatter = pdf_to_wps_xml(file_path, use_ocr=use_ocr)
    elif ext == 'docx':
        xml, images, frontmatter = docx_to_wps_xml(file_path)
    elif ext == 'pptx':
        xml, images, frontmatter = pptx_to_wps_xml(file_path)
    elif ext in ('xlsx', 'xls'):
        xml, images, frontmatter = xlsx_to_wps_xml(file_path)
    elif ext == 'sy':
        data = json.loads(file_path.read_text(encoding='utf-8'))
        siyuan_id = data.get('ID', '')
        note_title = data.get('Properties', {}).get('title', file_path.stem)
        if workspace_root:
            # 推断笔记本名
            try:
                rel = file_path.relative_to(workspace_root / 'data')
                notebook_name = rel.parts[0] if rel.parts else ''
            except Exception:
                pass
        xml, images, frontmatter = siyuan_to_wps_xml(file_path, workspace_root=workspace_root)
    elif ext == 'txt':
        text = file_path.read_text(encoding='utf-8', errors='ignore')
        xml = '\n'.join(f'<p>{escape_xml(l)}</p>' for l in text.split('\n'))
        images = {}
    else:
        return {'success': False, 'error': f'不支持的格式：{ext}'}

    # 构建 meta blockquote
    meta_xml = build_meta_blockquote(
        file_path=file_path,
        root_path=root_path or file_path.parent,
        source_type=source_type,
        frontmatter=frontmatter,
        siyuan_id=siyuan_id,
        notebook_name=notebook_name,
    )

    # 处理图片：本地路径 → base64
    resolved_images = {}
    for placeholder, src in images.items():
        if src.startswith('data:'):
            resolved_images[placeholder] = src
        elif src.startswith(('http://', 'https://')):
            resolved_images[placeholder] = src
        else:
            img_path = Path(src)
            if img_path.exists():
                resolved_images[placeholder] = read_image_as_base64(img_path)
            else:
                resolved_images[placeholder] = src

    # 保存输出
    (output_dir / 'content.xml').write_text(xml, encoding='utf-8')
    (output_dir / 'meta.xml').write_text(meta_xml, encoding='utf-8')
    (output_dir / 'images.json').write_text(
        json.dumps(resolved_images, ensure_ascii=False), encoding='utf-8'
    )

    meta = {
        'note_title': note_title,
        'source_file': str(file_path),
        'source_type': source_type,
        'ext': ext,
        'image_count': len(resolved_images),
        'frontmatter': frontmatter,
    }
    (output_dir / 'meta.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    return {
        'success': True,
        'note_title': note_title,
        'xml_path': str(output_dir / 'content.xml'),
        'meta_xml_path': str(output_dir / 'meta.xml'),
        'images_path': str(output_dir / 'images.json'),
        'meta_path': str(output_dir / 'meta.json'),
        'image_count': len(resolved_images),
    }


def main():
    parser = argparse.ArgumentParser(description='将文档转换为 WPS 笔记 XML')
    parser.add_argument('file', help='要转换的文件路径')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--source', default='generic',
                        choices=['obsidian', 'siyuan', 'generic'],
                        help='来源类型')
    parser.add_argument('--vault-root', help='Obsidian Vault 根目录')
    parser.add_argument('--workspace-root', help='思源笔记工作空间根目录')
    parser.add_argument('--ocr', action='store_true', help='启用 OCR（扫描版 PDF）')
    parser.add_argument('--root-path', help='扫描根目录（用于生成相对路径）')
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f'❌ 文件不存在：{file_path}', file=sys.stderr)
        sys.exit(1)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(args.output_dir) if args.output_dir else Path(f'/tmp/doc_import_{ts}')

    result = convert_file(
        file_path=file_path,
        output_dir=output_dir,
        source_type=args.source,
        vault_root=Path(args.vault_root) if args.vault_root else None,
        workspace_root=Path(args.workspace_root) if args.workspace_root else None,
        use_ocr=args.ocr,
        root_path=Path(args.root_path) if args.root_path else None,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
