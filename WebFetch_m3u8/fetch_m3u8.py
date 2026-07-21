import asyncio
from playwright.async_api import async_playwright

# 1. 改为列表（List），支持放多个需要检测的网页
TARGET_URLS = [
    "https://chococams.com/model/stripchat/jiajia_l",
    "https://chococams.com/model/chaturbate/cute_fox_girl"
]

async def handle_request(request):
    """
    拦截并检查每一个网络请求
    """
    url = request.url
    # 检查请求链接中是否包含 .m3u8 关键字
    if ".m3u8" in url.lower():
        print(f"\n🎉 成功捕获到 m3u8 链接:")
        print(f"URL: {url}")
        print(f"请求方法: {request.method}")
        print("-" * 50)

async def check_url(context, url):
    """
    处理单个网址的抓取逻辑
    """
    page = await context.new_page()
    
    # 绑定网络监听事件
    page.on("request", handle_request)
    
    print(f"\n[开始处理] 正在打开网页: {url} ...")
    try:
        # 访问网页，等待网络相对空闲
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        
        # 给网页 3 秒让其渲染 DOM 树
        await asyncio.sleep(3)
        
        # 💡 针对流媒体网站的核心：尝试寻找播放按钮并点击
        # 这里使用了多个常见的播放按钮选择器（文字包含、图标样式等）
        play_selectors = [
            "text=Play", "text=播放", 
            ".play-button", "[aria-label='Play']", 
            ".video-js .vjs-big-play-button", ".play-btn"
        ]
        
        clicked = False
        for selector in play_selectors:
            try:
                # 检查选择器是否存在且可见
                if await page.locator(selector).is_visible(timeout=2000):
                    await page.click(selector)
                    print(f"👉 成功点击了播放按钮: {selector}")
                    clicked = True
                    break
            except Exception:
                continue
        
        if not clicked:
            # 如果没找到特定的按钮类名，直接模拟点击屏幕中心（通常是播放器中心位置）
            print("⚠️ 未找到明确的播放按钮，尝试点击页面中心以触发播放...")
            viewport = page.viewport_size
            if viewport:
                await page.mouse.click(viewport['width'] / 2, viewport['height'] / 2)
            else:
                await page.mouse.click(500, 400)

        print("⌛ 正在等待视频加载/缓冲（持续 15 秒）...")
        await asyncio.sleep(15)  # 留出足够时间让 m3u8 请求触发
        
    except Exception as e:
        print(f"❌ 处理网址 {url} 时发生错误: {e}")
    finally:
        # 显式关闭当前页面，释放内存，防止影响下一个网址
        await page.close()

async def main():
    async with async_playwright() as p:
        # 在本地调试时建议将 headless 改为 False，能直观看到有没有点击成功
        # 部署到 GitHub Actions 时请务必改回 True
        browser = await p.chromium.launch(headless=True)
        
        # 创建上下文，加入更逼真的浏览器请求头
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        # 循环遍历每个网址
        for url in TARGET_URLS:
            await check_url(context, url)
            
        # 最终关闭浏览器
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
