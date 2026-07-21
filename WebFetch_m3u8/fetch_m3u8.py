import os
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 配置文件路径
URL_FILE = 'url.txt'
OUTPUT_FILE = 'live_links.txt'

def get_optimized_chrome():
    """为 Linux 容器环境配置 Chrome"""
    chrome_options = Options()
    # 核心修复参数：无头模式、沙盒限制、共享内存、GPU禁用
    options = ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    for arg in options:
        chrome_options.add_argument(arg)
    return webdriver.Chrome(options=chrome_options)

def extract_m3u8_from_logs(driver):
    """从网络日志中提取 m3u8 链接"""
    m3u8_urls = set()
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            log_data = json.loads(entry['message'])['message']
            # 只关注网络请求的发送或接收
            if 'Network.requestWillBeSent' in log_data['method']:
                request_url = log_data['params']['request']['url']
                # 匹配包含 .m3u8 且不包含 'master' 的链接（不区分大小写）
                if '.m3u8' in request_url.lower() and 'master' not in request_url.lower():
                    m3u8_urls.add(request_url)
    except Exception as e:
        print(f"解析日志出错: {e}")
    return m3u8_urls

def main():
    # 检查并读取 url.txt
    if not os.path.exists(URL_FILE):
        print(f"错误：未找到 {URL_FILE} 文件，请在同级目录下创建并添加目标网页地址。")
        return
    
    with open(URL_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    if not urls:
        print(f"{URL_FILE} 中没有找到有效的网址。")
        return

    print(f"已加载 {len(urls)} 个网页地址，准备开始动态解析...")
    
    all_extracted_m3u8 = set()
    driver = init_driver()

    try:
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] 正在解析网页: {url}")
            try:
                driver.get(url)
                # 等待 8 秒让网页动态加载并播放视频流（可根据网速调整）
                time.sleep(8) 
                
                # 抓取当前页面的 m3u8 链接
                found_urls = extract_m3u8_from_logs(driver)
                print(f"-> 发现 {len(found_urls)} 个符合要求的 m3u8 链接")
                all_extracted_m3u8.update(found_urls)
                
            except Exception as e:
                print(f"访问网页失败 {url}: {e}")
                
    finally:
        driver.quit()

    # 将结果写入 live_links.txt（自动去重并覆盖/创建文件）
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for link in sorted(all_extracted_m3u8):
            f_out.write(link + '\n')
            
    print(f"\n🎉 任务完成！共获取到 {len(all_extracted_m3u8)} 个去重后的链接，已保存至 '{OUTPUT_FILE}'。")

if __name__ == '__main__':
    main()
