import os 
import time 
import json 
import sys
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 

# 1. 配置需要收集的直播网页列表 
TARGET_URLS = [ 
    "https://chococams.com", 
    "https://chococams.com",  
    "https://chococams.com" 
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
    """动态选择有头/无头模式，捕获网络请求中的 m3u8 链接""" 
    new_links = set() 
    options = Options() 
    
    # 严格检查运行环境：如果检测到是 GitHub Actions，则强制启动无头模式防闪退
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print("[环境提示] 当前处于 GitHub Actions 云端环境，强制启用 --headless 无头模式。")
        options.add_argument("--headless=new") 
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--disable-gpu")
    else:
        print("[环境提示] 当前处于本地电脑环境，正在为您启动【有头浏览器】窗口。")
    
    # 保持防爬虫伪装参数
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
        
        # 延长等待时间供页面完整加载
        print("等待 15 秒加载媒体流数据...")
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
                        # 【核心修复】取 split 后的第 0 个元素，确保 clean_url 是纯字符串而不是 List 列表
                        clean_url = request_url.split('?')[0] 
                        if clean_url not in existing_links and clean_url not in new_links: 
                            print(f"发现新链接: {clean_url}") 
                            new_links.add(clean_url) 
            except Exception: 
                continue 
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
