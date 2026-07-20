import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. 配置需要收集的直播网页列表
TARGET_URLS = [
    "https://zh.stripchat.com/winter11",
    "https://zh-hans.chaturbate.com/baeasian/"
]
DATA_FILE = "live_links.txt"

def load_existing_links():
    """读取本地已有的链接，防止重复"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_links(links):
    """保存不重复的链接"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for link in sorted(links):
            f.write(f"{link}\n")

def fetch_m3u8_from_url(url, existing_links):
    """启动无头浏览器，捕获网络请求中的 m3u8 链接"""
    new_links = set()
    
    options = Options()
    options.add_argument("--headless=new")  # 使用全新的无头模式，更难被检测
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 绕过成人网站和反爬系统的关键伪装参数
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 开启性能日志
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    # 执行 JavaScript 抹除自动化特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 针对这类直播网站，适当延长等待时间（15秒），让 Cloudflare 验证通过并加载出直播视频
        time.sleep(15) 
        
        # 解析浏览器网络日志
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if 'Network.requestWillBeSent' in log.get('method', ''):
                    params = log.get('params', {})
                    request = params.get('request', {})
                    request_url = request.get('url', '')
                    
                    # 匹配 m3u8 链接
                    if ".m3u8" in request_url:
                        # 部分平台的 m3u8 后面带有超长动态 token，这里进行去重清洗（只保留问号前的主干 URL）
                        clean_url = request_url.split('?')[0]
                        
                        if clean_url not in existing_links and clean_url not in new_links:
                            print(f"发现新链接: {clean_url}")
                            new_links.add(clean_url)
            except Exception:
                continue # 遇到解析不规范的日志片段直接跳过，不中断程序
                
    except Exception as e:
        print(f"访问出错 {url}: {e}")
    finally:
        driver.quit()
        
    return new_links

if __name__ == "__main__":
    existing_links = load_existing_links()
    all_new_links = set()
    
    for url in TARGET_URLS:
        new_urls = fetch_m3u8_from_url(url, existing_links)
        all_new_links.update(new_urls)
        
    if all_new_links:
        final_links = existing_links.union(all_new_links)
        save_links(final_links)
        print(f"任务完成！新增 {len(all_new_links)} 条链接，总计 {len(final_links)} 条。")
    else:
        print("未发现新的 m3u8 链接。")
