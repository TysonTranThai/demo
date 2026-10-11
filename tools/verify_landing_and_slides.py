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

        # 1. Verify Slide 1 (Landing Page)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Initial active slide: {active_slide}")
        assert active_slide == "step1-trangchu", f"Expected step1-trangchu, got {active_slide}"

        # Check landing page elements
        hero_title = await page.locator(".sah-landing-hero h1").text_content()
        print(f"Hero Title: {hero_title.strip() if hero_title else 'None'}")
        
        pillars_count = await page.locator(".sah-pillar-card").count()
        print(f"Pillars count: {pillars_count}")
        assert pillars_count == 4, f"Expected 4 pillars, got {pillars_count}"

        roadmap_items = await page.locator(".sah-roadmap-step").count()
        print(f"Roadmap items count: {roadmap_items}")
        assert roadmap_items == 9, f"Expected 9 roadmap items, got {roadmap_items}"

        # Check role default (guest/student)
        is_teacher_link_visible = await page.locator("a[href='#step-dashboard']").is_visible()
        print(f"Is teacher link visible (default/guest): {is_teacher_link_visible}")
        assert not is_teacher_link_visible, "Teacher link should NOT be visible for guest"

        slide_counter = await page.locator(".active-slide .sah-ppt-slide-num").text_content()
        print(f"Slide counter on slide 1: {slide_counter.strip() if slide_counter else 'None'}")
        assert "1" in slide_counter and "9" in slide_counter, f"Expected 1 / 9 in counter, got {slide_counter}"

        # Capture Slide 1 screenshot
        await page.screenshot(path="tools/screenshot_slide1_landing.png")
        print("Captured tools/screenshot_slide1_landing.png")

        # 2. Advance to Slide 2 using Continue button
        print("Clicking Continue button on Slide 1...")
        await page.locator(".active-slide .sah-ppt-btn.sah-ppt-next").click()
        await page.wait_for_timeout(500)

        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide after continue: {active_slide}")
        assert active_slide == "step2-bando", f"Expected step2-bando, got {active_slide}"

        slide_counter = await page.locator(".active-slide .sah-ppt-slide-num").text_content()
        print(f"Slide counter on slide 2: {slide_counter.strip() if slide_counter else 'None'}")
        assert "2" in slide_counter and "9" in slide_counter, f"Expected 2 / 9 in counter, got {slide_counter}"

        # Check that Slide 1 is not displayed (only step2-bando is visible)
        intro_visible = await page.locator("#step1-trangchu").is_visible()
        map_visible = await page.locator("#step2-bando").is_visible()
        print(f"Slide 1 visible: {intro_visible}, Slide 2 visible: {map_visible}")
        assert not intro_visible, "Slide 1 should be hidden"
        assert map_visible, "Slide 2 should be visible"

        await page.screenshot(path="tools/screenshot_slide2_map.png")
        print("Captured tools/screenshot_slide2_map.png")

        # 3. Test Back button: goes back to Slide 1
        print("Testing Back button...")
        await page.locator(".active-slide .sah-ppt-btn.sah-ppt-prev").click()
        await page.wait_for_timeout(500)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide after back: {active_slide}")
        assert active_slide == "step1-trangchu", f"Expected step1-trangchu, got {active_slide}"

        # 4. Test Keyboard Navigation (ArrowRight to advance, ArrowLeft to go back)
        print("Testing Keyboard ArrowRight navigation...")
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(500)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide after ArrowRight: {active_slide}")
        assert active_slide == "step2-bando", f"Expected step2-bando, got {active_slide}"

        print("Testing Keyboard ArrowLeft navigation...")
        await page.keyboard.press("ArrowLeft")
        await page.wait_for_timeout(500)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide after ArrowLeft: {active_slide}")
        assert active_slide == "step1-trangchu", f"Expected step1-trangchu, got {active_slide}"

        # 5. Advance to Slide 3 (5 Khu di sản)
        await page.keyboard.press("ArrowRight") # to map
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowRight") # to 5 khu di san
        await page.wait_for_timeout(500)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide after 2x ArrowRight: {active_slide}")
        assert active_slide == "step3-5khudisan", f"Expected step3-5khudisan, got {active_slide}"
        await page.screenshot(path="tools/screenshot_slide3_heritages.png")
        print("Captured tools/screenshot_slide3_heritages.png")

        # 6. Test Teacher Role Guard
        print("\nTesting Teacher Role Guard...")
        # Set role to teacher in localStorage and trigger visibility update
        await page.evaluate("""() => {
            localStorage.setItem('rm_role', 'teacher');
            document.body.classList.add('role-teacher');
            if (window.updateTeacherVisibility) window.updateTeacherVisibility();
        }""")
        await page.wait_for_timeout(500)

        # Check teacher elements are now visible
        is_teacher_link_visible = await page.locator("a[href='#step-dashboard']").is_visible()
        print(f"Is teacher link visible (as teacher): {is_teacher_link_visible}")
        assert is_teacher_link_visible, "Teacher link should be visible when role is teacher"

        slide_counter = await page.locator(".active-slide .sah-ppt-slide-num").text_content()
        print(f"Slide counter as teacher: {slide_counter.strip() if slide_counter else 'None'}")
        assert "10" in slide_counter, f"Expected 10 total slides for teacher, got {slide_counter}"

        # Go to Dashboard slide (Slide 10)
        await page.evaluate("window.goToSlide(9)") # 0-indexed slide 9 is 10th slide
        await page.wait_for_timeout(500)
        active_slide = await page.locator(".sah-slide.active-slide").get_attribute("id")
        print(f"Active slide at slide 10: {active_slide}")
        assert active_slide == "step-dashboard", f"Expected step-dashboard, got {active_slide}"
        await page.screenshot(path="tools/screenshot_slide10_teacher_dashboard.png")
        print("Captured tools/screenshot_slide10_teacher_dashboard.png")

        # Now switch back to student role
        print("Switching back to student role...")
        await page.evaluate("""() => {
            localStorage.setItem('rm_role', 'student');
            document.body.classList.remove('role-teacher');
            if (window.updateTeacherVisibility) window.updateTeacherVisibility();
        }""")
        await page.wait_for_timeout(500)

        is_teacher_link_visible = await page.locator("a[href='#step-dashboard']").is_visible()
        print(f"Is teacher link visible after switching to student: {is_teacher_link_visible}")
        assert not is_teacher_link_visible, "Teacher link should NOT be visible for student"

        # 7. Test Slide Mode Toggle (switch to Scroll Mode, then back)
        print("\nTesting Slide Mode toggle...")
        toggle_btn = page.locator("#btnViewToggle")
        await toggle_btn.click()
        await page.wait_for_timeout(500)
        is_slide_mode = await page.evaluate("document.body.classList.contains('slide-mode')")
        print(f"Is in slide mode after toggle: {is_slide_mode}")
        assert not is_slide_mode, "Should be in scroll mode"

        # Toggle back
        await toggle_btn.click()
        await page.wait_for_timeout(500)
        is_slide_mode = await page.evaluate("document.body.classList.contains('slide-mode')")
        print(f"Is in slide mode after second toggle: {is_slide_mode}")
        assert is_slide_mode, "Should be back in slide mode"

        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
