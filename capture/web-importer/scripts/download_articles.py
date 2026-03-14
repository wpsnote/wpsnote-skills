# -*- coding=utf-8
"""
微信公众号文章下载工具
下载文章内容和图片到本地

使用方式：
1. 单链接下载：python3.11 download_articles.py "https://mp.weixin.qq.com/s/xxxxx"
2. 批量下载：python3.11 download_articles.py（使用内置列表）
3. 最新推文下载到历史推文：python3.11 download_articles.py --latest
"""
import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urlparse, parse_qs
import json
import sys
import datetime

# 文章列表
ARTICLES = [
    {"title": "录音早就不是秘密了，但效率红利怎么还没轮到我？", "url": "https://mp.weixin.qq.com/s/Qf6DInzduIO9ULDP03zmUQ"},
    {"title": "从会对话到会干活，AI Agent 如何实现动作闭环？", "url": "https://mp.weixin.qq.com/s/tZe2Eo9TW1rSg7u_hYYcsg"},
    {"title": "高考志愿填报千万别全指望 AI，这3个关键点必须自己掌握（附攻略）", "url": "https://mp.weixin.qq.com/s/Bho8CiTWLPdASDIHnnv3lw"},
    {"title": "OpenAI 重新 Open后，开源小尺寸模型断层领先。", "url": "https://mp.weixin.qq.com/s/8gHYBnEBk-DKy-9JwzflfA"},
    {"title": "三分钟私有化部署 Claude Code：安全+降本90%，一步到位！", "url": "https://mp.weixin.qq.com/s/b28xU1C-M3uKPy0zWssiug"},
    {"title": "Kimi K2：你怎么敢在巨头面前开源？", "url": "https://mp.weixin.qq.com/s/TR34ETFlZD0CTN4F_sezog"},
    {"title": "深度拆解产品：一款「可控」的AI生图工具该怎么设计?", "url": "https://mp.weixin.qq.com/s/hRvrQA6X4c5rNlzsHSGRDA"},
    {"title": "我发现了一个几乎不可能被 AI 替代的工作", "url": "https://mp.weixin.qq.com/s/YparUcSbbmFh3eznVOWF6A"},
    {"title": "我替你们试了，飞书的最佳平替，终于开源了（附私有化部署教程）", "url": "https://mp.weixin.qq.com/s/9lqbi6ucr1GH5GiZ2bzdhA"},
    {"title": "GPT-5 发布，成本减半，然后垂类大模型快被端了…", "url": "https://mp.weixin.qq.com/s/s81BYH8ZflY5RS5i0Cg-Cg"},
    {"title": "我用AI复活了敦煌壁画里的人，也找到了AI创作的秘密。", "url": "https://mp.weixin.qq.com/s/An_W_ekg6eyrdwOrN2yqvw"},
    {"title": "AI 加速编程，而我却在让渡大脑", "url": "https://mp.weixin.qq.com/s/M-Zx087YnnX2YylgAX3EkQ"},
    {"title": "告别流量焦虑：我让阅读量提升500%的数据分析法。", "url": "https://mp.weixin.qq.com/s/bptkwRbHDs8Dz5XXXxoaww"},
    {"title": "Sora App 发布8小时后，B站和抖音们真正的挑战才刚刚开始", "url": "https://mp.weixin.qq.com/s/Kzs-Bda1c7F1ieWC8Zl87w"},
    {"title": "AIGC 小白动嘴做海报的时代来了", "url": "https://mp.weixin.qq.com/s/TvpEhfy_ASsMqi02xe8SWw"},
    {"title": "我花10小时写的原创，被AI在10分钟内偷走了。", "url": "https://mp.weixin.qq.com/s/6yWlI1xG8cA_KK_afkNwuA"},
    {"title": "AI 没有杀死产品经理，但正在杀死 PMF", "url": "https://mp.weixin.qq.com/s/rarPJe0uKSUlBeLGriBNnQ"},
    {"title": "你们公司投在 AI 增效的钱，是烧掉了，还是成了资产？", "url": "https://mp.weixin.qq.com/s/E6Fh7kqR8PGMzyoiSyvF-w"},
    {"title": "当友商开着飞机来的时候，你挖的护城河还有用吗？", "url": "https://mp.weixin.qq.com/s/MztVsps4aRpvzkaoqKvQWg"},
    {"title": "WPS AI 产品总监：用户需要的是 AI 副驾，不是 AI 代驾", "url": "https://mp.weixin.qq.com/s/fCiZIPsONcYqZlCu7_QSOA"},
    {"title": "亲测 Sora App 成为目前地表最强 AIGC  二创工具", "url": "https://mp.weixin.qq.com/s/ZaW5ghq0905_eFG0WTHukA"},
    {"title": "2048 搭小山 之进阶攻略", "url": "https://mp.weixin.qq.com/s/2kr__7lAt9-F7VBIO_jvtA"},
    {"title": "AI Agent 很鸡贼，RPA 这样的老实人如何自处？", "url": "https://mp.weixin.qq.com/s/kUWqJtVetnNSm8TEii4Arg"},
    {"title": "为庆祝程序员节，我为你做了个魔性小游戏", "url": "https://mp.weixin.qq.com/s/2Un-4vdyF9r5BBxwf8GO9Q"},
    {"title": "都说小朋友才过假期，成年人只有 Q4", "url": "https://mp.weixin.qq.com/s/wYXKYMmqtuCNp7fuCXI7zw"},
    {"title": "我们热议的AI，为何对 90% 的人是无效技术？", "url": "https://mp.weixin.qq.com/s/tEXpEajC6REXGa6u2QE3xA"},
    {"title": "我用 AI 回答了圆明园的「遗憾」，并找到了驾驭 AI 的三个原则", "url": "https://mp.weixin.qq.com/s/zmCVBzwuv0oSDZTAtgVg8g"},
    {"title": "你觉得 AI 不聪明，AI 觉得你不诚实。", "url": "https://mp.weixin.qq.com/s/ohjAnA14eixGE9bMJeBROw"},
    {"title": "别卷 Prompt 了，上下文工程正在淘汰你", "url": "https://mp.weixin.qq.com/s/8jJ5vaRMB7QSBR-yhoP5fQ"},
    {"title": "刘润年度演讲2025：进化的力量（演讲全文）", "url": "https://mp.weixin.qq.com/s/XBfB5GmBd6ZUY6aDLu9X5w"},
    {"title": "AI：我只是琴，我不是你的子期。", "url": "https://mp.weixin.qq.com/s/r4_--E-mi-2dkGsooGUXLw"},
    {"title": "复盘：AI 负责「做对」，总监负责「选对」", "url": "https://mp.weixin.qq.com/s/SqilL-54GYzqxu2IeLj5dg"},
    {"title": "为什么你开发的 AI 产品，正在变得不值钱？", "url": "https://mp.weixin.qq.com/s/BWdnD0NZmK9eVBaCQljdlg"},
    {"title": "月付 1300 元，我成了 AI 付费打工人（附工具列表）", "url": "https://mp.weixin.qq.com/s/ag-BCtTGMnthrEyA4t3nug"},
    {"title": "我把 AI 预算SOP做成了工具，90秒快速演示，告别拍脑袋。", "url": "https://mp.weixin.qq.com/s/RBL9IPhu9oy8rNGXhG3ZQA"},
    {"title": "我们如何迎接另一个我？", "url": "https://mp.weixin.qq.com/s/g7iqD8dKTwfGmcbMH0utTg"},
    {"title": "没想到 Nano Banana Pro 成了开盒神器，如何自保？", "url": "https://mp.weixin.qq.com/s/vBK7W0BqoDMgfBAjtTi4hg"},
    {"title": "Nano Banana Pro 懂个锤子的物理", "url": "https://mp.weixin.qq.com/s/A6e1e5M_RX2xb-Y2J93XEg"},
    {"title": "Nano Banana Pro 为什么能做 PPT？", "url": "https://mp.weixin.qq.com/s/OXm0zQJFdtAxG-KKjL7kWQ"},
    {"title": "你每月烧掉的 Token 费用，至少 20% 都是冤枉钱", "url": "https://mp.weixin.qq.com/s/H2JiPYDAa5rsvnybkkjW3g"},
    {"title": "送你一套提示词，帮你在千问 AI 小剧场里横着走，无痛搞抽象", "url": "https://mp.weixin.qq.com/s/z3x_Mw_Uydd-a-0nZWjMdw"},
    {"title": "Gemini 3 Flash 来了，1 分钟带你快速了解", "url": "https://mp.weixin.qq.com/s/NU5KzQljyxftmFXapyz_LA"},
    {"title": "普通人做应用，最好的 PMF，其实是你自己", "url": "https://mp.weixin.qq.com/s/spVtt8XkG7Vet6IGZgapFA"},
    {"title": "敢让 AI 帮你写总结？你也是心大。它大字都不认识！", "url": "https://mp.weixin.qq.com/s/IsVvBu8h8OqIrmVz0DZd3A"},
    {"title": "格物：Nano Banana 核心靠什么？", "url": "https://mp.weixin.qq.com/s/IKkPZIkfOERdVm_vJ06u6w"},
    {"title": "年终总结：别卷了，AI 的底裤都快卷没了", "url": "https://mp.weixin.qq.com/s/wixFUyPDk7oNIETzNyYefw"},
    {"title": "做了一个 AI 锐评自己的推文，整破防了", "url": "https://mp.weixin.qq.com/s/ZgL46bKM3SOw9gVdBe9jdA"},
    {"title": "手把手教你部署一个好用的 AI 搭子", "url": "https://mp.weixin.qq.com/s/T3S600XldPxyaQUu4a5a3Q"},
    {"title": "一个月怒砸 500 刀之后，给你这套 AI 私有部署配置方案", "url": "http://mp.weixin.qq.com/s?__biz=MzUwOTcxNjMyNg==&tempkey=MTM1OF9ma1pvSEJsd3ZicDkrVmc2aFVjU240UFFzTzhmY2l5RzZJQlpPNzhpYlh5dTdTUDJBeE1zUVJyQUtzaDlHb0had0p5bFRtaVNrVFhnV1F6Z0ZmVGhwaE5mWWZGZl9jamh0UUtyeld4X2s0cHhNb1FWWGNqLXlGbHM2elU0QU1ZZS1ySVVVWFJBZ3pjcGtGSVdTbjJSMGF4cllYc3Y4MVIzTlFwSTRnfn4%3D&chksm=f90ca3b0ce7b2aa661facc0f9d8c748f0de5f7e18b6e4861891b0c95ce9956b264aee88660b7#rd"},
    {"title": "Vibe do something，然后呢？", "url": "https://mp.weixin.qq.com/s/bMpadjRqkKxr7rhREQEFEA"},
    {"title": "班主任们别再研究天书般的提示词了！这个教程直接喂饭，美图\"张口就来\"！", "url": "https://mp.weixin.qq.com/s/lJ846bE9VZIAZcunRMYhLQ"},
    {"title": "即梦AI字体我有点玩明白了，用这套Prompt提效50%", "url": "https://mp.weixin.qq.com/s/1c088ebd3inxNaZYzjCSiQ"},
    {"title": "AutoGLM 发布之后，如今国产大模型终于长出了手。", "url": "https://mp.weixin.qq.com/s/cNYuEBQn1-n31oVFZEu-kg"},
    {"title": "两周涨粉 1 万，她是怎么做到的？", "url": "https://mp.weixin.qq.com/s/3MlpwaBRRRMpWY9UeENMVw"},
    {"title": "站姐智能体，这个 Prompt 帮你自动扒瓜、写瓜、讲八卦！", "url": "https://mp.weixin.qq.com/s/8uRuqocfiiI9W2Co3lptew"},
    {"title": "难绷，Qwen3 支持 MCP ，却用了个 FunCall 的壳", "url": "https://mp.weixin.qq.com/s/r4izkAYUzbeA4UoI2oSVXw"},
    {"title": "拍照问AI，到底能打穿哪些看不见的场景？", "url": "https://mp.weixin.qq.com/s/GC9Hvis6McG38bWkw5f6YQ"},
    {"title": "你可能看不懂扣子空间为什么重要，但它已经在卡生态位了", "url": "https://mp.weixin.qq.com/s/mzJz2NZmp9EjtI_5MCIx6g"},
    {"title": "粉丝福利：扣子空间邀请码 300 个", "url": "https://mp.weixin.qq.com/s/bovDFSRti6TU6SkeFgQ-kg"},
    {"title": "Lovart 这样的设计 Agent 出现之后，我们距离超级个体还远吗？", "url": "https://mp.weixin.qq.com/s/Q25b0DuXIYReCHVeYLdNLA"},
    {"title": "我写了一段 AI 写标题的提示词，它居然写得比我还稳", "url": "https://mp.weixin.qq.com/s/YbspzxiNa6hCnNS0DBH61w"},
    {"title": "AI 卷成这样，我为什么还要去交大读个硕士？", "url": "https://mp.weixin.qq.com/s/-6LjSIasdVvIM9VCc9wtLw"},
    {"title": "用 AI 做了一次真正的深度研究，才明白什么叫降维打击", "url": "https://mp.weixin.qq.com/s/OSSNVIKZ-UUERn8LifDlUQ"},
    {"title": "我让 AI 押了个高考作文题，它 15 分钟干了我一周的活", "url": "http://mp.weixin.qq.com/s?__biz=MzUwOTcxNjMyNg==&tempkey=MTM1M19USTJXeWxDQm5oTkNUMElSa2tadEtpYVB5UVNGZUp5TXJrN3pXc2haQ0xUdVpLM3ZrQXlkUURtOFBKc0ZVVTBfaFg5dWlFUmtIc3VMejJDN0lTSXBhOXctX20wQUEwUWlzNWJhMldVeVl1S1VNb2pXN1RDc1REQlF1c0NyeXVDd1NldktXSkJyazZ3aDJKU3ZyRzU2QTNRRE0wcGRBaUt1U3JFaEp3fn4%3D&chksm=f90cb54ece7b3c58a091d00f73a4cfe26a44194cc958965669652a0d54048ca2b5d97b7e23b6#rd"},
    {"title": "为什么花钱的 Al Agent 还不好用? 我用一个乘法公式，筛掉了80%的玩具", "url": "https://mp.weixin.qq.com/s/UeJJxndml_LZLaVY66xsEg"},
    {"title": "Google 下注 Diffusion，我系统分析它到底适不适合做 AI 工具", "url": "https://mp.weixin.qq.com/s/gIhjRRmoOT4d3jPSkJcb5A"},
    {"title": "从 MCP 谈起，到底什么才是 AI Native 产品？", "url": "https://mp.weixin.qq.com/s/7xYBo4VDFoJsn8WyvkqAsA"},
]

# 最新推文列表（下载到历史推文目录）
LATEST_ARTICLES = [
    {"title": "别再盲选模型了！AI 助手一句话帮你搞定！", "url": "https://mp.weixin.qq.com/s/jNzws3rDzPasos1K9L7Zog"},
    {"title": "不再再被榜单欺骗，大模型选型，这才是正确姿势！", "url": "https://mp.weixin.qq.com/s/c_Xjqsm0NAkuFRKnEuahiw"},
    {"title": "花21000块钱，测34205条主流大模型用例，结论免费给你", "url": "https://mp.weixin.qq.com/s/mq3zQYeuYpnwubW5dvP6vQ"},
]

# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    # 移除或替换不合法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除前后空格
    filename = filename.strip()
    # 限制长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def validate_wechat_url(url):
    """验证是否为有效的微信公众号文章链接"""
    if not url:
        return False
    return 'mp.weixin.qq.com' in url and ('/s/' in url or '/s?' in url)

def extract_mmdd_from_time(publish_time_str):
    """从发布时间字符串提取 MMDD 格式"""
    if not publish_time_str:
        return ''
    try:
        # 尝试解析时间格式，微信公众号通常是 "2024-01-25 08:30" 这样的格式
        time_obj = datetime.datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M')
        return time_obj.strftime('%m%d')
    except:
        # 如果解析失败，尝试其他格式
        try:
            # 尝试只有日期的格式
            time_obj = datetime.datetime.strptime(publish_time_str.split()[0], '%Y-%m-%d')
            return time_obj.strftime('%m%d')
        except:
            return ''

def extract_yyyymmddhhmm_from_time(publish_time_str):
    """从发布时间字符串提取 yyyymmddhhmm 格式"""
    if not publish_time_str:
        return ''
    try:
        time_obj = datetime.datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M')
        return time_obj.strftime('%Y%m%d%H%M')
    except:
        try:
            time_obj = datetime.datetime.strptime(publish_time_str.split()[0], '%Y-%m-%d')
            return time_obj.strftime('%Y%m%d') + '0000'
        except:
            return ''

def create_folder_name(publish_time, title, use_history_format=False):
    """生成文件夹名称
    use_history_format=False: MMDD 标题关键词（推文/已下载的推文）
    use_history_format=True:  yyyymmddhhmm_标题（历史推文）
    """
    if use_history_format:
        yyyymmddhhmm = extract_yyyymmddhhmm_from_time(publish_time)
        safe_title = sanitize_filename(title)
        if yyyymmddhhmm:
            return f"{yyyymmddhhmm}_{safe_title}"
        else:
            current_ts = datetime.datetime.now().strftime('%Y%m%d%H%M')
            return f"{current_ts}_{safe_title}"
    else:
        mmdd = extract_mmdd_from_time(publish_time)
        title_keywords = title[:15] if len(title) > 15 else title
        safe_keywords = sanitize_filename(title_keywords)
        if mmdd:
            return f"{mmdd} {safe_keywords}"
        else:
            current_mmdd = datetime.datetime.now().strftime('%m%d')
            return f"{current_mmdd} {safe_keywords}"

def download_image(img_url, save_path, max_retries=3):
    """下载单张图片，支持重试"""
    for retry in range(max_retries):
        try:
            response = requests.get(img_url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                if retry < max_retries - 1:
                    print(f"      ⚠️  图片下载失败 (状态码: {response.status_code})，重试 {retry + 1}/{max_retries - 1}")
                    time.sleep(2)
                else:
                    print(f"      ❌ 图片下载失败 (状态码: {response.status_code})")
                    return False
        except Exception as e:
            if retry < max_retries - 1:
                print(f"      ⚠️  图片下载异常: {str(e)}，重试 {retry + 1}/{max_retries - 1}")
                time.sleep(2)
            else:
                print(f"      ❌ 图片下载异常: {str(e)}")
                return False
    return False

def download_article(title, url, base_dir, max_retries=3, use_history_format=False):
    """下载单篇文章，支持重试"""
    print(f"\n📄 正在下载: {title}")
    
    # 文章下载重试逻辑
    for retry in range(max_retries):
        try:
            # 先下载文章内容获取发布时间
            print(f"   🌐 请求文章页面...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                if retry < max_retries - 1:
                    print(f"   ⚠️  请求失败 (状态码: {response.status_code})，重试 {retry + 1}/{max_retries - 1}")
                    time.sleep(2)
                    continue
                else:
                    print(f"   ❌ 请求失败 (状态码: {response.status_code})")
                    return False
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章信息
            article_info = {
                'title': title,
                'url': url,
                'author': '',
                'publish_time': '',
                'content': '',
            }
            
            # 提取作者
            author_tag = soup.find('a', {'id': 'js_name'})
            if author_tag:
                article_info['author'] = author_tag.text.strip()
            
            # 提取发布时间
            time_tag = soup.find('em', {'id': 'publish_time'})
            publish_time_str = ''
            if time_tag and time_tag.text.strip():
                article_info['publish_time'] = time_tag.text.strip()
                publish_time_str = time_tag.text.strip()
            else:
                # 如果页面上没有显示时间，尝试从JavaScript变量中提取
                create_time_match = re.search(r'var createTime = [\'"]([^\'"]+)[\'"]', response.text)
                if create_time_match:
                    publish_time_str = create_time_match.group(1)
                    article_info['publish_time'] = publish_time_str
            
            # 创建文章目录（使用新的命名格式：MMDD 标题关键词）
            folder_name = create_folder_name(publish_time_str, title, use_history_format)
            article_dir = os.path.join(base_dir, folder_name)
            os.makedirs(article_dir, exist_ok=True)
            
            # 创建图片目录（改为"图片素材"）
            images_dir = os.path.join(article_dir, '图片素材')
            os.makedirs(images_dir, exist_ok=True)
        
            # 提取正文内容
            content_div = soup.find('div', {'id': 'js_content'})
            if not content_div:
                print(f"   ❌ 未找到文章内容")
                return False
            
            # 保存原始 HTML
            html_path = os.path.join(article_dir, '原文.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   ✅ HTML 已保存")
            
            # 下载图片
            images = content_div.find_all('img')
            print(f"   🖼️  发现 {len(images)} 张图片")
            
            image_mapping = {}
            img_counter = 1
            failed_images = []
            
            for img in images:
                img_url = img.get('data-src') or img.get('src')
                if not img_url:
                    continue
                
                # 跳过表情图片和占位图
                if 'emotion' in img_url or 'mmbiz_png/0' in img_url:
                    continue
                
                # 确定图片扩展名
                ext = '.jpg'
                if '.png' in img_url:
                    ext = '.png'
                elif '.gif' in img_url:
                    ext = '.gif'
                elif '.webp' in img_url:
                    ext = '.webp'
                
                # 保存图片
                img_filename = f"image_{img_counter:03d}{ext}"
                img_path = os.path.join(images_dir, img_filename)
                
                print(f"      📥 下载图片 {img_counter}: {img_filename}")
                if download_image(img_url, img_path, max_retries=3):
                    local_path = f"./图片素材/{img_filename}"
                    image_mapping[img_url] = local_path
                    
                    # 替换 HTML 中的图片链接
                    img['src'] = local_path
                    if img.get('data-src'):
                        img['data-src'] = local_path
                    
                    # 在图片标签后添加一个特殊标记，用于 Markdown 转换
                    img['data-md-path'] = local_path
                    img_counter += 1
                else:
                    failed_images.append(img_filename)
                
                # 延迟避免请求过快
                time.sleep(1.5)
        
            # 转换为 Markdown 格式（保留图片位置）
            def convert_to_markdown(element):
                """递归转换 HTML 元素为 Markdown"""
                if element.name is None:
                    # 文本节点
                    return element.string if element.string else ''
                
                if element.name == 'img':
                    # 图片标签
                    md_path = element.get('data-md-path')
                    if md_path:
                        alt_text = element.get('alt', '图片')
                        return f"\n\n![{alt_text}]({md_path})\n\n"
                    return ''
                
                # 处理其他标签
                result = []
                for child in element.children:
                    result.append(convert_to_markdown(child))
                
                text = ''.join(result)
                
                # 根据标签类型添加格式
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(element.name[1])
                    return f"\n\n{'#' * level} {text.strip()}\n\n"
                elif element.name == 'p':
                    return f"\n\n{text.strip()}\n\n"
                elif element.name == 'strong' or element.name == 'b':
                    return f"**{text}**"
                elif element.name == 'em' or element.name == 'i':
                    return f"*{text}*"
                elif element.name == 'br':
                    return '\n'
                elif element.name == 'section':
                    return text
                else:
                    return text
            
            # 生成 Markdown 内容
            md_content = convert_to_markdown(content_div)
            # 清理多余的空行
            md_content = re.sub(r'\n{3,}', '\n\n', md_content)
            article_info['content'] = md_content.strip()
            
            # 保存 Markdown 格式（改为"终稿.md"，不包含元信息）
            md_path = os.path.join(article_dir, '终稿.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"{article_info['title']}\n")
                f.write(md_content)
            print(f"   ✅ Markdown 已保存（终稿.md）")
            
            # 保存元数据
            meta_path = os.path.join(article_dir, 'meta.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'title': article_info['title'],
                    'author': article_info['author'],
                    'publish_time': article_info['publish_time'],
                    'url': article_info['url'],
                    'images_count': len(image_mapping),
                    'failed_images_count': len(failed_images),
                    'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            
            # 显示下载摘要
            print(f"\n   📊 下载摘要:")
            print(f"      📁 保存路径: {article_dir}")
            print(f"      🖼️  图片总数: {len(images)}")
            print(f"      ✅ 成功: {len(image_mapping)} 张")
            print(f"      ❌ 失败: {len(failed_images)} 张")
            if failed_images:
                print(f"      失败列表: {', '.join(failed_images)}")
            
            print(f"\n   ✅ 文章下载完成!")
            return True
            
        except Exception as e:
            if retry < max_retries - 1:
                print(f"   ⚠️  下载失败: {str(e)}，重试 {retry + 1}/{max_retries - 1}")
                time.sleep(2)
                continue
            else:
                print(f"   ❌ 下载失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    
    return False

def download_single_article_from_url(url):
    """从URL下载单篇文章"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 单链接模式")
    print("=" * 80)
    
    # 验证链接
    if not validate_wechat_url(url):
        print("❌ 错误: 无效的微信公众号文章链接")
        print("\n使用说明:")
        print('  python3.11 download_articles.py "https://mp.weixin.qq.com/s/xxxxx"')
        return False
    
    print(f"📎 文章链接: {url}")
    
    # 创建保存目录（保存到"推文"目录）
    base_dir = os.path.join(os.path.dirname(__file__), '..', '推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"📁 保存目录: {os.path.abspath(base_dir)}\n")
    
    # 下载文章（不需要提供标题，会自动从页面提取）
    success = download_article_from_url(url, base_dir)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 下载成功!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 下载失败")
        print("=" * 80)
    
    return success

def download_article_from_url(url, base_dir, max_retries=3):
    """从URL下载文章（自动提取标题）"""
    print(f"\n📄 正在获取文章信息...")
    
    # 先请求一次获取标题
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"   ❌ 请求失败 (状态码: {response.status_code})")
            return False
        
        # 解析标题
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('h1', {'class': 'rich_media_title'}) or soup.find('h2', {'class': 'rich_media_title'})
        
        if title_tag:
            title = title_tag.text.strip()
            print(f"   📝 文章标题: {title}")
        else:
            print(f"   ⚠️  未找到标题，使用默认标题")
            title = "未命名文章"
        
        # 调用原有的下载函数
        return download_article(title, url, base_dir, max_retries)
        
    except Exception as e:
        print(f"   ❌ 获取文章信息失败: {str(e)}")
        return False

def batch_download():
    """批量下载模式"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 批量下载模式")
    print("=" * 80)
    print(f"共 {len(ARTICLES)} 篇文章待下载")
    print("=" * 80)
    
    # 创建保存目录
    base_dir = os.path.join(os.path.dirname(__file__), '..', '已下载的推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"\n📁 保存目录: {os.path.abspath(base_dir)}\n")
    
    # 统计
    success_count = 0
    fail_count = 0
    
    # 下载所有文章
    for idx, article in enumerate(ARTICLES, 1):
        print(f"\n[{idx}/{len(ARTICLES)}]", end=" ")
        
        if download_article(article['title'], article['url'], base_dir):
            success_count += 1
        else:
            fail_count += 1
        
        # 延迟避免请求过快
        if idx < len(ARTICLES):
            print(f"\n   ⏳ 等待 5 秒...")
            time.sleep(5)
    
    # 输出统计
    print("\n" + "=" * 80)
    print("📊 下载完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {fail_count} 篇")
    print(f"📁 保存位置: {os.path.abspath(base_dir)}")
    print("=" * 80)

def download_latest_to_history():
    """下载最新推文到历史推文目录"""
    print("=" * 80)
    print("微信公众号文章下载工具 - 最新推文 → 历史推文")
    print("=" * 80)
    print(f"共 {len(LATEST_ARTICLES)} 篇文章待下载")
    print("=" * 80)

    base_dir = os.path.join(os.path.dirname(__file__), '..', '历史推文')
    os.makedirs(base_dir, exist_ok=True)
    print(f"\n📁 保存目录: {os.path.abspath(base_dir)}\n")

    success_count = 0
    fail_count = 0

    for idx, article in enumerate(LATEST_ARTICLES, 1):
        print(f"\n[{idx}/{len(LATEST_ARTICLES)}]", end=" ")

        if download_article(article['title'], article['url'], base_dir, use_history_format=True):
            success_count += 1
        else:
            fail_count += 1

        if idx < len(LATEST_ARTICLES):
            print(f"\n   ⏳ 等待 5 秒...")
            time.sleep(5)

    print("\n" + "=" * 80)
    print("📊 下载完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {fail_count} 篇")
    print(f"📁 保存位置: {os.path.abspath(base_dir)}")
    print("=" * 80)


def main():
    """主函数"""
    # 检查 --latest 参数
    if '--latest' in sys.argv:
        download_latest_to_history()
        return

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 单链接下载模式
        url = sys.argv[1]
        download_single_article_from_url(url)
    else:
        # 批量下载模式
        batch_download()


if __name__ == '__main__':
    main()
