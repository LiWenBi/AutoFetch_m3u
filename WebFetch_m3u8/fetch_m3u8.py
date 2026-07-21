import asyncio
import os
from playwright.async_api import async_playwright

async def get_m3u8_from_url(url: str):
    """
    启动无头浏览器，访问目标网页并拦截所有网络请求，提取 M3U8 链接
    """
    print(f"\n[开始嗅探] 正在分析网页: {url}")
    m3u8_links = set()  # 使用集合去重

    async with async_playwright() as p:
        # 启动 Chromium 浏览器（无头模式）
        browser = await p.chromium.launch(headless=True)
        
        # 伪装常用浏览器 User-Agent，防止被平台拦截
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        # 定义网络请求拦截回调函数
        async def handle_request(request):
            # 判断请求的 URL 中是否包含 .m3u8
            if ".m3u8" in request.url:
                # 过滤掉一些无效的测试链接，只保留真正的直播流
                if "test" not in request.url.lower():
                    m3u8_links.add(request.url)
                    print(f" -> 💡 成功捕获 M3U8: {request.url}")

        # 监听页面的所有网络请求
        page.on("request", handle_request)

        try:
            # 1. 打开网页
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            # 2. 自动化处理平台特有的【年龄验证弹窗】或【进入房间按钮】
            await asyncio.sleep(3)  # 等待弹窗加载
            
            # 针对 Stripchat 的“进入房间/接受Cookie”按钮
            stripchat_btn = await page.query_selector("button:has-text('进入房间'), button:has-text('Enter'), [data-clickable-id='close-popup']")
            if stripchat_btn:
                await stripchat_btn.click()
                print(" -> 已自动点击 Stripchat 准入按钮")

            # 针对 Chaturbate 的“我已年满18岁”按钮
            chaturbate_btn = await page.query_selector("text='I am 18 or older', text='我已年满18岁'")
            if chaturbate_btn:
                await chaturbate_btn.click()
                print(" -> 已自动点击 Chaturbate 年龄确认按钮")

            # 3. 额外等待 8 秒，让动态播放器充分加载并发出 M3U8 流量
            await asyncio.sleep(8)
            
        except Exception as e:
            print(f"[提示] 页面解析时出现异常（可能主播未开播或触发反爬盾）: {e}")
        finally:
            await browser.close()

    return list(m3u8_links)

async def main():
    # 填入你的目标网址
    urls = [
        "https://stripchat.com/winter11",
        "https://chaturbate.com/akina520/"
    ]
    
    all_results = []
    
    # 循环遍历并依次处理两个网页
    for target_url in urls:
        results = await get_m3u8_from_url(target_url)
        print(f"\n=== {target_url} 提取结果 ===")
        if results:
            for idx, link in enumerate(results, 1):
                print(f"[{idx}] {link}")
                all_results.append(link)
        else:
            print("❌ 未捕获到 M3U8 链接。原因可能为：主播未开播、房间被封禁或触发反爬盾。")

    # 【完整性修复】自动将获取到的所有 M3U8 链接写入到项目根目录的 live_links.txt 文件中
    # 每次运行都会覆盖旧的链接，确保里面都是最新可用的
    with open("live_links.txt", "w", encoding="utf-8") as f:
        if all_results:
            for link in all_results:
                f.write(link + "\n")
            print(f"\n✅ 成功将 {len(all_results)} 条最新链接保存到 live_links.txt")
        else:
            f.write("当前无可用直播链接\n")
            print("\n⚠️ 未发现有效链接，已重置 live_links.txt")

if __name__ == "__main__":
    # 启动异步事件循环
    asyncio.run(main())
