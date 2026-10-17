import asyncio
import sys
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"name": "Mobile Small (360x640)", "width": 360, "height": 640},
    {"name": "Mobile Standard (390x844)", "width": 390, "height": 844},
    {"name": "Tablet Portrait (768x1024)", "width": 768, "height": 1024},
    {"name": "Desktop Standard (1280x800)", "width": 1280, "height": 800},
    {"name": "Desktop Wide (1440x900)", "width": 1440, "height": 900},
]

SLIDE_IDS = [
    "step1-trangchu",
    "step2-bando",
    "step3-5khudisan",
    "step4-hosodisan",
    "step5-danhgia321",
    "step6-ai5a",
    "step7-hopchieu",
    "step8-xuongsangtao",
    "step9-banthuchanh",
    "step10-trainghiemar",
    "step11-phong3d",
    "step12-dashboard"
]

async def dismiss_role_gate(pg):
    rg = pg.locator("#roleGate")
    if await rg.is_visible():
        await pg.locator('#rgChoices [data-role="guest"]').click()
        await asyncio.sleep(0.2)

async def verify_all():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test 1: Content & DOM String Verification
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(f"PageError: {err}"))
        page.on("console", lambda msg: page_errors.append(f"Console {msg.type}: {msg.text}") if msg.type in ["error"] else None)
        
        response = await page.goto("http://localhost:8080/index.html", wait_until="domcontentloaded")
        if response.status != 200:
            errors.append(f"Failed to load index.html, HTTP {response.status}")
        await dismiss_role_gate(page)
            
        print("--- [PASS 1] VERIFYING 12-STEP CURRICULUM SEQUENCE & LABELS ---")
        
        # 0. Check Đơn vị nghiên cứu & Đối tượng
        research_unit = await page.locator('.sah-meta-item:first-of-type').inner_text()
        print(f"Đơn vị nghiên cứu text: '{research_unit.strip()}'")
        assert "Trường Trung học cơ sở Lê Quý Đôn, xã Lê Quý Đôn, tỉnh Hưng Yên" in research_unit, f"Unexpected research unit: {research_unit}"
        
        target_audience = await page.locator('.sah-meta-item:nth-of-type(2)').inner_text()
        print(f"Đối tượng text: '{target_audience.strip()}'")
        assert "Học sinh THCS Lê Quý Đôn, xã Lê Quý Đôn và giáo viên Mĩ thuật" in target_audience, f"Unexpected target audience: {target_audience}"

        # Check hero sub badge
        badge_sub = await page.locator('.sah-badge-sub').inner_text()
        print(f"Hero Sub Badge: '{badge_sub.strip()}'")
        assert "TỈNH HƯNG YÊN (THÁI BÌNH CŨ) • CHÂU THỔ SÔNG HỒNG" in badge_sub, f"Unexpected badge sub: {badge_sub}"

        # 1. Check all 12 Stepper pills exist in the correct sequence
        stepper_pills = await page.locator('.sah-stepper-track .sah-step-pill').count()
        assert stepper_pills == 12, f"Expected 12 stepper pills, found {stepper_pills}"
        print(f"  ✓ Exactly 12 Stepper pills present in sequence")

        # 2. Check key step titles and badges
        # Step 4: Hồ sơ 15 ảnh
        badge_step4 = await page.locator('#step4-hosodisan .sah-step-badge').inner_text()
        print(f"  ✓ Slide 4 Badge: '{badge_step4.strip()}'")
        assert "15 ẢNH" in badge_step4

        # Step 5: Đánh giá và Tự hoàn thiện 3-2-1
        badge_step5 = await page.locator('#step5-danhgia321 .sah-step-badge').inner_text()
        print(f"  ✓ Slide 5 Badge: '{badge_step5.strip()}'")
        assert "3-2-1" in badge_step5

        # Step 6: AI 5A
        badge_step6 = await page.locator('#step6-ai5a .sah-step-badge').inner_text()
        print(f"  ✓ Slide 6 Badge: '{badge_step6.strip()}'")
        assert "AI" in badge_step6

        # Step 7: Hộp Chiếu Sáng Tạo
        badge_step7 = await page.locator('#step7-hopchieu .sah-step-badge').inner_text()
        print(f"  ✓ Slide 7 Badge: '{badge_step7.strip()}'")
        assert "HỘP CHIẾU SÁNG TẠO" in badge_step7

        # Step 8: Xưởng phác thảo
        badge_step8 = await page.locator('#step8-xuongsangtao .sah-step-badge').inner_text()
        print(f"  ✓ Slide 8 Badge: '{badge_step8.strip()}'")
        assert "PHÁC THẢO" in badge_step8

        # Step 9: Bản thực hành
        badge_step9 = await page.locator('#step9-banthuchanh .sah-step-badge').inner_text()
        print(f"  ✓ Slide 9 Badge: '{badge_step9.strip()}'")
        assert "BẢN THỰC HÀNH" in badge_step9

        # Step 10: Trải nghiệm AR
        badge_step10 = await page.locator('#step10-trainghiemar .sah-step-badge').inner_text()
        print(f"  ✓ Slide 10 Badge: '{badge_step10.strip()}'")
        assert "AR" in badge_step10

        # Step 11: Phòng 3D
        badge_step11 = await page.locator('#step11-phong3d .sah-step-badge').inner_text()
        print(f"  ✓ Slide 11 Badge: '{badge_step11.strip()}'")
        assert "PHÒNG 3D" in badge_step11

        # Step 12: Dashboard GV
        badge_step12 = await page.locator('#step12-dashboard .sah-step-badge').inner_text()
        print(f"  ✓ Slide 12 Badge: '{badge_step12.strip()}'")
        assert "DASHBOARD" in badge_step12

        # 3. Check Roadmap Track on Slide 1 has 12 steps
        roadmap_count = await page.locator('.sah-roadmap-track .sah-roadmap-step').count()
        assert roadmap_count == 12, f"Expected 12 roadmap steps on Slide 1, found {roadmap_count}"
        print(f"  ✓ Slide 1 Roadmap Track contains all 12 sequential steps")

        # 4. Check Exhibits & Locations
        ex2_loc = await page.locator('.sah-exhibit-card:has(h3:has-text("Chùa Keo")) .sah-exhibit-loc').inner_text()
        assert "xã Vũ Tiên, tỉnh Hưng Yên (Vũ Thư - Thái Bình cũ) • Khởi dựng năm 1632" in ex2_loc
        print(f"  ✓ Exhibit 02 (Chùa Keo) verified")

        ex3_loc = await page.locator('.sah-exhibit-card:nth-of-type(3) .sah-exhibit-loc').inner_text()
        assert "xã Long Hưng, tỉnh Hưng Yên (Hưng Hà, tỉnh Thái Bình cũ)" in ex3_loc
        print(f"  ✓ Exhibit 03 (Đền Trần) verified")

        # 5. Check Slide 2 Map items
        map_keo = await page.locator('.sah-map-item:nth-of-type(2) p').inner_text()
        assert "xã Vũ Tiên (Vũ Thư cũ)" in map_keo
        map_dentran = await page.locator('.sah-map-item:nth-of-type(3) p').inner_text()
        assert "xã Long Hưng (Hưng Hà cũ)" in map_dentran
        print(f"  ✓ Slide 2 Map items verified")
        
        await context.close()
        
        print("\n--- [PASS 2] VERIFYING RESPONSIVENESS & OVERFLOW ACROSS VIEWPORTS ---")
        for vp in VIEWPORTS:
            ctx = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            p_vp = await ctx.new_page()
            await p_vp.goto("http://localhost:8080/index.html", wait_until="domcontentloaded")
            
            # Check horizontal overflow
            scroll_data = await p_vp.evaluate("""() => {
                return {
                    docScroll: document.documentElement.scrollWidth,
                    docClient: document.documentElement.clientWidth,
                    bodyScroll: document.body.scrollWidth,
                    bodyClient: document.body.clientWidth
                };
            }""")
            overflow = max(0, scroll_data['docScroll'] - scroll_data['docClient'])
            assert overflow == 0, f"Horizontal overflow of {overflow}px on {vp['name']}!"
            print(f"  ✓ {vp['name']}: No horizontal overflow ({scroll_data['docClient']}px width)")
            
            # Check Topnav positioning on mobile/tablet
            if vp["width"] <= 860:
                topnav_position = await p_vp.evaluate("""() => {
                    const nav = document.querySelector('.rm-topnav');
                    const comp = window.getComputedStyle(nav);
                    const rect = nav.getBoundingClientRect();
                    return { position: comp.position, height: rect.height, top: rect.top };
                }""")
                assert topnav_position["position"] == "relative", f"Expected relative topnav on mobile, got {topnav_position['position']}"
            
            await ctx.close()
            
        print("\n--- [PASS 3] INTERACTIVE 12-SLIDE SEQUENTIAL FLOW VERIFICATION ---")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        p_flow = await ctx.new_page()
        console_msgs = []
        p_flow.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
        await p_flow.goto("http://localhost:8080/index.html", wait_until="domcontentloaded")
        await dismiss_role_gate(p_flow)
        
        # Test slide transitions from 0 to 11 (1 to 12)
        for slide_idx in range(12):
            cur_slide = await p_flow.evaluate("() => window.currentSlideIndex")
            assert cur_slide == slide_idx, f"Expected slide {slide_idx}, got {cur_slide}"
            
            # Check that the corresponding slide element is active and visible
            expected_id = SLIDE_IDS[slide_idx]
            is_vis = await p_flow.locator(f"#{expected_id}").is_visible()
            assert is_vis, f"Slide #{expected_id} is not visible at index {slide_idx}!"
            
            if slide_idx < 11:
                await p_flow.keyboard.press("ArrowRight")
                await asyncio.sleep(0.08)
                
        final_slide = await p_flow.evaluate("() => window.currentSlideIndex")
        assert final_slide == 11, f"Expected final slide 11 (step 12), got {final_slide}"
        print("  ✓ Navigated smoothly through all 12 slides via keyboard ArrowRight")
        
        # Check active slide title in slide 12
        step12_visible = await p_flow.locator('#step12-dashboard').is_visible()
        assert step12_visible, "Step 12: Dashboard GV is not visible!"
        print("  ✓ Step 12: Dashboard GV is active and fully visible")

        # Test Step 7: Hộp Chiếu Sáng Tạo interactivity
        await p_flow.evaluate("() => goToSlide(6)")
        await asyncio.sleep(0.1)
        step7_vis = await p_flow.locator('#step7-hopchieu').is_visible()
        assert step7_vis, "Step 7: Hộp Chiếu Sáng Tạo not visible!"
        
        # Test lighting mood switch
        await p_flow.locator('.sah-lb-mood-btn[data-mood="demtrang"]').click()
        await asyncio.sleep(0.05)
        box_mood = await p_flow.locator('#sahLbBox').get_attribute('data-mood')
        assert box_mood == 'demtrang', f"Expected data-mood='demtrang', got '{box_mood}'"
        print("  ✓ Step 7: Lightbox mood switch to 'demtrang' verified")

        # Test save preset button
        await p_flow.locator('.sah-lb-btn-save').click()
        await asyncio.sleep(0.05)
        toast_vis = await p_flow.locator('#sahLbSaveToast').is_visible()
        assert toast_vis, "Lightbox save toast did not appear"
        print("  ✓ Step 7: Lightbox preset saved successfully with toast notification")

        # Test Exhibit image switcher in Slide 0 (Landing Page Exhibit Showcase)
        await p_flow.evaluate("() => goToSlide(0)")
        await asyncio.sleep(0.1)
        for code in ["01", "02", "03", "04", "05"]:
            thumbs = await p_flow.locator(f"#thumbList{code} img").count()
            assert thumbs >= 3, f"Exhibit {code} should have at least 3 thumbs, found {thumbs}"
            second_thumb = p_flow.locator(f"#thumbList{code} img:nth-of-type(2)")
            await second_thumb.click()
            await asyncio.sleep(0.05)
            main_src = await p_flow.locator(f"#exhibitImg{code}").get_attribute("src")
            thumb_src = await second_thumb.get_attribute("src")
            assert thumb_src in main_src or main_src.endswith(thumb_src), f"Image switcher failed for Exhibit {code}: {main_src} != {thumb_src}"
            print(f"  ✓ Exhibit {code} thumbnail click switcher verified")
            
        # Check console errors (ignoring video preload connection reset/aborted/socket disconnect)
        bad_logs = [m for m in console_msgs if any(err_word in m.lower() for err_word in ["error", "uncaught"]) and "err_connection_reset" not in m.lower() and "err_aborted" not in m.lower() and "err_socket_not_connected" not in m.lower()]
        assert len(bad_logs) == 0, f"Found console errors: {bad_logs}"
        print(f"  ✓ Zero console errors detected during full interaction (Total logs evaluated: {len(console_msgs)})")
        
        print("\n--- [PASS 4] HOVER PREVIEWS & THEMATIC SITE BACKGROUNDS ACROSS 12 SLIDES ---")
        await p_flow.evaluate("() => { window.scrollTo(0, 0); goToSlide(0); }")
        await asyncio.sleep(0.2)
        
        # 1. Hover on Stepper Pill 3
        pill3 = p_flow.locator('.sah-step-pill[data-step="3"]')
        await pill3.hover()
        await asyncio.sleep(0.2)
        
        preview_vis = await p_flow.locator('#sahGlobalHoverPreview').evaluate("el => el.classList.contains('visible')")
        assert preview_vis, "Global hover preview modal is not visible on hovering step pill 3!"
        preview_img = await p_flow.locator('#sahGhpImg').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in preview_img
        print(f"  ✓ Stepper Pill 3 hover preview verified")
        
        # 2. Verify thematic site background across ALL 12 slides (data-active-slide)
        for idx, sid in enumerate(SLIDE_IDS):
            await p_flow.evaluate(f"() => goToSlide({idx})")
            await asyncio.sleep(0.05)
            active_attr = await p_flow.evaluate("() => document.body.getAttribute('data-active-slide')")
            assert active_attr == sid, f"Slide {idx} expected body[data-active-slide='{sid}'], got '{active_attr}'"
            print(f"  ✓ Slide {idx + 1:02d} ({sid}): Dynamic thematic background active")

        # Capture desktop screenshot of Step 7: Hộp Chiếu Sáng Tạo
        await p_flow.evaluate("() => goToSlide(6)")
        await asyncio.sleep(0.3)
        await p_flow.screenshot(path="tools/screenshot_step7_lightbox.png")
        print("  ✓ Captured tools/screenshot_step7_lightbox.png")

        await ctx.close()
        await browser.close()

    print("\n=======================================================")
    print(">>> ALL 4 VERIFICATION PASSES COMPLETED 100% GREEN! <<<")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(verify_all())
