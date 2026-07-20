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
