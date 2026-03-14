# -*- coding=utf-8
"""
通用网页内容爬取工具
输入 URL，自动提取正文内容，转换为 Markdown 格式，下载并保存图片。

使用方式：
  python3.11 web_to_md.py "https://example.com/article"
  python3.11 web_to_md.py "https://example.com/article" -o 输出目录名

依赖安装：
  pip3.11 install requests beautifulsoup4 readability-lxml markdownify lxml
"""

import requests
from bs4 import BeautifulSoup
from readability import Document
from markdownify import MarkdownConverter
import os
import re
import sys
import time
import hashlib
import argparse
import datetime
from urllib.parse import urlparse, urljoin, unquote


# ============================================================
# 配置
# ============================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
              'image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

# 默认保存根目录（脚本同级的 "爬取内容" 目录）
DEFAULT_OUTPUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '爬取内容')

# 图片目录名
IMAGES_DIR_NAME = 'images'

# 跳过的图片 URL 关键词（广告、追踪像素等）
SKIP_IMAGE_KEYWORDS = [
    'pixel', 'tracking', 'beacon', 'analytics',
    '1x1', 'spacer', 'blank.gif',
]

# 广告/推广相关的 class/id 关键词
AD_KEYWORDS = [
    'ad', 'advertisement', 'promo', 'promotion', 'sponsor',
    'banner', 'sidebar', 'related-posts', 'recommended',
    'newsletter', 'subscribe', 'cta', 'call-to-action',
    'download-app', 'app-store', 'play-store',
]

# 过滤级别
FILTER_LEVEL_MINIMAL = 0    # 最小过滤：只过滤导航、页脚等
FILTER_LEVEL_MODERATE = 1   # 中等过滤：过滤广告但保留文末推荐
FILTER_LEVEL_AGGRESSIVE = 2 # 激进过滤：只保留纯正文内容


# ============================================================
# 工具函数
# ============================================================

def sanitize_filename(name, max_length=80):
    """清理文件/文件夹名，移除非法字符"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name or 'untitled'


def get_domain(url):
    """提取域名用于日志显示"""
    parsed = urlparse(url)
    return parsed.netloc


def guess_image_ext(content_type, url):
    """根据 Content-Type 和 URL 猜测图片扩展名"""
    ct_map = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/svg+xml': '.svg',
        'image/bmp': '.bmp',
        'image/x-icon': '.ico',
        'image/avif': '.avif',
    }
    if content_type:
        ct = content_type.lower().split(';')[0].strip()
        if ct in ct_map:
            return ct_map[ct]

    # 从 URL 路径猜测
    path = urlparse(url).path.lower()
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.avif']:
        if ext in path:
            return '.jpg' if ext == '.jpeg' else ext
    return '.jpg'  # 默认


def is_valid_image_url(url):
    """判断图片 URL 是否值得下载"""
    if not url:
        return False
    url_lower = url.lower()
    for kw in SKIP_IMAGE_KEYWORDS:
        if kw in url_lower:
            return False
    # 跳过 data URI（已内联的 base64 图片）
    if url.startswith('data:'):
        return False
    return True


def make_absolute_url(base_url, src):
    """将相对 URL 转为绝对 URL"""
    if not src:
        return None
    if src.startswith('data:'):
        return None
    if src.startswith('//'):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}:{src}"
    return urljoin(base_url, src)


# ============================================================
# 自定义 Markdown 转换器
# ============================================================

class CustomMarkdownConverter(MarkdownConverter):
    """自定义 Markdown 转换器，优化图片处理和格式"""

    def __init__(self, image_mapping=None, **kwargs):
        super().__init__(**kwargs)
        self.image_mapping = image_mapping or {}

    def convert_img(self, el, text, convert_as_inline):
        """自定义图片转换：使用本地路径"""
        src = el.get('data-src') or el.get('src') or ''
        alt = el.get('alt') or '图片'

        # 如果有映射到本地路径，使用本地路径
        if src in self.image_mapping:
            local_path = self.image_mapping[src]
            return f'\n\n![{alt}]({local_path})\n\n'

        # 保留原始 URL
        if src and not src.startswith('data:'):
            return f'\n\n![{alt}]({src})\n\n'

        return ''

    def convert_figure(self, el, text, convert_as_inline):
        """处理 figure 标签"""
        return f'\n\n{text}\n\n'

    def convert_figcaption(self, el, text, convert_as_inline):
        """处理 figcaption 标签"""
        if text.strip():
            return f'\n*{text.strip()}*\n'
        return ''


# ============================================================
# 核心功能
# ============================================================

def fetch_page(url, max_retries=3):
    """获取网页内容，支持重试"""
    for retry in range(max_retries):
        try:
            print(f"   [请求] 正在获取页面... (第 {retry + 1} 次)")
            response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)

            if response.status_code != 200:
                print(f"   [警告] HTTP 状态码: {response.status_code}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue
                return None

            # 自动检测编码
            response.encoding = response.apparent_encoding or 'utf-8'
            print(f"   [成功] 页面获取成功 (编码: {response.encoding}, "
                  f"大小: {len(response.content) / 1024:.1f} KB)")
            return response

        except requests.exceptions.Timeout:
            print(f"   [警告] 请求超时")
            if retry < max_retries - 1:
                time.sleep(2)
        except requests.exceptions.ConnectionError as e:
            print(f"   [警告] 连接失败: {e}")
            if retry < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"   [错误] 请求异常: {e}")
            if retry < max_retries - 1:
                time.sleep(2)

    print(f"   [失败] 页面获取失败，已重试 {max_retries} 次")
    return None


def clean_content(soup, filter_level=FILTER_LEVEL_AGGRESSIVE):
    """
    清理内容，移除广告和推广元素
    
    Args:
        soup: BeautifulSoup 对象
        filter_level: 过滤级别
            0 - 最小过滤（只过滤导航、页脚）
            1 - 中等过滤（过滤广告但保留文末推荐）
            2 - 激进过滤（只保留纯正文）
    """
    if filter_level == FILTER_LEVEL_MINIMAL:
        # 只移除明显的非内容元素
        for tag in soup.find_all(['nav', 'footer', 'header', 'aside']):
            tag.decompose()
        return soup
    
    # 中等和激进过滤都要移除这些
    # 1. 移除导航、页脚等
    for tag in soup.find_all(['nav', 'footer', 'header', 'aside', 'form', 'button']):
        tag.decompose()
    
    # 2. 移除包含广告关键词的元素（先收集再删除，避免迭代器失效）
    tags_to_remove = []
    for tag in soup.find_all(True):
        if not tag:  # 跳过已删除的元素
            continue
            
        classes = tag.get('class', []) if hasattr(tag, 'get') else []
        tag_id = tag.get('id', '') if hasattr(tag, 'get') else ''
        
        # 组合 class 和 id 进行检查
        combined = ' '.join(classes) + ' ' + tag_id
        combined_lower = combined.lower()
        
        # 检查是否包含广告关键词
        if any(keyword in combined_lower for keyword in AD_KEYWORDS):
            tags_to_remove.append(tag)
    
    # 统一删除
    for tag in tags_to_remove:
        if tag and tag.parent:  # 确保元素还存在
            tag.decompose()
    
    if filter_level == FILTER_LEVEL_AGGRESSIVE:
        # 激进过滤：移除所有链接包含推广的元素
        links_to_remove = []
        for link in soup.find_all('a'):
            if not link:
                continue
                
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            # 检查是否是推广链接
            if any(keyword in href or keyword in text for keyword in 
                   ['utm_', 'download', 'apps.apple.com', 'play.google', 'subscribe', 
                    'try ', 'get started', 'sign up', 'buy now', 'app-store', 'play-store']):
                # 移除整个链接的父容器（通常是一个 div 或 p）
                parent = link.parent
                if parent and parent.name in ['div', 'p', 'section']:
                    links_to_remove.append(parent)
                else:
                    links_to_remove.append(link)
        
        # 统一删除
        for element in links_to_remove:
            if element and element.parent:
                element.decompose()
    
    return soup


def extract_content(html, url, filter_level=FILTER_LEVEL_AGGRESSIVE):
    """使用 readability 提取正文内容"""
    print(f"   [解析] 正在提取正文...")

    doc = Document(html)
    title = doc.title() or '未命名'
    content_html = doc.summary()

    # 清理标题
    title = title.strip()
    # 有些网站标题带有 " - 网站名" 后缀，可选择保留或去除
    # 这里保留完整标题

    print(f"   [标题] {title}")

    # readability 有时会过滤掉图片，尝试从原始 HTML 补充
    # 检查提取的内容中图片数量
    content_soup = BeautifulSoup(content_html, 'html.parser')
    extracted_images = content_soup.find_all('img')
    
    if len(extracted_images) < 3:  # 如果图片太少，尝试补充
        original_soup = BeautifulSoup(html, 'html.parser')
        # 查找文章主体区域的常见 class/id
        main_content = (
            original_soup.find('article') or
            original_soup.find('div', class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in 
                ['content', 'article', 'post', 'entry', 'main']
            )) or
            original_soup.find('main')
        )
        
        if main_content:
            # 从主体区域提取图片并补充到 readability 结果中
            main_images = main_content.find_all('img')
            if len(main_images) > len(extracted_images):
                print(f"   [补充] readability 提取了 {len(extracted_images)} 张图片，"
                      f"从原始 HTML 发现 {len(main_images)} 张，正在补充...")
                # 使用原始主体内容替代
                content_html = str(main_content)
                content_soup = BeautifulSoup(content_html, 'html.parser')
    
    # 清理内容（移除广告等）
    filter_names = {0: '最小', 1: '中等', 2: '激进'}
    print(f"   [过滤] 使用 {filter_names.get(filter_level, '未知')} 过滤级别")
    content_soup = clean_content(content_soup, filter_level)
    content_html = str(content_soup)

    return title, content_html


def extract_metadata(soup, url):
    """从 HTML 提取元数据"""
    meta = {
        'url': url,
        'domain': get_domain(url),
        'author': '',
        'publish_time': '',
        'description': '',
    }

    # 提取作者
    author_meta = (
        soup.find('meta', {'name': 'author'}) or
        soup.find('meta', {'property': 'article:author'}) or
        soup.find('meta', {'name': 'twitter:creator'})
    )
    if author_meta:
        meta['author'] = author_meta.get('content', '').strip()

    # 提取发布时间
    time_meta = (
        soup.find('meta', {'property': 'article:published_time'}) or
        soup.find('meta', {'name': 'publish_date'}) or
        soup.find('meta', {'name': 'date'}) or
        soup.find('time')
    )
    if time_meta:
        if time_meta.name == 'time':
            meta['publish_time'] = time_meta.get('datetime', '') or time_meta.text.strip()
        else:
            meta['publish_time'] = time_meta.get('content', '').strip()

    # 提取描述
    desc_meta = (
        soup.find('meta', {'name': 'description'}) or
        soup.find('meta', {'property': 'og:description'})
    )
    if desc_meta:
        meta['description'] = desc_meta.get('content', '').strip()

    return meta


def download_image(img_url, save_path, referer=None, max_retries=3):
    """下载单张图片"""
    img_headers = HEADERS.copy()
    if referer:
        img_headers['Referer'] = referer

    for retry in range(max_retries):
        try:
            resp = requests.get(img_url, headers=img_headers, timeout=30, stream=True)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                # 检查是否真的是图片（放宽判断：Content-Type 为空也允许）
                if content_type and not content_type.startswith('image/') and 'octet-stream' not in content_type:
                    print(f"      [跳过] 非图片类型: {content_type}")
                    return None, None

                ext = guess_image_ext(content_type, img_url)
                # 如果 save_path 没有正确扩展名，更新
                base, old_ext = os.path.splitext(save_path)
                if old_ext != ext:
                    save_path = base + ext

                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                size_kb = os.path.getsize(save_path) / 1024
                # 跳过太小的图片（可能是追踪像素）
                if size_kb < 0.5:
                    os.remove(save_path)
                    return None, None

                return save_path, ext
            else:
                if retry < max_retries - 1:
                    time.sleep(1)
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
            else:
                print(f"      [失败] 图片下载异常: {e}")
    return None, None


def process_images(content_html, base_url, images_dir):
    """处理正文中的所有图片：下载到本地并建立映射"""
    soup = BeautifulSoup(content_html, 'html.parser')
    images = soup.find_all('img')

    if not images:
        print(f"   [图片] 未发现图片")
        return {}, content_html

    print(f"   [图片] 发现 {len(images)} 个图片标签")
    os.makedirs(images_dir, exist_ok=True)

    image_mapping = {}  # 原始URL -> 本地相对路径
    img_counter = 0
    downloaded = 0
    skipped = 0

    for img in images:
        # 获取图片 URL（优先 data-src，常见于懒加载）
        img_url = img.get('data-src') or img.get('src')
        if not img_url:
            continue

        abs_url = make_absolute_url(base_url, img_url)
        if not abs_url or not is_valid_image_url(abs_url):
            skipped += 1
            continue

        # 去重
        if abs_url in image_mapping:
            continue

        img_counter += 1
        img_filename = f"img_{img_counter:03d}.jpg"  # 扩展名会在下载时修正
        img_path = os.path.join(images_dir, img_filename)

        print(f"      [{img_counter}] 下载: {abs_url[:80]}...")
        saved_path, ext = download_image(abs_url, img_path, referer=base_url)

        if saved_path:
            # 获取实际保存的文件名（扩展名可能变了）
            actual_filename = os.path.basename(saved_path)
            local_rel_path = f"./{IMAGES_DIR_NAME}/{actual_filename}"
            image_mapping[abs_url] = local_rel_path
            # 同时映射原始 src（可能是相对路径）
            image_mapping[img_url] = local_rel_path
            downloaded += 1
        else:
            skipped += 1

        # 图片间的小延迟，避免被封
        time.sleep(0.5)

    print(f"   [图片] 完成: 下载 {downloaded} 张, 跳过 {skipped} 张")
    return image_mapping, content_html


def html_to_markdown(content_html, image_mapping=None):
    """将 HTML 正文转换为 Markdown"""
    converter = CustomMarkdownConverter(
        image_mapping=image_mapping,
        heading_style='ATX',
        bullets='-',
        strong_em_symbol='*',
        strip=['script', 'style', 'nav', 'footer', 'header',
               'aside', 'form', 'button', 'input'],
        newline_style='backslash',
    )

    md = converter.convert(content_html)

    # 清理格式
    # 移除过多的连续空行
    md = re.sub(r'\n{4,}', '\n\n\n', md)
    # 移除行首行尾的多余空格
    lines = md.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    md = '\n'.join(cleaned_lines)
    # 移除开头的空行
    md = md.lstrip('\n')

    return md


def create_output_dir(title, output_root):
    """创建输出目录"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d')
    # 使用 日期_标题关键词 作为目录名
    dir_name = sanitize_filename(f"{timestamp}_{title}", max_length=80)
    output_dir = os.path.join(output_root, dir_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# ============================================================
# 主流程
# ============================================================

def scrape_url(url, output_root=None, custom_dir_name=None, filter_level=FILTER_LEVEL_AGGRESSIVE):
    """
    爬取指定 URL 的网页内容并保存为 Markdown

    Args:
        url: 目标网页 URL
        output_root: 输出根目录，默认为 DEFAULT_OUTPUT_ROOT
        custom_dir_name: 自定义输出目录名（可选）
        filter_level: 内容过滤级别 (0=最小, 1=中等, 2=激进)

    Returns:
        bool: 是否成功
    """
    if not output_root:
        output_root = DEFAULT_OUTPUT_ROOT

    print(f"\n{'=' * 70}")
    print(f"  网页内容爬取工具")
    print(f"{'=' * 70}")
    print(f"  目标: {url}")
    print(f"  域名: {get_domain(url)}")
    print(f"{'=' * 70}\n")

    # 1. 获取页面
    response = fetch_page(url)
    if not response:
        print("\n[失败] 无法获取页面内容")
        return False

    raw_html = response.text

    # 2. 解析完整 HTML 获取元数据
    full_soup = BeautifulSoup(raw_html, 'html.parser')
    metadata = extract_metadata(full_soup, url)
    print(f"   [元数据] 作者: {metadata.get('author', '未知')}")
    print(f"   [元数据] 时间: {metadata.get('publish_time', '未知')}")

    # 3. 提取正文
    title, content_html = extract_content(raw_html, url, filter_level=filter_level)

    if not content_html or len(content_html.strip()) < 50:
        print("\n[警告] 提取的正文内容过少，尝试使用完整 body...")
        body = full_soup.find('body')
        if body:
            content_html = str(body)
        else:
            print("\n[失败] 无法提取有效内容")
            return False

    # 4. 创建输出目录
    if custom_dir_name:
        dir_name = sanitize_filename(custom_dir_name)
        output_dir = os.path.join(output_root, dir_name)
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = create_output_dir(title, output_root)

    images_dir = os.path.join(output_dir, IMAGES_DIR_NAME)
    print(f"   [输出] 保存目录: {os.path.abspath(output_dir)}")

    # 5. 处理图片
    image_mapping, content_html = process_images(content_html, url, images_dir)

    # 6. 转换为 Markdown
    print(f"\n   [转换] 正在转换为 Markdown...")
    md_content = html_to_markdown(content_html, image_mapping)

    # 7. 组装最终 Markdown
    final_md_parts = []
    final_md_parts.append(f"# {title}\n")

    # 添加来源信息（方便追溯）
    final_md_parts.append(f"> 来源: {url}")
    if metadata.get('author'):
        final_md_parts.append(f"> 作者: {metadata['author']}")
    if metadata.get('publish_time'):
        final_md_parts.append(f"> 时间: {metadata['publish_time']}")
    final_md_parts.append(f"> 爬取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    final_md_parts.append('')

    final_md_parts.append('---\n')
    final_md_parts.append(md_content)

    final_md = '\n'.join(final_md_parts)

    # 8. 保存 Markdown 文件
    md_path = os.path.join(output_dir, 'content.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(final_md)
    print(f"   [保存] Markdown 已保存: content.md")

    # 9. 保存原始 HTML（备份）
    html_path = os.path.join(output_dir, 'original.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(raw_html)
    print(f"   [保存] 原始 HTML 已保存: original.html")

    # 10. 输出摘要
    img_count = len([f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]) if os.path.exists(images_dir) else 0
    md_size = os.path.getsize(md_path) / 1024

    print(f"\n{'=' * 70}")
    print(f"  爬取完成!")
    print(f"{'=' * 70}")
    print(f"  标题: {title}")
    print(f"  Markdown 大小: {md_size:.1f} KB")
    print(f"  图片数量: {img_count} 张")
    print(f"  保存目录: {os.path.abspath(output_dir)}")
    print(f"  文件列表:")
    print(f"    - content.md     (正文 Markdown)")
    print(f"    - original.html  (原始 HTML)")
    if img_count > 0:
        print(f"    - {IMAGES_DIR_NAME}/         ({img_count} 张图片)")
    print(f"{'=' * 70}")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='通用网页内容爬取工具 - 输入 URL，输出 Markdown + 图片',
        epilog='示例: python3.11 web_to_md.py "https://example.com/article"',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('url', help='要爬取的网页 URL')
    parser.add_argument('-o', '--output', help='自定义输出目录名（可选）', default=None)
    parser.add_argument('-d', '--dir', help='输出根目录路径（可选）', default=None)
    parser.add_argument('-f', '--filter', 
                        type=int, 
                        choices=[0, 1, 2],
                        default=2,
                        help='内容过滤级别：0=最小过滤（保留所有），1=中等过滤（过滤广告），2=激进过滤（只保留正文，默认）')

    args = parser.parse_args()

    # 验证 URL
    url = args.url.strip()
    if not url.startswith(('http://', 'https://')):
        print("[错误] 请提供有效的 URL（以 http:// 或 https:// 开头）")
        sys.exit(1)

    output_root = args.dir or DEFAULT_OUTPUT_ROOT
    filter_level = args.filter
    success = scrape_url(url, output_root=output_root, custom_dir_name=args.output, filter_level=filter_level)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
