import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

URL_FILE = 'url.txt'
OUTPUT_FILE = 'live_links.txt'

def init_driver():
    """初始化配置坚固的 Chrome 浏览器实例"""
    chrome_options = Options()
    
    # 彻底解决容器环境闪退的核心参数组
    chrome_options.add_argument('--headless=new')          # 必须使用新版无头模式
    chrome_options.add_argument('--no-sandbox')             # 禁用沙盒，Linux 容器必需
    chrome_options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm共享内存限制，防止崩溃
    chrome_options.add_argument('--disable-gpu')            # 禁用GPU硬件加速
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 禁用图片加载提升速度
    
    # 开启网络包日志捕获
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_m3u8_from_logs(driver):
    """从浏览器性能日志过滤出合规的 m3u8 地址"""
    m3u8_urls = set()
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            log_data = json.loads(entry['message'])['message']
            if 'Network.requestWillBeSent' in log_data['method']:
                url = log_data['params']['request']['url']
                # 去除包含 'master' 的链接（不区分大小写）
                if '.m3u8' in url.lower() and 'master' not in url.lower():
                    m3u8_urls.add(url)
    except Exception as e:
        print(f"提取网络日志异常: {e}")
    return m3u8_urls

def main():
    if not os.path.exists(URL_FILE):
        print(f"错误：未找到 {URL_FILE} 文件。")
        return
        
    with open(URL_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    if not urls:
        print("没有可解析的网址。")
        return

    print(f"开始解析 {len(urls)} 个网址...")
    driver = init_driver()
    all_links = set()
    
    try:
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] 正在读取: {url}")
            try:
                driver.get(url)
                time.sleep(10) # 适当延长等待时间，保证动态流加载完毕
                found = extract_m3u8_from_logs(driver)
                print(f"  -> 成功捕获 {len(found)} 个 m3u8 链接")
                all_links.update(found)
            except Exception as e:
                print(f"  -> 访问网址失败: {e}")
    finally:
        driver.quit()

    # 写入输出文件（去重并按字母排序）
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        f_out.write('\n'.join(sorted(all_links)) + '\n')
        
    print(f"所有任务执行完毕，结果已保存至 {OUTPUT_FILE}，共 {len(all_links)} 条。")

if __name__ == '__main__':
    main()
