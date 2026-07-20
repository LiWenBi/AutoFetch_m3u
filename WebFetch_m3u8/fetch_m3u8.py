import os
import time
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
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 修正后的新版配置日志写法
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # 初始化浏览器（确保这一行是 4 个空格缩进）
    driver = webdriver.Chrome(options=options)
    
    # 注意：这里的 try 必须和上面的 driver = ... 保持完全对齐（4个空格）
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        time.sleep(10)  # 等待页面加载
        
        # 解析浏览器网络日志
        logs = driver.get_log('performance')
        for entry in logs:
            import json
            log = json.loads(entry['message'])['message']
            if 'Network.requestWillBeSent' in log['method']:
                request_url = log['params']['request']['url']
                if ".m3u8" in request_url:
                    if request_url not in existing_links:
                        print(f"发现新链接: {request_url}")
                        new_links.add(request_url)
                        
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
