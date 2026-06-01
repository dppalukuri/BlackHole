"""
Debug test: step-by-step Bayut hCaptcha solving with verbose output.
"""
import asyncio
import os
import sys
import traceback

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_SOLVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "captcha-solver")
if _SOLVER_PATH not in sys.path:
    sys.path.insert(0, _SOLVER_PATH)


async def main():
    print("=" * 60)
    print("BAYUT CAPTCHA DEBUG TEST")
    print("=" * 60)

    from stealth_browser import get_stealth_browser
    from captcha import detect_captcha, _click_checkbox, _extract_challenge_data, _find_challenge_frame

    sb = await get_stealth_browser()
    context = await sb.new_context(site_name="bayut_debug", headed=True)
    page = await context.new_page()

    # Move window on-screen
    try:
        cdp = await context.new_cdp_session(page)
        window = await cdp.send("Browser.getWindowForTarget")
        wid = window.get("windowId")
        if wid:
            await cdp.send("Browser.setWindowBounds", {
                "windowId": wid,
                "bounds": {"left": 100, "top": 100, "width": 1280, "height": 900, "windowState": "normal"}
            })
    except Exception:
        pass

    url = "https://www.bayut.com/to-rent/apartments/dubai/dubai-marina/"
    print(f"\n[1] Navigating to {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    await asyncio.sleep(3)

    print(f"    Current URL: {page.url}")

    # Detect CAPTCHA
    captcha = await detect_captcha(page)
    if not captcha:
        print("    No CAPTCHA! Page loaded clean.")
        await context.close()
        await sb.cleanup()
        return

    print(f"    CAPTCHA type: {captcha['type']}")
    print(f"    Sitekey: {captcha.get('sitekey')}")

    # Step 2: Click checkbox
    print(f"\n[2] Clicking hCaptcha checkbox...")
    clicked = await _click_checkbox(page, "hcaptcha")
    print(f"    Checkbox clicked: {clicked}")
    await asyncio.sleep(4)  # Wait for challenge to render

    # Take screenshot after checkbox click
    await page.screenshot(path=".sessions/debug_after_checkbox.png")
    print("    Screenshot: .sessions/debug_after_checkbox.png")

    # Step 3: Extract challenge data
    print(f"\n[3] Extracting challenge data...")
    challenge = await _extract_challenge_data(page, "hcaptcha")
    task = challenge.get("task", "")
    images = challenge.get("images", [])
    is_canvas = challenge.get("is_canvas", False)

    print(f"    Task text: '{task}'")
    print(f"    Number of images: {len(images)}")
    print(f"    Is canvas: {is_canvas}")

    if images:
        for i, img in enumerate(images):
            if img.startswith("data:"):
                print(f"    Image {i}: data URL ({len(img)} chars, starts: {img[:60]}...)")
            elif img.startswith("http"):
                print(f"    Image {i}: HTTP URL: {img[:120]}")
            else:
                print(f"    Image {i}: Unknown format ({img[:80]}...)")

    if not images:
        print("\n    !!! No images extracted. Checking challenge frame directly...")
        cf = _find_challenge_frame(page, "hcaptcha")
        if cf:
            print(f"    Challenge frame URL: {cf.url[:100]}")
            # Try to extract more info
            try:
                html_snippet = await cf.evaluate("""() => {
                    return document.body ? document.body.innerHTML.substring(0, 2000) : 'no body';
                }""")
                print(f"    Challenge frame HTML:\n{html_snippet[:1000]}")
            except Exception as e:
                print(f"    Could not read challenge frame: {e}")
        else:
            print("    No challenge frame found!")
        await context.close()
        await sb.cleanup()
        return

    # Step 4: Try solving
    print(f"\n[4] Attempting solve...")

    if len(images) == 1:
        print("    Single image - canvas challenge")
        img_data = images[0]

        # Check if it's HTTP URL (not data URL) - this might be the problem
        if img_data.startswith("http"):
            print("    !!! Image is HTTP URL, not data URL!")
            print("    Downloading image and converting to data URL...")
            import httpx
            import base64
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(img_data, timeout=10)
                    b64 = base64.b64encode(resp.content).decode()
                    content_type = resp.headers.get("content-type", "image/png")
                    img_data = f"data:{content_type};base64,{b64}"
                    print(f"    Converted to data URL ({len(img_data)} chars)")
            except Exception as e:
                print(f"    Failed to download: {e}")
                await context.close()
                await sb.cleanup()
                return

        # Try the solve_canvas_challenge
        try:
            from solver import solve_canvas_challenge
            print(f"    Calling solve_canvas_challenge(image, task='{task}')...")
            result = await asyncio.wait_for(
                solve_canvas_challenge(img_data, task),
                timeout=60
            )
            if result:
                print(f"    SUCCESS! Click at ({result['canvas_x']}, {result['canvas_y']})")
                print(f"    Canvas size: {result['canvas_width']}x{result['canvas_height']}")
                print(f"    Confidence: {result['confidence']:.3f}")
            else:
                print("    FAILED: solve_canvas_challenge returned None")
        except asyncio.TimeoutError:
            print("    TIMEOUT: Solver took too long (>60s)")
        except Exception as e:
            print(f"    ERROR: {e}")
            traceback.print_exc()
    else:
        print(f"    Grid challenge with {len(images)} images")
        try:
            from solver import solve_hcaptcha_challenge
            print(f"    Calling solve_hcaptcha_challenge(task='{task}', images[{len(images)}])...")
            result = await asyncio.wait_for(
                solve_hcaptcha_challenge(task, images, threshold=0.5),
                timeout=60
            )
            print(f"    Selections: {result.get('selections', [])}")
            print(f"    Details: {result.get('details', [])[:3]}")
        except asyncio.TimeoutError:
            print("    TIMEOUT: Solver took too long (>60s)")
        except Exception as e:
            print(f"    ERROR: {e}")
            traceback.print_exc()

    # Keep browser open to see result
    print("\n[5] Browser open for 15s for inspection...")
    await page.screenshot(path=".sessions/debug_final.png")
    await asyncio.sleep(15)

    await context.close()
    await sb.cleanup()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
