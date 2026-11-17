#!/usr/bin/env python3
"""
WPS 笔记导出为公众号 HTML 格式
使用: python export-to-html.py --note-id <笔记ID> [--template <模板名>] [--output <路径>]

读取策略：优先使用 wpsnote-cli CLI，CLI 不可用时降级到 MCP 工具（由 AI Agent 调用）。
"""

import argparse
import re
import html as html_module
import base64
import json
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

_COMM_SCRIPT_DIR = Path(__file__).resolve().parents[3] / "comm_script"
if str(_COMM_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_COMM_SCRIPT_DIR))

import wps_cli  # noqa: E402


def _cli_available() -> bool:
    """检查 wpsnote-cli 是否可用"""
    return wps_cli.cli_available()


def _cli_run(args: list) -> Optional[dict]:
    """
    运行 wpsnote-cli 命令并返回解包后的业务 JSON。
    失败时返回 None。
    """
    res = wps_cli.cli(args, timeout=30)
    if not res.get("ok"):
        print(f"   ⚠️  CLI 调用失败: {res.get('message', '')}")
        return None
    return res.get("data") or None


def cli_read_note(note_id: str) -> Optional[dict]:
    """
    通过 wpsnote-cli 读取笔记内容。
    返回 { title, content, word_count } 或 None（失败时）。
    """
    data = _cli_run(["read", "--note_id", note_id])
    if data and data.get("content"):
        return data
    return None


def cli_find_note(keyword: str) -> Optional[str]:
    """
    通过 wpsnote-cli 搜索笔记，返回第一个匹配的 note_id 或 None。
    """
    data = _cli_run(["find", "--keywords", json.dumps([keyword], ensure_ascii=False), "--limit", "1"])
    if data:
        notes = data.get("items") or data.get("notes") or data.get("results") or []
        if notes:
            return notes[0].get("note_id") or notes[0].get("id")
    return None


def cli_current_note() -> Optional[str]:
    """
    获取当前编辑中笔记 ID（云端 CLI 无桌面编辑器上下文，恒返回 None）。
    """
    return None


class WPSNoteExporter:
    """WPS 笔记导出器 - 将笔记内容转换为公众号 HTML 格式"""

    # 颜色配置（默认）
    COLOR_ORANGE = "rgb(255, 104, 39)"
    COLOR_BLUE = "rgb(0, 128, 255)"
    COLOR_GRAY = "rgb(100, 106, 115)"
    COLOR_LGRAY = "rgb(153, 153, 153)"
    COLOR_BG_GRAY = "rgb(245, 245, 245)"
    COLOR_BORDER = "rgb(230, 230, 230)"

    # 字体配置
    FONT_FAMILY = "mp-quote, 'PingFang SC', -apple-system-font, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif"
    MONO_FAMILY = "'Menlo', 'Monaco', 'Courier New', monospace"

    # 语法高亮颜色
    CODE_COLORS = {
        "keyword": "rgb(207, 34, 46)",
        "string": "rgb(14, 118, 50)",
        "comment": "rgb(140, 149, 159)",
        "number": "rgb(5, 80, 174)",
        "builtin": "rgb(111, 66, 193)",
        "operator": "rgb(60, 80, 100)",
        "decorator": "rgb(207, 34, 46)",
        "default": "rgb(36, 41, 47)",
    }

    # 语言规则
    LANG_RULES = {
        "python": [
            (r'#[^\n]*', "comment"),
            (r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "string"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'@\w+', "decorator"),
            (r'\b(def|class|import|from|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|try|except|finally|with|as|pass|break|continue|raise|lambda|yield|async|await)\b', "keyword"),
            (r'\b(print|len|range|str|int|float|list|dict|set|tuple|bool|type|open|super|self|cls)\b', "builtin"),
            (r'\b\d+\.?\d*\b', "number"),
            (r'[+\-*/=<>!&|^~%]+', "operator"),
        ],
        "javascript": [
            (r'//[^\n]*', "comment"),
            (r'/\*[\s\S]*?\*/', "comment"),
            (r'`(?:\\.|[^`\\])*`', "string"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false)\b', "keyword"),
            (r'\b(console|Math|Object|Array|String|Number|Boolean|Promise|fetch|setTimeout|setInterval|JSON|window|document)\b', "builtin"),
            (r'\b\d+\.?\d*\b', "number"),
            (r'[+\-*/=<>!&|^~%?:]+', "operator"),
        ],
        "typescript": [
            (r'//[^\n]*', "comment"),
            (r'/\*[\s\S]*?\*/', "comment"),
            (r'`(?:\\.|[^`\\])*`', "string"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false|type|interface|enum|namespace|declare|abstract|implements|readonly|private|public|protected|as|keyof)\b', "keyword"),
            (r'\b(string|number|boolean|any|void|never|unknown|object|Array|Promise|Record|Partial|Required|Readonly)\b', "builtin"),
            (r'\b\d+\.?\d*\b', "number"),
            (r'[+\-*/=<>!&|^~%?:]+', "operator"),
        ],
        "bash": [
            (r'#[^\n]*', "comment"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|export|local|echo|exit|in|true|false)\b', "keyword"),
            (r'\$\{?[\w@#?*!]+\}?', "builtin"),
            (r'\b\d+\b', "number"),
            (r'[|&;<>]+', "operator"),
        ],
        "yaml": [
            (r'#[^\n]*', "comment"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'^(\s*[\w\-]+)(?=\s*:)', "keyword"),
            (r'\b(true|false|null|yes|no)\b', "builtin"),
            (r'\b\d+\.?\d*\b', "number"),
            (r'[:\-\[\]{}|>]+', "operator"),
        ],
        "json": [
            (r'"(?:\\.|[^"\\])*"(?=\s*:)', "keyword"),
            (r'"(?:\\.|[^"\\])*"', "string"),
            (r'\b(true|false|null)\b', "builtin"),
            (r'\b-?\d+\.?\d*(?:[eE][+-]?\d+)?\b', "number"),
            (r'[{}\[\]:,]+', "operator"),
        ],
        "css": [
            (r'/\*[\s\S]*?\*/', "comment"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'[.#]?[\w-]+(?=\s*\{)', "keyword"),
            (r'(?<=:\s)[\w-]+', "builtin"),
            (r'#[0-9a-fA-F]{3,8}\b', "string"),
            (r'\b\d+\.?\d*(?:px|em|rem|%|vh|vw|s|ms)?\b', "number"),
            (r'[:;{}()]+', "operator"),
        ],
        "html": [
            (r'<!--[\s\S]*?-->', "comment"),
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "string"),
            (r'</?\w[\w-]*', "keyword"),
            (r'[\w-]+=', "builtin"),
            (r'[<>/=]+', "operator"),
        ],
    }

    def __init__(self, skill_dir: Optional[Path] = None):
        """
        初始化导出器

        Args:
            skill_dir: Skill 根目录，默认为脚本所在目录的父目录
        """
        if skill_dir is None:
            skill_dir = Path(__file__).parent.parent
        self.skill_dir = Path(skill_dir)
        self.template_dir = self.skill_dir / "templates"
        self.template_config: Dict[str, Any] = {}
        self._init_lang_rules()

    def _init_lang_rules(self):
        """初始化语言规则别名"""
        self.LANG_RULES["sh"] = self.LANG_RULES["bash"]
        self.LANG_RULES["js"] = self.LANG_RULES["javascript"]
        self.LANG_RULES["ts"] = self.LANG_RULES["typescript"]
        self.LANG_RULES["py"] = self.LANG_RULES["python"]

    def read_note(self, note_id: str) -> dict:
        """
        读取 WPS 笔记内容。

        优先策略：
          1. wpsnote-cli read --note_id <id> --json   （CLI 可用时）
          2. 降级：由 AI Agent 通过 MCP read_note 提供数据，
             或传入 --xml-content 参数直接解析

        Args:
            note_id: 笔记 ID

        Returns:
            包含 title, content, blocks 的字典
        """
        print(f"📖 正在读取笔记: {note_id}")

        if _cli_available():
            print("   → 使用 wpsnote-cli 读取")
            note = cli_read_note(note_id)
            if note:
                return {
                    "note_id": note_id,
                    "title": note.get("title", "untitled"),
                    "content": note.get("content", ""),
                    "blocks": [],
                }
            print("   ⚠️  CLI 读取失败，请由 AI Agent 通过 MCP 提供内容")
        else:
            print("   → wpsnote-cli 不可用，请由 AI Agent 通过 MCP 工具读取后传入 --xml-file 参数")

        # 无法自动读取时返回空内容，让调用方处理
        return {
            "note_id": note_id,
            "title": "untitled",
            "content": "",
            "blocks": [],
        }

    def _get_sample_xml(self) -> str:
        """获取示例 XML 内容（用于测试）"""
        return '''<h1>示例文章标题</h1>
<p>这是一段普通正文，包含<b/>加粗文字</b>和正常文字。</p>
<h2>第一章节</h2>
<p>章节内容在这里。</p>
<h3>小节标题</h3>
<p><b/>整段橙色加粗的重要结论。</b></p>
<blockquote>这是一个引用块的内容。</blockquote>
<codeblock lang="python">def hello():
    print("Hello, World!")</codeblock>
<p><note/>这是一个注释说明。</note></p>'''

    def xml_to_markdown(self, xml_content: str) -> str:
        """
        将 WPS 笔记 XML 转换为 Markdown

        支持的 XML 标签:
        - <p>: 段落
        - <h1>-<h6>: 标题
        - <strong>: 粗体
        - <em>: 斜体
        - <a>: 链接
        - <blockquote>: 引用块
        - <codeblock>: 代码块
        - <table>: 表格
        - <columns>: 分栏布局
        - <highlightBlock>: 高亮块
        - <emoji>: 表情符号

        Args:
            xml_content: WPS 笔记 XML 内容

        Returns:
            Markdown 格式文本
        """
        md_content = xml_content

        # 处理占位符标签（在标准标签之前处理）
        md_content = self._process_placeholder_tags(md_content)

        # 标题 h1-h6
        for i in range(1, 7):
            md_content = re.sub(
                rf'<h{i}[^>]*>(.*?)</h{i}>',
                rf'{"#" * i} \1\n\n',
                md_content,
                flags=re.DOTALL
            )

        # 引用块
        md_content = re.sub(
            r'<blockquote[^>]*>(.*?)</blockquote>',
            lambda m: self._convert_blockquote(m.group(1)),
            md_content,
            flags=re.DOTALL
        )

        # 代码块
        md_content = re.sub(
            r'<codeblock[^>]*lang="([^"]*)"[^>]*>(.*?)</codeblock>',
            r'```\1\n\2\n```\n\n',
            md_content,
            flags=re.DOTALL
        )

        # 高亮块
        md_content = re.sub(
            r'<highlightBlock[^>]*>(.*?)</highlightBlock>',
            lambda m: self._convert_highlight(m.group(1)),
            md_content,
            flags=re.DOTALL
        )

        # 表格
        md_content = re.sub(
            r'<table[^>]*>(.*?)</table>',
            lambda m: self._convert_table(m.group(1)),
            md_content,
            flags=re.DOTALL
        )

        # 分栏
        md_content = re.sub(
            r'<columns[^>]*>(.*?)</columns>',
            lambda m: self._convert_columns(m.group(1)),
            md_content,
            flags=re.DOTALL
        )

        # 段落（处理内联样式）
        md_content = re.sub(
            r'<p[^>]*>(.*?)</p>',
            lambda m: self._convert_inline_styles(m.group(1)),
            md_content,
            flags=re.DOTALL
        )

        # 清理剩余标签
        md_content = re.sub(r'<[^>]+>', '', md_content)

        # 清理多余空行
        md_content = re.sub(r'\n{3,}', '\n\n', md_content)

        return md_content.strip()

    def _process_placeholder_tags(self, xml_content: str) -> str:
        """
        处理占位符标签

        转换规则:
        - <b/>...</b> → !!...!! （橙色加粗）
        - <h2/>...</h2> → ## ... （蓝色大标题）
        - <h3/>...</h3> → ### ... （蓝色小标题）
        - <bq/>...</bq> → > ... （引用块）
        - <note/>...</note> → ~~...~~ （灰色小字）
        """
        # <b/>...</b> → !!...!!
        xml_content = re.sub(
            r'<b/>(.*?)</b>',
            r'!!\1!!',
            xml_content,
            flags=re.DOTALL
        )

        # <h2/>...</h2> → ## ...
        xml_content = re.sub(
            r'<h2/>(.*?)</h2>',
            r'## \1\n\n',
            xml_content,
            flags=re.DOTALL
        )

        # <h3/>...</h3> → ### ...
        xml_content = re.sub(
            r'<h3/>(.*?)</h3>',
            r'### \1\n\n',
            xml_content,
            flags=re.DOTALL
        )

        # <bq/>...</bq> → > ...
        xml_content = re.sub(
            r'<bq/>(.*?)</bq>',
            lambda m: self._convert_placeholder_blockquote(m.group(1)),
            xml_content,
            flags=re.DOTALL
        )

        # <note/>...</note> → ~~...~~
        xml_content = re.sub(
            r'<note/>(.*?)</note>',
            r'~~\1~~\n\n',
            xml_content,
            flags=re.DOTALL
        )

        return xml_content

    def _convert_placeholder_blockquote(self, content: str) -> str:
        """转换占位符引用块"""
        lines = content.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines if line.strip())
        return quoted + '\n\n'

    # WPS 预设 fontColor 色板 → RGB（任意非预设色值被编辑器静默丢弃，此处同样忽略）
    WPS_FONT_COLORS = {
        "#080F17": "rgb(8,15,23)",
        "#C21C13": "rgb(194,28,19)",
        "#DB7800": "rgb(219,120,0)",
        "#078654": "rgb(7,134,84)",
        "#0E52D4": "rgb(14,82,212)",
        "#0080A0": "rgb(0,128,160)",
        "#757575": "rgb(117,117,117)",
        "#DA326B": "rgb(218,50,107)",
        "#D1A300": "rgb(209,163,0)",
        "#58A401": "rgb(88,164,1)",
        "#116AF0": "rgb(17,106,240)",
        "#A639D7": "rgb(166,57,215)",
    }

    # WPS 预设 fontHighlightColor 色板 → RGB
    WPS_HIGHLIGHT_COLORS = {
        "#FBF5B3": "rgb(251,245,179)",
        "#F8D7B7": "rgb(248,215,183)",
        "#F7C7D3": "rgb(247,199,211)",
        "#DFF0C4": "rgb(223,240,196)",
        "#C6EADD": "rgb(198,234,221)",
        "#D9EEFB": "rgb(217,238,251)",
        "#D5DCF7": "rgb(213,220,247)",
        "#E6D6F0": "rgb(230,214,240)",
        "#E6E6E6": "rgb(230,230,230)",
    }

    def _convert_wps_span(self, attrs: str, inner: str) -> str:
        """
        将 WPS <span fontColor="..." fontHighlightColor="..." fontSize="...">
        转换为带内联样式的 HTML <span>。
        只处理预设色板中的颜色，非预设色值忽略（与 WPS 编辑器行为一致）。
        """
        style_parts = []

        fc_match = re.search(r'fontColor="([^"]+)"', attrs)
        if fc_match:
            hex_val = fc_match.group(1).upper()
            rgb = self.WPS_FONT_COLORS.get(hex_val)
            if rgb:
                style_parts.append(f"color: {rgb};")

        fh_match = re.search(r'fontHighlightColor="([^"]+)"', attrs)
        if fh_match:
            hex_val = fh_match.group(1).upper()
            rgb = self.WPS_HIGHLIGHT_COLORS.get(hex_val)
            if rgb:
                style_parts.append(
                    f"background-color: {rgb}; padding: 0 2px; border-radius: 2px;"
                )

        fs_match = re.search(r'fontSize="([^"]+)"', attrs)
        if fs_match:
            style_parts.append(f"font-size: {fs_match.group(1)}px;")

        if style_parts:
            return f'<span style="{" ".join(style_parts)}">{inner}</span>'
        return inner

    def _convert_inline_styles(self, text: str) -> str:
        """转换内联样式，包含 WPS 预设颜色映射"""
        # WPS <span fontColor/fontHighlightColor/fontSize> → 内联样式 HTML span
        text = re.sub(
            r'<span\s([^>]*(?:fontColor|fontHighlightColor|fontSize)[^>]*)>(.*?)</span>',
            lambda m: self._convert_wps_span(m.group(1), m.group(2)),
            text,
            flags=re.DOTALL
        )
        # 粗体
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
        # 斜体
        text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
        # 行内代码
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
        # 链接
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text)

        return text + '\n\n'

    def _convert_blockquote(self, content: str) -> str:
        """转换引用块"""
        lines = content.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines if line.strip())
        return quoted + '\n\n'

    def _convert_highlight(self, content: str) -> str:
        """转换高亮块"""
        # 提取 emoji 图标
        emoji_match = re.search(r'<emoji[^>]*value="([^"]*)"', content)
        emoji = emoji_match.group(1) if emoji_match else '💡'

        # 提取文本内容
        text = re.sub(r'<[^>]+>', '', content).strip()

        return f'{emoji} **提示**\n\n{text}\n\n'

    def _convert_table(self, content: str) -> str:
        """
        转换表格为 Markdown 格式

        WPS XML 表格格式:
        <table>
          <tr><td><p>单元格1</p></td><td><p>单元格2</p></td></tr>
          <tr><td><p>单元格3</p></td><td><p>单元格4</p></td></tr>
        </table>
        """
        md_lines = ['']

        # 提取所有行
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, flags=re.DOTALL)

        for i, row in enumerate(rows):
            # 提取单元格（支持 td 和 th）
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, flags=re.DOTALL)
            # 清理单元格内容中的标签
            cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

            if cells:
                md_lines.append('| ' + ' | '.join(cells) + ' |')

                # 第一行后面添加分隔符
                if i == 0:
                    md_lines.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')

        md_lines.append('')
        return '\n'.join(md_lines)

    def _convert_columns(self, content: str) -> str:
        """
        转换分栏为 Markdown 格式

        WPS XML 分栏格式:
        <columns>
          <column><p>左栏内容</p></column>
          <column><p>右栏内容</p></column>
        </columns>

        转换为：
        <!-- COLUMNS -->
        | 左栏内容 | 右栏内容 |
        <!-- /COLUMNS -->
        """
        # 提取所有 column
        columns = re.findall(r'<column[^>]*>(.*?)</column>', content, flags=re.DOTALL)

        if not columns:
            return ''

        # 清理每个 column 的内容
        cleaned_columns = []
        for col in columns:
            # 移除所有标签，保留文本
            text = re.sub(r'<[^>]+>', '', col).strip()
            cleaned_columns.append(text)

        # 使用 HTML 注释标记分栏，便于后续渲染
        md = '\n<!-- COLUMNS -->\n'
        md += '| ' + ' | '.join(cleaned_columns) + ' |\n'
        md += '<!-- /COLUMNS -->\n\n'

        return md

    def apply_placeholders(self, md_content: str) -> str:
        """
        处理 Markdown 中的占位符语法

        已经由 _process_placeholder_tags 处理完成，
        此方法用于二次确认和额外处理
        """
        return md_content

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        加载 YAML 模板配置

        Args:
            template_name: 模板名称（不含扩展名）

        Returns:
            模板配置字典
        """
        template_path = self.template_dir / f"{template_name}.yaml"

        if not template_path.exists():
            print(f"⚠️  模板不存在: {template_path}，使用默认配置")
            return self._get_default_template()

        with open(template_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.template_config = config
        return config

    def _get_default_template(self) -> Dict[str, Any]:
        """获取默认模板配置"""
        return {
            "colors": {
                "primary": "rgb(255, 104, 39)",
                "accent": "rgb(0, 128, 255)",
                "text": "rgb(100, 106, 115)",
                "bg_block": "rgb(245, 245, 245)",
            },
            "fonts": {
                "family": {
                    "body": "PingFang SC, -apple-system-font, sans-serif",
                    "mono": "Menlo, Monaco, Courier New, monospace"
                },
                "size": {
                    "body": 16,
                    "h2": 18,
                    "h3": 16
                }
            },
            "spacing": {
                "line_height_body": 2.0,
                "paragraph_gap": 15,
                "max_width": 677
            }
        }

    def markdown_to_html(self, md_content: str, template: Optional[Dict[str, Any]] = None) -> str:
        """
        将 Markdown 转换为带内联样式的 HTML

        Args:
            md_content: Markdown 内容
            template: 模板配置（可选）

        Returns:
            带内联样式的 HTML
        """
        if template is None:
            template = self._get_default_template()

        # 获取样式配置
        colors = template.get("colors", {})
        fonts = template.get("fonts", {})
        spacing = template.get("spacing", {})
        features = template.get("features", {})

        primary_color = colors.get("primary", self.COLOR_ORANGE)
        accent_color = colors.get("accent", self.COLOR_BLUE)
        text_color = colors.get("text", self.COLOR_GRAY)
        bg_block_color = colors.get("bg_block", self.COLOR_BG_GRAY)
        quote_border_color = colors.get("quote_border", accent_color)  # 引用块边框颜色

        font_family = fonts.get("family", {}).get("body", self.FONT_FAMILY)
        mono_family = fonts.get("family", {}).get("mono", self.MONO_FAMILY)

        body_size = fonts.get("size", {}).get("body", 16)
        h2_size = fonts.get("size", {}).get("h2", 18)
        h3_size = fonts.get("size", {}).get("h3", 16)

        line_height = spacing.get("line_height_body", 2.0)
        para_gap = spacing.get("paragraph_gap", 15)
        max_width = spacing.get("max_width", 677)

        # 功能开关
        use_flex_columns = features.get("flex_columns", True)

        # 构建样式字典
        styles = {
            "p": f'style="margin: 0px 0px {para_gap}px 0px; padding: 0px; outline: 0px; max-width: 100%; clear: both; min-height: 20px; word-break: break-all; color: {text_color}; font-size: {body_size}px; line-height: {line_height};"',
            "span": f'style="font-size: {body_size}px; color: {text_color}; font-family: {font_family}; white-space: pre-wrap;"',
            "bold_inline": f'style="font-size: {body_size}px; font-weight: bold; color: {primary_color}; font-family: {font_family};"',
            "hb": f'style="font-size: {body_size}px; font-weight: bold; color: {primary_color}; font-family: {font_family}; white-space: pre-wrap;"',
            "h2": f'style="margin: 30px 0px 15px 0px; padding: 0px; font-size: {h2_size}px; font-weight: bold; color: {accent_color}; line-height: 1.6;"',
            "h3": f'style="margin: 20px 0px 10px 0px; padding: 0px; font-size: {h3_size}px; font-weight: bold; color: {accent_color}; line-height: 1.6;"',
            "blockquote": f'style="margin: 20px 0px; padding: 15px 20px; background-color: {bg_block_color}; border-left: 4px solid {accent_color}; font-size: 15px; color: {text_color}; line-height: 1.8;"',
            "blockquote_p": f'style="margin: 0px; padding: 0px; font-family: {font_family};"',
            "hr": f'style="margin: 25px 0px; border: none; border-top: 1px solid {self.COLOR_BORDER};"',
            "note": f'style="margin: 20px 0px 0px 0px; padding: 0px; font-size: 14px; color: {self.COLOR_LGRAY}; line-height: 1.8;"',
            "section": f'style="max-width: {max_width}px; margin: 0 auto; background-color: #fff; padding: 20px; font-family: {font_family};"',
            "body": 'style="margin: 0; padding: 20px; background-color: #f5f5f5;"',
        }

        # 解析 Markdown 为 HTML 内容
        content_html = self._parse_md_to_html(
            md_content, styles, font_family, mono_family,
            primary_color, accent_color, text_color,
            quote_border_color, use_flex_columns
        )

        # 加载 HTML 模板
        template_html = self._load_html_template()

        # 替换模板变量
        html_output = template_html.replace("{{ content }}", content_html)
        html_output = html_output.replace("{{ date }}", datetime.now().strftime("%Y-%m-%d"))

        return html_output

    def _parse_md_to_html(self, md_content: str, styles: Dict[str, str],
                          font_family: str, mono_family: str,
                          primary_color: str, accent_color: str, text_color: str,
                          quote_border_color: str = None, use_flex_columns: bool = True) -> str:
        """将 Markdown 解析为 HTML"""
        lines = md_content.split('\n')
        result = []
        i = 0
        ul_items, ol_items = [], []

        def flush_ul():
            if ul_items:
                result.append(self._render_ul(ul_items, styles, font_family, primary_color, text_color))
                ul_items.clear()

        def flush_ol():
            if ol_items:
                result.append(self._render_ol(ol_items, styles, font_family, primary_color, text_color))
                ol_items.clear()

        def flush_lists():
            flush_ul()
            flush_ol()

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                flush_lists()
                i += 1
                continue

            # 代码块
            if stripped.startswith('```'):
                flush_lists()
                lang = stripped[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                result.append(self._render_codeblock('\n'.join(code_lines), lang, mono_family, text_color))
                i += 1
                continue

            # h1/h2 标题
            if stripped.startswith('# ') and not stripped.startswith('## '):
                flush_lists()
                result.append(f'<h2 {styles["h2"]}>{stripped[2:].strip()}</h2>')
                i += 1
                continue

            if stripped.startswith('## '):
                flush_lists()
                result.append(f'<h2 {styles["h2"]}>{stripped[3:].strip()}</h2>')
                i += 1
                continue

            # h3 标题
            if stripped.startswith('### '):
                flush_lists()
                result.append(self._render_h3(stripped[4:].strip(), styles, font_family, accent_color))
                i += 1
                continue

            # 更高级标题转为 h3
            if re.match(r'^#{4,}\s', stripped):
                flush_lists()
                result.append(self._render_h3(re.sub(r'^#{4,}\s+', '', stripped), styles, font_family, accent_color))
                i += 1
                continue

            # !!橙色加粗!!
            if stripped.startswith('!!') and stripped.endswith('!!') and len(stripped) > 4:
                flush_lists()
                result.append(self._render_hb(stripped[2:-2], styles))
                i += 1
                continue

            # 引用块
            if re.match(r'^>\s*\S', stripped) or stripped == '>':
                flush_lists()
                bq_lines = []
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith('> '):
                        bq_lines.append(s[2:])
                        i += 1
                    elif s == '>':
                        i += 1
                        break
                    else:
                        break
                if bq_lines:
                    result.append(self._render_blockquote('<br>'.join(bq_lines), styles, font_family, quote_border_color))
                continue

            # 分隔线
            if re.match(r'^[-*_]{3,}$', stripped):
                flush_lists()
                result.append(f'<hr {styles["hr"]}>')
                i += 1
                continue

            # 分栏标记
            if stripped == '<!-- COLUMNS -->':
                flush_lists()
                col_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() != '<!-- /COLUMNS -->':
                    if lines[i].strip():
                        col_lines.append(lines[i])
                    i += 1
                if col_lines:
                    result.append(self._render_columns(col_lines, styles, font_family, text_color, use_flex_columns))
                i += 1
                continue

            # 表格（Markdown 格式）
            if '|' in stripped and i + 1 < len(lines) and re.match(r'^\|?\s*:?-+:?\s*\|', lines[i + 1]):
                flush_lists()
                table_lines = []
                # 表头
                table_lines.append(stripped)
                i += 1
                # 分隔符
                if i < len(lines):
                    table_lines.append(lines[i].strip())
                    i += 1
                # 数据行
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i].strip())
                    i += 1
                result.append(self._render_table(table_lines, styles, font_family, text_color, accent_color))
                continue

            # 注释 ~~...~~
            if stripped.startswith('~~') and stripped.endswith('~~') and len(stripped) > 4:
                inner = stripped[2:-2]
                if '~~' not in inner:
                    flush_lists()
                    result.append(self._render_note(inner, styles, font_family))
                    i += 1
                    continue

            # 无序列表
            ul_match = re.match(r'^[-*+]\s+(.+)$', stripped)
            if ul_match:
                flush_ol()
                ul_items.append(ul_match.group(1))
                i += 1
                continue

            # 有序列表
            ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
            if ol_match:
                flush_ul()
                ol_items.append(ol_match.group(1))
                i += 1
                continue

            # 整行加粗 **...**
            if stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
                inner = stripped[2:-2]
                if '**' not in inner:
                    flush_lists()
                    result.append(self._render_bold_line(inner, styles))
                    i += 1
                    continue

            # 普通段落
            flush_lists()
            result.append(self._render_p(stripped, styles, font_family, primary_color, accent_color))
            i += 1

        flush_lists()
        return '\n\n'.join(result)

    def _render_p(self, text: str, styles: Dict[str, str], font_family: str,
                  primary_color: str, accent_color: str) -> str:
        """渲染段落"""
        processed = self._process_inline(text, font_family, primary_color, accent_color)
        return f'<p {styles["p"]}><span {styles["span"]}>{processed}</span></p>'

    def _render_hb(self, text: str, styles: Dict[str, str]) -> str:
        """渲染橙色加粗整段"""
        return f'<p {styles["p"]}><span {styles["hb"]}>{html_module.escape(text)}</span></p>'

    def _render_bold_line(self, text: str, styles: Dict[str, str]) -> str:
        """渲染整行加粗"""
        return f'<p {styles["p"]}><span {styles["bold_inline"]}>{html_module.escape(text)}</span></p>'

    def _render_h3(self, text: str, styles: Dict[str, str], font_family: str, accent_color: str) -> str:
        """渲染 h3 标题"""
        return f'<p {styles["p"]}><span {styles["h3"]}>{html_module.escape(text)}</span></p>'

    def _render_blockquote(self, text: str, styles: Dict[str, str],
                           font_family: str, quote_border_color: str = None) -> str:
        """渲染引用块"""
        # 获取基础样式（去掉外层的 style=" 和 "）
        blockquote_style = styles.get("blockquote", "")
        if blockquote_style.startswith('style="') and blockquote_style.endswith('"'):
            blockquote_style = blockquote_style[7:-1]  # 去掉 style=" 和 "

        # 使用模板中的引用边框颜色
        if quote_border_color:
            # 替换边框颜色
            blockquote_style = re.sub(
                r'border-left:\s*4px\s+solid\s+[^;]+',
                f'border-left: 3px solid {quote_border_color}',
                blockquote_style
            )

        return (f'<blockquote style="{blockquote_style}">\n'
                f'    <p {styles["blockquote_p"]}>{html_module.escape(text)}</p>\n'
                f'</blockquote>')

    def _render_note(self, text: str, styles: Dict[str, str], font_family: str) -> str:
        """渲染注释"""
        return f'<p {styles["note"]}><span style="font-family: {font_family};">{html_module.escape(text)}</span></p>'

    def _render_ul(self, items: list, styles: Dict[str, str], font_family: str,
                   primary_color: str, text_color: str) -> str:
        """渲染无序列表"""
        lines = []
        for item in items:
            processed = self._process_inline(item, font_family, primary_color, text_color)
            lines.append(
                f'<p {styles["p"]}><span {styles["span"]}>'
                f'<span style="color: {primary_color}; margin-right: 6px;">•</span>'
                f'{processed}</span></p>'
            )
        return '\n'.join(lines)

    def _render_ol(self, items: list, styles: Dict[str, str], font_family: str,
                   primary_color: str, text_color: str) -> str:
        """渲染有序列表"""
        lines = []
        for i, item in enumerate(items, 1):
            processed = self._process_inline(item, font_family, primary_color, text_color)
            lines.append(
                f'<p {styles["p"]}><span {styles["span"]}>'
                f'<span style="color: {primary_color}; font-weight: bold; margin-right: 6px;">{i}.</span>'
                f'{processed}</span></p>'
            )
        return '\n'.join(lines)

    def _render_codeblock(self, code: str, lang: str, mono_family: str, text_color: str) -> str:
        """渲染代码块"""
        if not lang:
            # 无语言标注的代码块
            lines = code.strip().split('\n')
            inner = '\n'.join(
                f'<p style="margin: 0 0 4px 0; padding: 0; font-size: 15px; color: {text_color}; '
                f'font-family: {self.FONT_FAMILY}; line-height: 1.8;">'
                f'{html_module.escape(ln) if ln.strip() else "&nbsp;"}</p>'
                for ln in lines
            )
            return (f'<section style="margin: 16px 0px; padding: 16px 20px; '
                    f'background-color: rgb(248, 249, 250); border-radius: 6px; '
                    f'border: 1px solid {self.COLOR_BORDER};">{inner}</section>')

        # 有语言标注的代码块 - 语法高亮
        highlighted = self._highlight_code(code, lang)
        # 在 white-space: pre 的元素内，保留 \n 换行符，只转换空格
        highlighted = highlighted.replace('  ', '\u00A0\u00A0')  # 使用不间断空格

        lang_label = (f'<span style="position: absolute; top: 8px; right: 12px; font-size: 11px; '
                      f'color: rgb(130, 140, 150); font-family: {mono_family}; '
                      f'text-transform: uppercase; letter-spacing: 0.5px;">{html_module.escape(lang)}</span>')

        pre_style = (f'margin: 0px; padding: 0px; font-family: {mono_family}; font-size: 13px; '
                     f'line-height: 1.7; white-space: pre; word-break: normal; overflow-wrap: normal;')

        return (f'<section style="position: relative; margin: 16px 0px; padding: 16px 20px; '
                f'background-color: rgb(246, 248, 250); border-radius: 6px; overflow-x: auto; '
                f'border: 1px solid rgb(210, 215, 220);">'
                f'{lang_label}<p style="{pre_style}">{highlighted}</p></section>')

    def _render_table(self, table_lines: list, styles: Dict[str, str],
                      font_family: str, text_color: str, accent_color: str = None) -> str:
        """
        渲染表格为 HTML

        Args:
            table_lines: Markdown 表格行列表 [表头, 分隔符, 数据行...]
            accent_color: 强调色，用于表头背景
        """
        if len(table_lines) < 2:
            return ''

        # 使用传入的强调色或默认蓝色
        header_bg = accent_color if accent_color else "rgb(0, 128, 255)"

        # 解析表头
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]

        # 解析数据行（跳过分隔符）
        data_rows = []
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                data_rows.append(cells)

        if not headers:
            return ''

        # 构建 HTML 表格
        html_parts = ['<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">']

        # 表头
        html_parts.append('  <thead>')
        html_parts.append(f'    <tr style="background-color: {header_bg};">')
        for header in headers:
            html_parts.append(
                f'      <th style="padding: 12px 16px; text-align: left; color: white; '
                f'font-weight: bold; border: 1px solid rgb(230, 230, 230); '
                f'font-family: {font_family};">{html_module.escape(header)}</th>'
            )
        html_parts.append('    </tr>')
        html_parts.append('  </thead>')

        # 数据行
        if data_rows:
            html_parts.append('  <tbody>')
            for row_idx, row in enumerate(data_rows):
                bg_color = 'rgb(250, 250, 250)' if row_idx % 2 == 0 else 'white'
                html_parts.append(f'    <tr style="background-color: {bg_color};">')
                for cell in row:
                    html_parts.append(
                        f'      <td style="padding: 10px 16px; border: 1px solid rgb(230, 230, 230); '
                        f'color: {text_color}; font-family: {font_family};">'
                        f'{html_module.escape(cell)}</td>'
                    )
                html_parts.append('    </tr>')
            html_parts.append('  </tbody>')

        html_parts.append('</table>')
        return '\n'.join(html_parts)

    def _render_columns(self, col_lines: list, styles: Dict[str, str],
                        font_family: str, text_color: str, use_flex: bool = True) -> str:
        """
        渲染分栏为 HTML

        Args:
            col_lines: 分栏内容行列表
            use_flex: 是否使用 flex 布局（true）或表格布局（false）
        """
        if not col_lines:
            return ''

        # 解析 Markdown 表格格式
        first_line = col_lines[0].strip()
        if '|' not in first_line:
            return ''

        columns = [cell.strip() for cell in first_line.split('|') if cell.strip()]
        if len(columns) < 2:
            return ''

        num_cols = len(columns)

        # 使用 flex 布局（类似样本 HTML 的并排图片）
        if use_flex:
            html_parts = ['<div style="display: flex; justify-content: space-between; margin: 15px 0; gap: 10px;">']

            for idx, col_content in enumerate(columns):
                # 支持图片+文字的组合格式
                content = col_content.strip()
                is_last = (idx == num_cols - 1)
                margin_right = '' if is_last else 'margin-right: 8px;'

                # 检查内容是否包含图片标记 ![alt](url)
                img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)(.*)$', content)
                if img_match:
                    alt_text, img_src, caption = img_match.groups()
                    inner_html = f'<img src="{html_module.escape(img_src)}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;">'
                    if caption.strip():
                        inner_html += f'<p style="margin: 8px 0 0 0; padding: 0; color: {text_color}; font-family: {font_family}; font-size: 14px; line-height: 1.6; text-align: center;">{html_module.escape(caption.strip())}</p>'
                else:
                    # 纯文本内容
                    inner_html = f'<p style="margin: 0; padding: 0; color: {text_color}; font-family: {font_family}; font-size: 15px; line-height: 2.0; text-align: center;">{html_module.escape(content)}</p>'

                html_parts.append(
                    f'<div style="flex: 1; text-align: center; {margin_right}">'
                    f'{inner_html}'
                    f'</div>'
                )

            html_parts.append('</div>')
        else:
            # 传统表格布局（带分隔线）
            html_parts = ['<div style="display: flex; gap: 16px; margin: 16px 0;">']

            for idx, col_content in enumerate(columns):
                is_last = (idx == num_cols - 1)
                border_style = '' if is_last else 'border-right: 1px solid rgb(230, 230, 230); padding-right: 16px;'

                html_parts.append(
                    f'<div style="flex: 1; {border_style}">'
                    f'<p style="margin: 0; padding: 0; color: {text_color}; '
                    f'font-family: {font_family}; font-size: 15px; line-height: 1.8;">'
                    f'{html_module.escape(col_content)}</p>'
                    f'</div>'
                )

            html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _highlight_code(self, code: str, lang: str) -> str:
        """代码语法高亮"""
        lang = lang.lower().strip()
        rules = self.LANG_RULES.get(lang)

        if not rules:
            return html_module.escape(code)

        length = len(code)
        colors = [None] * length

        for pattern, color_key in rules:
            for m in re.finditer(pattern, code, re.MULTILINE):
                start, end = m.start(), m.end()
                if all(colors[j] is None for j in range(start, end)):
                    for j in range(start, end):
                        colors[j] = color_key

        result = []
        i = 0
        while i < length:
            color_key = colors[i]
            j = i + 1
            while j < length and colors[j] == color_key:
                j += 1
            segment = html_module.escape(code[i:j])
            color = self.CODE_COLORS.get(color_key, self.CODE_COLORS["default"])
            result.append(f'<span style="color: {color};">{segment}</span>')
            i = j

        return ''.join(result)

    def _process_inline(self, text: str, font_family: str, primary_color: str, accent_color: str) -> str:
        """处理行内元素，同时保留 WPS 颜色映射已生成的 HTML span"""
        placeholders = {}
        placeholder_idx = [0]

        def protect(html_frag: str) -> str:
            key = f'\x00PROTECT{placeholder_idx[0]}\x00'
            placeholder_idx[0] += 1
            placeholders[key] = html_frag
            return key

        # 保护 WPS 颜色已转换的 <span style="...">...</span>（来自 _convert_inline_styles）
        text = re.sub(
            r'<span style="[^"]*">[^<]*</span>',
            lambda m: protect(m.group(0)),
            text
        )

        # 行内代码
        def replace_inline_code(m):
            code = html_module.escape(m.group(1))
            style = (f'background-color: rgb(235, 236, 240); color: rgb(80, 90, 105); '
                     f'font-family: {self.MONO_FAMILY}; font-size: 13px; padding: 1px 5px; '
                     f'border-radius: 3px; white-space: nowrap;')
            return f'<code style="{style}">{code}</code>'

        def protect_inline_code(m):
            key = f'\x00CODE{placeholder_idx[0]}\x00'
            placeholder_idx[0] += 1
            placeholders[key] = replace_inline_code(m)
            return key

        text = re.sub(r'`([^`]+)`', protect_inline_code, text)

        # 加粗 **...**
        text = re.sub(
            r'\*\*(.+?)\*\*',
            lambda m: f'<span style="font-size: 16px; font-weight: bold; color: {primary_color}; font-family: {font_family};">{m.group(1)}</span>',
            text
        )

        # 恢复行内代码
        for key, val in placeholders.items():
            text = text.replace(key, val)

        # 链接 [文字](url)
        text = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            lambda m: f'<a href="{m.group(2)}" style="color: {accent_color}; text-decoration: none;">{m.group(1)}</a>',
            text
        )

        return text

    def _load_html_template(self) -> str:
        """加载 HTML 模板"""
        template_path = self.template_dir / "template.html"

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 默认模板
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>公众号文章</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #f5f5f5;">

<section id="mp-section" style="max-width: 677px; margin: 0 auto; background-color: #fff; padding: 20px; font-family: mp-quote, 'PingFang SC', -apple-system-font, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif;">

{{ content }}

</section>

<div id="copy-bar" style="position: fixed; bottom: 24px; right: 24px; z-index: 9999;">
  <button id="copy-btn" onclick="copyContent()" style="
    background: rgb(0, 128, 255);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-family: 'PingFang SC', sans-serif;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,128,255,0.35);
    transition: all 0.2s;
  ">复制内容</button>
</div>
<script>
function copyContent() {
  const section = document.getElementById('mp-section');
  const btn = document.getElementById('copy-btn');
  const range = document.createRange();
  range.selectNode(section);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try {
    document.execCommand('copy');
    btn.textContent = '✓ 已复制';
    btn.style.background = 'rgb(7, 134, 84)';
    setTimeout(() => {
      btn.textContent = '复制内容';
      btn.style.background = 'rgb(0, 128, 255)';
    }, 2000);
  } catch(e) {
    btn.textContent = '复制失败，请手动选择';
    btn.style.background = 'rgb(194, 28, 19)';
  }
  sel.removeAllRanges();
}
</script>

</body>
</html>'''

    def xml_to_html(self, xml_content: str, template: Optional[Dict[str, Any]] = None) -> str:
        """
        将 WPS 笔记 XML 直接转换为带内联样式的 HTML 片段。
        跳过 Markdown 中间层，保留颜色、样式等富文本信息。
        """
        if template is None:
            template = self._get_default_template()

        colors = template.get("colors", {})
        fonts = template.get("fonts", {})
        spacing = template.get("spacing", {})
        features = template.get("features", {})

        primary_color = colors.get("primary", self.COLOR_ORANGE)
        accent_color  = colors.get("accent",  self.COLOR_BLUE)
        text_color    = colors.get("text",     self.COLOR_GRAY)
        bg_block_color = colors.get("bg_block", self.COLOR_BG_GRAY)

        font_family = fonts.get("family", {}).get("body", self.FONT_FAMILY)
        mono_family = fonts.get("family", {}).get("mono", self.MONO_FAMILY)
        body_size   = fonts.get("size", {}).get("body", 16)
        h2_size     = fonts.get("size", {}).get("h2",   18)
        h3_size     = fonts.get("size", {}).get("h3",   16)
        line_height = spacing.get("line_height_body", 2.0)
        para_gap    = spacing.get("paragraph_gap",    15)

        # --- 行内元素渲染 ---
        def render_inline(text: str) -> str:
            """处理 WPS XML 行内标记 → HTML"""
            # 保护已生成 HTML（如颜色 span）防止被 escape
            protected: Dict[str, str] = {}
            idx = [0]

            def protect(frag: str) -> str:
                k = f"\x00P{idx[0]}\x00"
                idx[0] += 1
                protected[k] = frag
                return k

            # WPS fontColor / fontHighlightColor / fontSize
            def convert_wps_span(m: re.Match) -> str:
                attrs, inner = m.group(1), render_inline_raw(m.group(2))
                parts = []
                fc = re.search(r'fontColor="([^"]+)"', attrs)
                if fc:
                    rgb = self.WPS_FONT_COLORS.get(fc.group(1).upper())
                    if rgb:
                        parts.append(f"color: {rgb};")
                fh = re.search(r'fontHighlightColor="([^"]+)"', attrs)
                if fh:
                    rgb = self.WPS_HIGHLIGHT_COLORS.get(fh.group(1).upper())
                    if rgb:
                        parts.append(f"background-color: {rgb}; padding: 0 2px; border-radius: 2px;")
                fs = re.search(r'fontSize="([^"]+)"', attrs)
                if fs:
                    parts.append(f"font-size: {fs.group(1)}px;")
                if parts:
                    return protect(f'<span style="{" ".join(parts)}">{inner}</span>')
                return inner

            def render_inline_raw(t: str) -> str:
                # 递归处理 WPS span（嵌套颜色）
                t = re.sub(
                    r'<span\s([^>]*(?:fontColor|fontHighlightColor|fontSize)[^>]*)>(.*?)</span>',
                    convert_wps_span, t, flags=re.DOTALL
                )
                # <strong> → 橙色加粗
                t = re.sub(
                    r'<strong>(.*?)</strong>',
                    lambda m: protect(f'<span style="font-weight: bold; color: {primary_color};">{m.group(1)}</span>'),
                    t
                )
                # <em>
                t = re.sub(r'<em>(.*?)</em>', r'<em>\1</em>', t)
                # <s> / <u>
                t = re.sub(r'<s>(.*?)</s>', r'<s>\1</s>', t)
                t = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', t)
                # <a>
                t = re.sub(
                    r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    lambda m: protect(
                        f'<a href="{m.group(1)}" style="color: {accent_color}; text-decoration: none;">{m.group(2)}</a>'
                    ),
                    t
                )
                # <emoji value="..."/>
                t = re.sub(r'<emoji[^/]*/>', lambda m: re.search(r'value="([^"]+)"', m.group(0)).group(1) if re.search(r'value="([^"]+)"', m.group(0)) else '', t)
                # <br/>
                t = t.replace('<br/>', '<br>')
                # 清理其他剩余标签
                t = re.sub(r'<[^>]+>', '', t)
                return t

            result = render_inline_raw(text)
            # 还原保护片段
            for k, v in protected.items():
                result = result.replace(k, v)
            return result

        # --- 块级渲染函数 ---
        S_P   = f'style="margin: 0px 0px {para_gap}px 0px; padding: 0px; outline: 0px; max-width: 100%; clear: both; min-height: 20px; word-break: break-all; color: {text_color}; font-size: {body_size}px; line-height: {line_height};"'
        S_SPAN = f'style="font-size: {body_size}px; color: {text_color}; font-family: {font_family}; white-space: pre-wrap;"'
        S_HB  = f'style="font-size: {body_size}px; font-weight: bold; color: {primary_color}; font-family: {font_family}; white-space: pre-wrap;"'
        S_H2  = f'style="margin: 30px 0px 15px 0px; padding: 0px; font-size: {h2_size}px; font-weight: bold; color: {accent_color}; line-height: 1.6;"'
        S_H3  = f'style="margin: 20px 0px 10px 0px; padding: 0px; font-size: {h3_size}px; font-weight: bold; color: {accent_color}; line-height: 1.6;"'
        S_BQ  = f'style="margin: 20px 0px; padding: 15px 20px; background-color: {bg_block_color}; border-left: 4px solid {accent_color}; font-size: 15px; color: {text_color}; line-height: 1.8;"'
        S_BQ_P = f'style="margin: 0px; padding: 0px; font-family: {font_family};"'
        S_HR  = f'style="margin: 25px 0px; border: none; border-top: 1px solid {self.COLOR_BORDER};"'
        S_NOTE = f'style="margin: 20px 0px 0px 0px; padding: 0px; font-size: 14px; color: {self.COLOR_LGRAY}; line-height: 1.8;"'
        S_BULLET = f'style="color: {primary_color}; margin-right: 6px;"'
        S_NUM    = f'style="color: {primary_color}; font-weight: bold; margin-right: 6px;"'

        def render_p(inner_xml: str) -> str:
            inner = render_inline(inner_xml)
            return f'<p {S_P}><span {S_SPAN}>{inner}</span></p>'

        def render_hb(inner_xml: str) -> str:
            inner = html_module.escape(re.sub(r'<[^>]+>', '', inner_xml))
            return f'<p {S_P}><span {S_HB}>{inner}</span></p>'

        def render_heading(level: int, inner_xml: str) -> str:
            text = html_module.escape(re.sub(r'<[^>]+>', '', inner_xml).strip())
            if level <= 2:
                return f'<h2 {S_H2}>{text}</h2>'
            return f'<p {S_P}><span {S_H3}>{text}</span></p>'

        def render_blockquote(inner_xml: str) -> str:
            text = render_inline(inner_xml)
            return f'<blockquote {S_BQ}>\n    <p {S_BQ_P}>{text}</p>\n</blockquote>'

        def render_codeblock(code: str, lang: str) -> str:
            if not lang:
                lines = code.strip().split('\n')
                inner = '\n'.join(
                    f'<p style="margin: 0 0 4px 0; padding: 0; font-size: 15px; color: {text_color}; font-family: {font_family}; line-height: 1.8;">'
                    f'{html_module.escape(ln) if ln.strip() else "&nbsp;"}</p>'
                    for ln in lines
                )
                return (f'<section style="margin: 16px 0px; padding: 16px 20px; '
                        f'background-color: rgb(248, 249, 250); border-radius: 6px; '
                        f'border: 1px solid {self.COLOR_BORDER};">{inner}</section>')
            highlighted = self._highlight_code(code, lang).replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            lang_label = (f'<span style="position: absolute; top: 8px; right: 12px; font-size: 11px; '
                          f'color: rgb(130, 140, 150); font-family: {mono_family}; '
                          f'text-transform: uppercase; letter-spacing: 0.5px;">{html_module.escape(lang)}</span>')
            pre_style = (f'margin: 0px; padding: 0px; font-family: {mono_family}; font-size: 13px; '
                         f'line-height: 1.7; white-space: pre; word-break: normal; overflow-wrap: normal;')
            return (f'<section style="position: relative; margin: 16px 0px; padding: 16px 20px; '
                    f'background-color: rgb(246, 248, 250); border-radius: 6px; overflow-x: auto; '
                    f'border: 1px solid rgb(210, 215, 220);">'
                    f'{lang_label}<p style="{pre_style}">{highlighted}</p></section>')

        def render_list_item(text: str, ordered: bool, num: int = 0) -> str:
            inner = render_inline(text)
            if ordered:
                marker = f'<span {S_NUM}>{num}.</span>'
            else:
                marker = f'<span {S_BULLET}>•</span>'
            return f'<p {S_P}><span {S_SPAN}>{marker}{inner}</span></p>'

        def render_table(table_xml: str) -> str:
            s_table = f'style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 15px;"'
            s_th = f'style="padding: 10px 14px; background-color: {accent_color}; color: #fff; font-weight: bold; text-align: center; border: 1px solid rgb(0, 100, 220);"'
            s_td = f'style="padding: 10px 14px; color: {text_color}; border: 1px solid rgb(210, 215, 220); vertical-align: top; line-height: 1.7;"'
            s_td_alt = f'style="padding: 10px 14px; color: {text_color}; border: 1px solid rgb(210, 215, 220); vertical-align: top; line-height: 1.7; background-color: rgb(248, 249, 250);"'
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_xml, re.DOTALL)
            html = f'<table {s_table}>\n'
            for i, row in enumerate(rows):
                cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
                html += '  <tr>\n'
                for cell in cells:
                    cell_text = render_inline(re.sub(r'<p[^>]*>(.*?)</p>', r'\1', cell, flags=re.DOTALL))
                    if i == 0:
                        html += f'    <th {s_th}>{cell_text}</th>\n'
                    else:
                        td_s = s_td_alt if i % 2 == 0 else s_td
                        html += f'    <td {td_s}>{cell_text}</td>\n'
                html += '  </tr>\n'
            return html + '</table>'

        def render_highlight_block(hb_xml: str) -> str:
            emoji_m = re.search(r'<emoji[^/]*value="([^"]+)"', hb_xml)
            emoji = emoji_m.group(1) if emoji_m else '💡'
            text = render_inline(re.sub(r'<[^>]+>', ' ', hb_xml).strip())
            bg_attr = re.search(r'highlightBlockBackgroundColor="([^"]+)"', hb_xml)
            bd_attr = re.search(r'highlightBlockBorderColor="([^"]+)"', hb_xml)
            bg = bg_attr.group(1) if bg_attr else '#FAF1E6'
            bd = bd_attr.group(1) if bd_attr else '#FEC794'
            return (f'<blockquote style="margin: 20px 0; padding: 15px 20px; '
                    f'background-color: {bg}; border-left: 4px solid {bd}; '
                    f'font-size: 15px; color: {text_color}; line-height: 1.8;">'
                    f'<p style="margin: 0; padding: 0; font-family: {font_family};">'
                    f'{emoji}&nbsp;{text}</p></blockquote>')

        def render_columns(cols_xml: str) -> str:
            cols = re.findall(r'<column[^>]*>(.*?)</column>', cols_xml, re.DOTALL)
            if not cols:
                return ''
            parts = ['<div style="display: flex; justify-content: space-between; margin: 15px 0; gap: 10px;">']
            for i, col in enumerate(cols):
                inner = render_inline(re.sub(r'<[^>]+>', ' ', col).strip())
                is_last = (i == len(cols) - 1)
                mr = '' if is_last else 'margin-right: 8px;'
                parts.append(f'<div style="flex: 1; text-align: center; {mr}">'
                              f'<p style="margin: 0; padding: 0; color: {text_color}; font-family: {font_family}; font-size: 15px; line-height: 2.0; text-align: center;">{inner}</p>'
                              f'</div>')
            parts.append('</div>')
            return '\n'.join(parts)

        # --- 主解析循环：逐块处理 WPS XML ---
        # 先处理占位符标签（在正式解析之前转换为标准 WPS 标签）
        xml = self._process_placeholder_tags(xml_content)

        result = []

        # 按块级标签逐一提取并渲染
        # 使用迭代式扫描处理顶层块
        pos = 0
        BLOCK_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                      'p', 'blockquote', 'codeblock', 'table',
                      'highlightBlock', 'columns', 'hr', 'img',
                      'NoteAudioCard', 'embed']

        # 构建顶层块匹配模式
        block_pat = re.compile(
            r'<(h[1-6]|p|blockquote|codeblock|table|highlightBlock|columns|hr/|img/|NoteAudioCard/|embed[^>]*/?)([^>]*)>(.*?)</\1>|<(hr|img|NoteAudioCard|embed)[^>]*/?>',
            re.DOTALL
        )

        # list 状态
        ordered_counter = [0]

        for m in block_pat.finditer(xml):
            tag  = (m.group(1) or m.group(4) or '').strip('/')
            attrs = m.group(2) or ''
            inner = m.group(3) or ''
            # 自闭合标签（hr/img/NoteAudioCard/embed）走右侧分支，
            # attrs/inner 为空，需从完整匹配串里提取属性
            full_match = m.group(0) if (not attrs and not inner) else None

            if tag in ('h1', 'h2'):
                result.append(render_heading(2, inner))
            elif tag in ('h3', 'h4', 'h5', 'h6'):
                result.append(render_heading(3, inner))
            elif tag == 'p':
                # 检查 listType
                lt = re.search(r'listType="([^"]+)"', attrs)
                if lt:
                    ltype = lt.group(1)
                    if ltype == 'ordered':
                        ordered_counter[0] += 1
                        result.append(render_list_item(inner, True, ordered_counter[0]))
                    else:
                        ordered_counter[0] = 0
                        result.append(render_list_item(inner, False))
                else:
                    ordered_counter[0] = 0
                    # 检查 hb 占位符（已被 _process_placeholder_tags 转换为 !!...!! 包裹的段落）
                    stripped = re.sub(r'<[^>]+>', '', inner).strip()
                    if stripped.startswith('!!') and stripped.endswith('!!') and len(stripped) > 4:
                        result.append(render_hb(stripped[2:-2]))
                    else:
                        result.append(render_p(inner))
            elif tag == 'blockquote':
                ordered_counter[0] = 0
                result.append(render_blockquote(inner))
            elif tag == 'codeblock':
                ordered_counter[0] = 0
                lang_m = re.search(r'lang="([^"]*)"', attrs)
                lang = lang_m.group(1) if lang_m else ''
                result.append(render_codeblock(inner, lang))
            elif tag == 'table':
                ordered_counter[0] = 0
                result.append(render_table(inner))
            elif tag == 'highlightBlock':
                ordered_counter[0] = 0
                result.append(render_highlight_block(attrs + inner))
            elif tag == 'columns':
                ordered_counter[0] = 0
                result.append(render_columns(inner))
            elif tag == 'hr':
                ordered_counter[0] = 0
                result.append(f'<hr {S_HR}>')
            # img：优先使用 WPS CDN src，可被微信公众号直接引用
            elif tag == 'img':
                ordered_counter[0] = 0
                attr_str = attrs or (full_match or '')
                src_m     = re.search(r'src="([^"]+)"',     attr_str)
                caption_m = re.search(r'caption="([^"]+)"', attr_str)
                if src_m:
                    src = src_m.group(1)
                    caption = caption_m.group(1) if caption_m else ''
                    img_html = (f'<img src="{src}" '
                                f'style="max-width: 100%; height: auto; display: block; margin: 15px auto;">')
                    if caption:
                        cap_style = (f'text-align: center; font-size: 13px; '
                                     f'color: {self.COLOR_LGRAY}; margin: 4px 0 15px 0;')
                        img_html += f'<p style="{cap_style}">{html_module.escape(caption)}</p>'
                    result.append(img_html)

        return '\n\n'.join(r for r in result if r)

    def _export_from_note_data(self, note: dict, template_name: str = "blue-theme",
                               output_path: Optional[str] = None) -> str:
        """
        将已读取的笔记数据直接转换并保存为 HTML。
        路径：WPS XML → HTML（无 Markdown 中间层）。
        """
        title = note.get("title", "untitled")

        print(f"🎨 加载模板: {template_name}")
        template = self.load_template(template_name)

        print("🌐 WPS XML → HTML（直接转换）...")
        content_html = self.xml_to_html(note.get("content", ""), template)

        # 载入 HTML 模板壳
        html_template = self._load_html_template()
        html_content = html_template.replace("{{ title }}", html_module.escape(title))
        html_content = html_content.replace("{{ content }}", content_html)

        # 保存文件
        if output_path is None:
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_') or "untitled"
            output_path = f"{safe_title}_formatted.html"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 导出完成: {output_path}")
        print(f"   标题: {title}")
        print(f"   内容块数: {content_html.count('<p ') + content_html.count('<h2') + content_html.count('<blockquote')}")

        return str(output_path)

    def export(self, note_id: str, template_name: str = "blue-theme",
               output_path: Optional[str] = None) -> str:
        """
        完整导出流程：读取笔记并转换为 HTML。

        读取优先级：
          1. wpsnote-cli（CLI 可用时自动使用）
          2. 降级：由 AI Agent 通过 MCP 读取后传入 --xml-file

        Args:
            note_id: 笔记 ID
            template_name: 模板名称
            output_path: 输出路径（可选）

        Returns:
            生成的 HTML 文件路径
        """
        print(f"🚀 开始导出笔记: {note_id}")

        note = self.read_note(note_id)
        if not note.get("content"):
            raise ValueError(
                f"笔记内容为空（note_id={note_id}）。\n"
                "如果 wpsnote-cli 不可用，请由 AI Agent 通过 MCP read_note 读取内容后，\n"
                "将内容保存为 XML 文件，再用 --xml-file 参数传入。"
            )

        return self._export_from_note_data(note, template_name, output_path)


def search_notes(keyword: str) -> Optional[str]:
    """
    搜索笔记，返回第一个匹配的 note_id。
    优先使用 CLI，不可用时返回 None（由 AI Agent 通过 MCP 处理）。
    """
    print(f"🔍 搜索笔记: {keyword}")

    if _cli_available():
        note_id = cli_find_note(keyword)
        if note_id:
            print(f"   → CLI 找到笔记: {note_id}")
            return note_id
        print("   ⚠️  CLI 未找到匹配笔记，请使用 MCP 搜索后通过 --note-id 指定")
    else:
        print("   → wpsnote-cli 不可用，请由 AI Agent 通过 MCP search_notes 搜索后传入 --note-id")
    return None


def main():
    parser = argparse.ArgumentParser(description='将 WPS 笔记导出为公众号 HTML 格式')
    parser.add_argument('--note-id', '-n', help='笔记 ID')
    parser.add_argument('--search', '-s', help='搜索关键词（自动选择第一个结果）')
    parser.add_argument('--current', action='store_true', help='获取当前编辑中的笔记')
    parser.add_argument('--xml-file', help='直接传入笔记 XML 文件路径（MCP 降级时使用）')
    parser.add_argument('--title', help='笔记标题（配合 --xml-file 使用）')
    parser.add_argument('--template', '-t', default='blue-theme', help='模板名称（默认: blue-theme）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--skill-dir', help='Skill 根目录（默认: 脚本所在目录的父目录）')

    args = parser.parse_args()

    # 确定 skill 目录
    skill_dir = Path(args.skill_dir) if args.skill_dir else None

    # 创建导出器
    exporter = WPSNoteExporter(skill_dir)

    # --- 获取笔记 ID ---

    # 方式 1：直接传入 XML 文件（MCP 降级时，AI Agent 将内容写入文件后传入）
    if args.xml_file:
        xml_path = Path(args.xml_file)
        if not xml_path.exists():
            print(f"❌ XML 文件不存在: {xml_path}")
            return 1
        xml_content = xml_path.read_text(encoding="utf-8")
        title = args.title or xml_path.stem
        note_data = {"note_id": "local", "title": title, "content": xml_content, "blocks": []}
        try:
            output_path = exporter._export_from_note_data(note_data, args.template, args.output)
            print(f"\n📄 输出文件: {output_path}")
            return 0
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return 1

    # 方式 2：获取当前编辑中的笔记（仅旧桌面端支持，云端需传 --note-id / --search）
    note_id = args.note_id
    if args.current:
        print("❌ 云端 wpsnote-cli 不支持 --current（无桌面编辑器上下文），请改用 --note-id 或 --search")
        return 1

    # 方式 3：关键词搜索
    if args.search and not note_id:
        note_id = search_notes(args.search)
        if not note_id:
            print("❌ 未找到匹配的笔记，请手动指定 --note-id")
            return 1

    if not note_id:
        print("❌ 请提供 --note-id、--search、--current 或 --xml-file 之一")
        return 1

    # 执行导出
    try:
        output_path = exporter.export(
            note_id=note_id,
            template_name=args.template,
            output_path=args.output
        )
        print(f"\n📄 输出文件: {output_path}")
        return 0
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
