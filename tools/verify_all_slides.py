import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path='/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            headless=True
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        print("Navigating to http://localhost:8080/index.html...")
        await page.goto("http://localhost:8080/index.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Handle Role Gate if shown
        role_gate = page.locator("#roleGate")
        if await role_gate.is_visible():
            print("Role gate open. Selecting 'Khách tham quan' (guest)...")
            await page.locator('#rgChoices [data-role="guest"]').click()
            await page.wait_for_timeout(500)

        slide_names = [
            "step1-trangchu",
            "step2-bando",
            "step3-5khudisan",
            "step4-hosodisan",
            "step5-phong3d",
            "step6-ai5a",
            "step7-xuongsangtao",
            "step8-argallery",
            "step9-danhgia"
        ]

        for i, sid in enumerate(slide_names):
            print(f"Testing Slide {i+1}: {sid}...")
            await page.evaluate(f"window.goToSlide({i})")
            await page.wait_for_timeout(400)
            
            # Verify active slide ID
            active_id = await page.locator(".sah-slide.active-slide").get_attribute("id")
            assert active_id == sid, f"Expected {sid}, got {active_id}"

            # Verify Back button presence
            prev_btn = page.locator(f"#{sid} .sah-ppt-btn.sah-ppt-prev")
            if i > 0:
                is_prev_vis = await prev_btn.is_visible()
                assert is_prev_vis, f"Slide {i+1} Back button should be visible"

            # Verify Continue / Finish button presence
            next_btn = page.locator(f"#{sid} .sah-ppt-btn.sah-ppt-next:visible")
            assert await next_btn.is_visible(), f"Slide {i+1} Continue button should be visible"

            # Verify slide counter
            counter_txt = await page.locator(f"#{sid} .sah-ppt-slide-num").text_content()
            print(f"Slide {i+1} counter: {counter_txt.strip() if counter_txt else 'None'}")
            assert f"{i+1}" in counter_txt and "9" in counter_txt

            # Capture screenshot
            await page.screenshot(path=f"tools/slide_{i+1}_{sid}.png")
            print(f"  ✓ Captured tools/slide_{i+1}_{sid}.png")

        print("\nAll 9 student/guest slides successfully verified and captured!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
