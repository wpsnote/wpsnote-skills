"""
将 PDF/PPT 的每一页转换为 PNG 图片，用于图片类文档的视觉解读。
用法：python3 scripts/pdf_to_images.py /path/to/file.pdf
输出：/tmp/pdf_pages_<pid>/page_01.png, page_02.png, ...
"""
import sys
import os

try:
    import fitz
except ImportError:
    import subprocess
    subprocess.run(["pip3", "install", "pymupdf", "-q"], check=True)
    import fitz

def convert_pdf_to_images(pdf_path: str, out_dir: str = None, dpi: int = 150, max_pages: int = 40):
    if not os.path.isfile(pdf_path):
        print(f"错误: 文件不存在 - {pdf_path}", file=sys.stderr)
        sys.exit(1)
    if out_dir is None:
        out_dir = f"/tmp/pdf_pages_{os.getpid()}"
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    total = len(doc)
    pages_to_process = min(total, max_pages)
    
    saved = []
    for i in range(pages_to_process):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        out_path = os.path.join(out_dir, f"page_{i+1:02d}.png")
        pix.save(out_path)
        saved.append(out_path)
    
    doc.close()
    
    if total > max_pages:
        print(f"[注意] 文件共 {total} 页，仅处理前 {max_pages} 页")
    
    print(f"转换完成，共 {len(saved)} 张图片保存至 {out_dir}")
    for p in saved:
        print(p)
    
    return saved

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 pdf_to_images.py /path/to/file.pdf")
        sys.exit(1)
    convert_pdf_to_images(sys.argv[1])
