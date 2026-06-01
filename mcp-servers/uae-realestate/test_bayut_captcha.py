"""
Test script for Bayut CAPTCHA detection and solving.
Run: python test_bayut_captcha.py
"""
import asyncio
import os
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add captcha-solver to path
_SOLVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "captcha-solver")
if _SOLVER_PATH not in sys.path:
    sys.path.insert(0, _SOLVER_PATH)


async def main():
    print("=" * 60)
    print("BAYUT CAPTCHA TEST")
    print("=" * 60)

    # Check available keys
    gemini = os.environ.get("GEMINI_API_KEY", "")
    anthropic = os.environ.get("ANTHROPIC_API_KEY", "")
    capsolver = os.environ.get("CAPSOLVER_API_KEY", "")
    print(f"\nAPI Keys:")
    print(f"  GEMINI_API_KEY:    {'SET' if gemini else 'NOT SET'}")
    print(f"  ANTHROPIC_API_KEY: {'SET' if anthropic else 'NOT SET'}")
    print(f"  CAPSOLVER_API_KEY: {'SET' if capsolver else 'NOT SET'}")

    if not gemini and not anthropic and not capsolver:
        print("\n⚠ WARNING: No API keys set. CAPTCHA solving will rely on CLIP only.")
        print("  For best results, set GEMINI_API_KEY (free at aistudio.google.com)")
        print("  Example: export GEMINI_API_KEY=AIza...")

    # Import after path setup
    from stealth_browser import get_stealth_browser
    from captcha import detect_captcha, handle_captcha_if_present

    sb = await get_stealth_browser()

    # Step 1: Open Bayut in headed mode so we can see what happens
    print("\n[1] Opening Bayut in HEADED mode...")
    context = await sb.new_context(site_name="bayut_test", headed=True)
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
    except Exception as e:
        print(f"  (Could not reposition window: {e})")

    url = "https://www.bayut.com/to-rent/apartments/dubai/dubai-marina/"
    print(f"  Navigating to: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    await asyncio.sleep(3)

    # Step 2: Check current URL and detect CAPTCHA
    print(f"\n[2] Current URL: {page.url}")
    captcha_in_url = "captcha" in page.url.lower()
    print(f"  CAPTCHA in URL: {captcha_in_url}")

    captcha_info = await detect_captcha(page)
    if captcha_info:
        print(f"\n  CAPTCHA DETECTED!")
        print(f"    Type:    {captcha_info.get('type', 'unknown')}")
        print(f"    Sitekey: {captcha_info.get('sitekey', 'none')}")
        print(f"    URL:     {captcha_info.get('url', '')}")
    else:
        print(f"\n  No CAPTCHA detected on page!")
        if not captcha_in_url:
            print("  Page loaded successfully without CAPTCHA!")

            # Try to see if there are property listings
            count = await page.evaluate("""() => {
                return document.querySelectorAll('article').length;
            }""")
            print(f"  Property listings found: {count}")

            # Take screenshot for reference
            await page.screenshot(path=".sessions/bayut_test_success.png")
            print("  Screenshot saved to .sessions/bayut_test_success.png")
            await context.close()
            await sb.cleanup()
            return

    # Step 3: Take screenshot of the CAPTCHA page
    await page.screenshot(path=".sessions/bayut_test_captcha.png")
    print("  Screenshot saved to .sessions/bayut_test_captcha.png")

    # Step 4: Dump page info for debugging
    print("\n[3] Page analysis:")
    page_info = await page.evaluate("""() => {
        const info = {
            title: document.title,
            frames: [],
            scripts: [],
            captcha_elements: [],
        };

        // List all iframes
        for (const f of document.querySelectorAll('iframe')) {
            info.frames.push(f.src || '(no src)');
        }

        // Look for CAPTCHA-related scripts
        for (const s of document.querySelectorAll('script[src]')) {
            const src = s.getAttribute('src') || '';
            if (src.includes('captcha') || src.includes('hcaptcha') || src.includes('recaptcha') || src.includes('challenge')) {
                info.scripts.push(src);
            }
        }

        // Any elements with captcha-related classes/ids
        const allEls = document.querySelectorAll('[class*="captcha"], [id*="captcha"], [data-sitekey], .h-captcha, .g-recaptcha');
        for (const el of allEls) {
            info.captcha_elements.push({
                tag: el.tagName,
                id: el.id,
                class: el.className,
                sitekey: el.getAttribute('data-sitekey'),
            });
        }

        return info;
    }""")

    print(f"  Title: {page_info.get('title', '')}")
    print(f"  Frames ({len(page_info.get('frames', []))}):")
    for f in page_info.get("frames", []):
        print(f"    - {f}")
    print(f"  CAPTCHA scripts:")
    for s in page_info.get("scripts", []):
        print(f"    - {s}")
    print(f"  CAPTCHA elements:")
    for el in page_info.get("captcha_elements", []):
        print(f"    - <{el['tag']}> id={el['id']} class={el['class'][:60]} sitekey={el['sitekey']}")

    # Also check iframes from Playwright's perspective
    print(f"\n  Playwright frames ({len(page.frames)}):")
    for f in page.frames:
        print(f"    - {f.url[:100]}")

    # Step 5: Attempt CAPTCHA solving
    print("\n[4] Attempting CAPTCHA solve...")
    solved = await handle_captcha_if_present(page, max_retries=3)

    if solved:
        print("\n  ✓ CAPTCHA SOLVED!")
        print(f"  Current URL: {page.url}")

        # Save session
        await sb.save_session(context)
        print("  Session saved for future use.")

        # Check for listings
        await asyncio.sleep(2)
        count = await page.evaluate("() => document.querySelectorAll('article').length")
        print(f"  Property listings found: {count}")
        await page.screenshot(path=".sessions/bayut_test_solved.png")
        print("  Screenshot saved to .sessions/bayut_test_solved.png")
    else:
        print("\n  ✗ CAPTCHA NOT SOLVED")
        print(f"  Current URL: {page.url}")
        await page.screenshot(path=".sessions/bayut_test_failed.png")
        print("  Screenshot saved to .sessions/bayut_test_failed.png")

        # Keep browser open for manual inspection
        print("\n  Browser staying open for 30s for manual inspection...")
        print("  (You can manually solve the CAPTCHA in the browser window)")
        for i in range(30):
            await asyncio.sleep(1)
            if "captcha" not in page.url.lower():
                print(f"\n  ✓ CAPTCHA solved manually! URL: {page.url}")
                await sb.save_session(context)
                print("  Session saved.")
                break

    await context.close()
    await sb.cleanup()
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
