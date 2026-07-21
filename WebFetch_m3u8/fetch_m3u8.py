import asyncio
from playwright.async_api import async_playwright

async def get_m3u8_from_url(url: str):
    """
    启动无头浏览器，访问目标网页并拦截所有网络请求，提取 M3U8 链接
    """
    print(f"\n[开始嗅探] 正在分析网页: {url}")
    m3u8_links = set() # 使用集合去重

    async with async_playwright() as p:
        # 启动 Chromium 浏览器（无头模式）
        browser = await p.chromium.launch(headless=True)
        
        # 伪装常用浏览器 User-Agent，防止被轻易拦截
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 定义网络请求拦截回调函数
        async def handle_request(request):
            # 判断请求的 URL 中是否包含 .m3u8
            if ".m3u8" in request.url:
                # 排除可能干扰的打点或测试链接（可根据需要去掉此过滤）
                if "test" not in request.url.lower():
                    m3u8_links.add(request.url)
                    print(f" -> 捕获到 M3U8: {request.url}")

        # 监听页面的所有网络请求
        page.on("request", handle_request)

        try:
            # 访问网页，waitUntil="networkidle" 表示等待网络请求基本空闲（最长等待30秒）
            # 对于部分直播网站，通常页面一加载就会立刻发出 m3u8 请求
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 【重要】如果部分网站需要点击播放才会加载 M3U8，可以在此处手动增加等待或模拟点击
            # 例如强制多等待 5 秒，确保动态 JS 脚本执行完毕
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[提示] 页面加载可能超时或受阻，但已捕获的链接依然有效。错误信息: {e}")
        finally:
            await browser.close()

    return list(m3u8_links)

async def main():
    # 替换为你需要获取 M3U8 的两个网页目标地址
    urls = [
        "https://zh.stripchat.com/winter11",
        "https://zh-hans.chaturbate.com/akina520/"
    ]
    
    # 循环遍历并依次处理两个网页
    for target_url in urls:
        results = await get_m3u8_from_url(target_url)
        
        print(f"=== {target_url} 提取结果 ===")
        if results:
            for idx, link in enumerate(results, 1):
                print(f"[{idx}] {link}")
        else:
            print("❌ 未捕获到 M3U8 链接，可能需要登录、绕过年龄验证或该主播当前未开播。")

if __name__ == "__main__":
    # 启动异步事件循环
    asyncio.run(main())
