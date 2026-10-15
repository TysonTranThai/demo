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
            
        print("--- [PASS 1] VERIFYING CONTENT & TEXT STRINGS ---")
        
        # 0. Check Đơn vị nghiên cứu & Đối tượng
        research_unit = await page.locator('.sah-meta-item:first-of-type').inner_text()
        print(f"Đơn vị nghiên cứu text: '{research_unit.strip()}'")
        assert "Trường Trung học cơ sở Lê Quý Đôn, xã Lê Quý Đôn, tỉnh Hưng Yên" in research_unit, f"Unexpected research unit: {research_unit}"
        
        target_audience = await page.locator('.sah-meta-item:nth-of-type(2)').inner_text()
        print(f"Đối tượng text: '{target_audience.strip()}'")
        assert "Học sinh THCS Lê Quý Đôn, xã Lê Quý Đôn và giáo viên Mĩ thuật" in target_audience, f"Unexpected target audience: {target_audience}"

        # 1. Check "Đánh giá và tự hoàn thiện"
        topnav_step9 = await page.locator('.rm-topnav-link[href="#step9-danhgia"]').inner_text()
        print(f"Topnav Step 9 text: '{topnav_step9.strip()}'")
        assert "Đánh giá và tự hoàn thiện" in topnav_step9, f"Unexpected topnav text: {topnav_step9}"
        
        stepper_step9 = await page.locator('.sah-step-pill[data-step="9"] .sah-step-txt').inner_text()
        print(f"Stepper Step 9 text: '{stepper_step9.strip()}'")
        assert "Đánh giá và tự hoàn thiện" in stepper_step9, f"Unexpected stepper text: {stepper_step9}"
        
        badge_step9 = await page.locator('#step9-danhgia .sah-step-badge').inner_text()
        print(f"Slide 9 Badge: '{badge_step9.strip()}'")
        assert "ĐÁNH GIÁ VÀ TỰ HOÀN THIỆN" in badge_step9, f"Unexpected badge text: {badge_step9}"
        
        # Check roadmap step 9
        roadmap_step9 = await page.locator('.sah-roadmap-step:has(.sah-rm-num:text-is("9"))').inner_text()
        print(f"Roadmap Step 9 text: '{roadmap_step9.strip()}'")
        assert "Đánh giá và tự hoàn thiện" in roadmap_step9, f"Unexpected roadmap text: {roadmap_step9}"
        
        # 2. Check Exhibit 02 (Chùa Keo)
        ex2_loc = await page.locator('.sah-exhibit-card:has(h3:has-text("Chùa Keo")) .sah-exhibit-loc').inner_text()
        print(f"Exhibit 02 Location: '{ex2_loc.strip()}'")
        assert "xã Vũ Tiên, tỉnh Hưng Yên (Vũ Thư - Thái Bình cũ) • Khởi dựng năm 1632" in ex2_loc, f"Unexpected Ex2 loc: {ex2_loc}"
        
        # 3. Check Exhibit 03 (Đền Trần)
        ex3_title = await page.locator('.sah-exhibit-card:nth-of-type(3) h3').inner_text()
        print(f"Exhibit 03 Title: '{ex3_title.strip()}'")
        assert "Đền Trần Long Hưng" in ex3_title, f"Unexpected Ex3 title: {ex3_title}"
        ex3_loc = await page.locator('.sah-exhibit-card:nth-of-type(3) .sah-exhibit-loc').inner_text()
        print(f"Exhibit 03 Location: '{ex3_loc.strip()}'")
        assert "xã Long Hưng, tỉnh Hưng Yên (Hưng Hà, tỉnh Thái Bình cũ)" in ex3_loc, f"Unexpected Ex3 loc: {ex3_loc}"
        
        # 4. Check Exhibit 04 (Lê Quý Đôn)
        ex4_loc = await page.locator('.sah-exhibit-card:nth-of-type(4) .sah-exhibit-loc').inner_text()
        print(f"Exhibit 04 Location: '{ex4_loc.strip()}'")
        assert "xã Lê Quý Đôn, tỉnh Hưng Yên (Hưng Hà, tỉnh Thái Bình cũ)" in ex4_loc, f"Unexpected Ex4 loc: {ex4_loc}"
        
        # 5. Check Exhibit 05 (Đồng Xâm)
        ex5_loc = await page.locator('.sah-exhibit-card:nth-of-type(5) .sah-exhibit-loc').inner_text()
        print(f"Exhibit 05 Location: '{ex5_loc.strip()}'")
        assert "xã Trà Giang, tỉnh Hưng Yên (Kiến Xương, tỉnh Thái Bình cũ)" in ex5_loc, f"Unexpected Ex5 loc: {ex5_loc}"
        
        # 6. Check Map items on Slide 2
        map_keo = await page.locator('.sah-map-item:nth-of-type(2) p').inner_text()
        print(f"Slide 2 Chùa Keo map item: '{map_keo.strip()}'")
        assert "xã Vũ Tiên (Vũ Thư cũ)" in map_keo
        
        map_dentran = await page.locator('.sah-map-item:nth-of-type(3) p').inner_text()
        print(f"Slide 2 Đền Trần map item: '{map_dentran.strip()}'")
        assert "xã Long Hưng (Hưng Hà cũ)" in map_dentran
        
        map_lequydon = await page.locator('.sah-map-item:nth-of-type(4) p').inner_text()
        print(f"Slide 2 Lê Quý Đôn map item: '{map_lequydon.strip()}'")
        assert "xã Lê Quý Đôn (Hưng Hà cũ)" in map_lequydon
        
        map_dongxam = await page.locator('.sah-map-item:nth-of-type(5) p').inner_text()
        print(f"Slide 2 Đồng Xâm map item: '{map_dongxam.strip()}'")
        assert "xã Trà Giang (Kiến Xương cũ)" in map_dongxam
        
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
                print(f"    Mobile topnav mode: {topnav_position}")
                assert topnav_position["position"] == "relative", f"Expected relative topnav on mobile, got {topnav_position['position']}"
            
            # Check roadmap step 9 bounding box and text clipping
            # Navigate to slide 1 (or check roadmap container)
            step9_box = await p_vp.evaluate("""() => {
                const step = document.querySelector('.sah-roadmap-step[onclick*="goToSlide(8)"]');
                if (!step) return null;
                const rect = step.getBoundingClientRect();
                const b = step.querySelector('b');
                const bRect = b ? b.getBoundingClientRect() : null;
                return {
                    stepWidth: rect.width,
                    bWidth: bRect ? bRect.width : 0,
                    overflows: bRect ? (bRect.width > rect.width) : false
                };
            }""")
            if step9_box:
                assert not step9_box["overflows"], f"Step 9 text overflows its card on {vp['name']}! {step9_box}"
                print(f"    Step 9 roadmap card width: {step9_box['stepWidth']:.1f}px, text width: {step9_box['bWidth']:.1f}px (Fits cleanly)")
            
            await ctx.close()
            
        print("\n--- [PASS 3] INTERACTIVE & SLIDE FLOW VERIFICATION ---")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        p_flow = await ctx.new_page()
        console_msgs = []
        p_flow.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
        await p_flow.goto("http://localhost:8080/index.html", wait_until="domcontentloaded")
        await dismiss_role_gate(p_flow)
        
        # Test slide transitions 1 to 9
        for slide_idx in range(9):
            cur_slide = await p_flow.evaluate("() => window.currentSlideIndex")
            assert cur_slide == slide_idx, f"Expected slide {slide_idx}, got {cur_slide}"
            if slide_idx < 8:
                await p_flow.keyboard.press("ArrowRight")
                await asyncio.sleep(0.1)
                
        final_slide = await p_flow.evaluate("() => window.currentSlideIndex")
        assert final_slide == 8, f"Expected slide 8 (step 9), got {final_slide}"
        print("  ✓ Navigated smoothly through all 9 slides")
        
        # Check active slide title in slide 9
        step9_visible = await p_flow.locator('#step9-danhgia').is_visible()
        assert step9_visible, "Step 9 slide is not visible!"
        print("  ✓ Step 9: Đánh giá và tự hoàn thiện is active and fully visible")
        
        # Test Exhibit image switcher in Slide 0 (Landing Page Exhibit Showcase)
        await p_flow.evaluate("() => goToSlide(0)")
        await asyncio.sleep(0.1)
        for code in ["01", "02", "03", "04", "05"]:
            thumbs = await p_flow.locator(f"#thumbList{code} img").count()
            assert thumbs >= 3, f"Exhibit {code} should have at least 3 thumbs, found {thumbs}"
            # Click second thumbnail
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
        
        print("\n--- [PASS 4] HOVER PREVIEWS (BUTTON #3 & HERITAGE) & THEMATIC SITE BACKGROUNDS ---")
        await p_flow.evaluate("() => { window.scrollTo(0, 0); goToSlide(0); }")
        await asyncio.sleep(0.2)
        
        # 1. Hover on Stepper Pill 3 (Bước 3: 5 Kiệt Tác Di Sản)
        pill3 = p_flow.locator('.sah-step-pill[data-step="3"]')
        await pill3.hover()
        await asyncio.sleep(0.2)
        
        preview_vis = await p_flow.locator('#sahGlobalHoverPreview').evaluate("el => el.classList.contains('visible')")
        assert preview_vis, "Global hover preview modal is not visible on hovering step pill 3!"
        preview_img = await p_flow.locator('#sahGhpImg').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in preview_img, f"Expected 066_Nghi_mon_den_Tran.jpeg, got {preview_img}"
        preview_title = await p_flow.locator('#sahGhpTitle').inner_text()
        print(f"  ✓ Stepper Pill 3 hover preview: '{preview_title.strip()}', img: '{preview_img}'")
        
        # 2. Hover on Roadmap Step 3
        roadmap3 = p_flow.locator('.sah-roadmap-step:has(.sah-rm-num:text-is("3"))')
        await roadmap3.hover()
        await asyncio.sleep(0.15)
        preview_img = await p_flow.locator('#sahGhpImg').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in preview_img, f"Expected 066_Nghi_mon_den_Tran.jpeg on roadmap step 3, got {preview_img}"
        print(f"  ✓ Roadmap Step 3 hover preview displayed image: '{preview_img}'")

        # 3. Slide 2: Map Item 3 & SVG Pin 3 (Đền Trần Long Hưng)
        await p_flow.evaluate("() => goToSlide(1)")
        await asyncio.sleep(0.5)
        
        # Check thumbnail in map item 3
        thumb3_src = await p_flow.locator('.sah-map-item:nth-of-type(3) .sah-map-thumb img').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in thumb3_src, f"Map item 3 thumbnail missing: {thumb3_src}"
        print(f"  ✓ Slide 2 Map Item 3 thumbnail verified: '{thumb3_src}'")
        
        map_item3 = p_flow.locator('.sah-map-item:nth-of-type(3)')
        await map_item3.hover()
        await asyncio.sleep(0.15)
        preview_img = await p_flow.locator('#sahGhpImg').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in preview_img
        print(f"  ✓ Map Item 3 hover preview displayed image: '{preview_img}'")
        
        pin3 = p_flow.locator('#pin-dentran')
        await pin3.hover()
        await asyncio.sleep(0.15)
        preview_img = await p_flow.locator('#sahGhpImg').get_attribute("src")
        assert "066_Nghi_mon_den_Tran.jpeg" in preview_img
        print(f"  ✓ SVG Pin 3 (#pin-dentran) hover preview verified with image: '{preview_img}'")
        
        # 4. Verify thematic site background across all slides (data-active-slide)
        slide_ids = [
            "step1-trangchu", "step2-bando", "step3-5khudisan", "step4-hosodisan",
            "step5-phong3d", "step6-ai5a", "step7-xuongsangtao", "step8-argallery", "step9-danhgia"
        ]
        for idx, sid in enumerate(slide_ids):
            await p_flow.evaluate(f"() => goToSlide({idx})")
            await asyncio.sleep(0.05)
            active_attr = await p_flow.evaluate("() => document.body.getAttribute('data-active-slide')")
            assert active_attr == sid, f"Slide {idx} expected body[data-active-slide='{sid}'], got '{active_attr}'"
            print(f"  ✓ Slide {idx + 1} ({sid}): Dynamic thematic background attribute active")

        # Capture desktop screenshot of Step 3 hover preview
        await p_flow.evaluate("() => goToSlide(0)")
        await pill3.hover()
        await asyncio.sleep(0.2)
        await p_flow.screenshot(path="tools/screenshot_hover_preview.png")
        print("  ✓ Captured tools/screenshot_hover_preview.png")

        await ctx.close()
        await browser.close()

    print("\n==========================================")
    print(">>> ALL VERIFICATION PASSES COMPLETED 100% SUCCESSFULLY! <<<")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(verify_all())
