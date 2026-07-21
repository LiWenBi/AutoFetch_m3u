import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 配置文件名
URL_FILE = 'url.txt'
OUTPUT_FILE = 'live_links.txt'

def init_driver():
    """初始化 Chrome，优化 Docker/GitHub Actions 环境参数"""
    chrome_options = Options()
    # 核心修复参数：headless=new, no-sandbox, disable-dev-shm-usage
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return webdriver.Chrome(options=chrome_options)

def extract_m3u8_from_logs(driver):
    """从网络性能日志中提取 .m3u8 链接"""
    m3u8_urls = set()
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            log_data = json.loads(entry['message'])['message']
            if 'Network.requestWillBeSent' in log_data['method']:
                url = log_data['params']['request']['url']
                # 过滤 .m3u8 并排除 master 类型
                if '.m3u8' in url.lower() and 'master' not in url.lower():
                    m3u8_urls.add(url)
    except Exception as e:
        print(f"解析日志出错: {e}")
    return m3u8_urls

def main():
    if not os.path.exists(URL_FILE):
        print(f"错误：未找到 {URL_FILE}。")
        return
    
    with open(URL_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    driver = init_driver()
    all_links = set()
    try:
        for url in urls:
            print(f"正在分析: {url}")
            driver.get(url)
            time.sleep(8) # 等待 JavaScript 动态渲染
            all_links.update(extract_m3u8_from_logs(driver))
    finally:
        driver.quit()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        f_out.write('\n'.join(sorted(all_links)))
    print(f"完成！已保存 {len(all_links)} 个链接至 {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
