"""Debug script to inspect actual Google Maps DOM structure."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stealth_browser import StealthBrowser
from urllib.parse import quote_plus


async def main():
    browser = StealthBrowser()
    ctx = await browser.new_context(session_name="debug")
    page = await ctx.new_page()

    try:
        url = f"https://www.google.com/maps/search/{quote_plus('restaurants Dubai Marina')}"
        print(f"Loading: {url}\n")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Dismiss consent
        try:
            btn = page.locator('button:has-text("Accept all"), button:has-text("Reject all")').first
            await btn.click(timeout=3000)
            await asyncio.sleep(1)
        except:
            pass

        # Wait for feed
        await page.wait_for_selector('div[role="feed"]', timeout=10000)
        await asyncio.sleep(2)

        # Debug 1: What does a listing card look like?
        print("=" * 60)
        print("LISTING CARDS")
        print("=" * 60)

        items = page.locator('div[role="feed"] > div > div > a[href*="/maps/place/"]')
        count = await items.count()
        print(f"Found {count} card links\n")

        if count == 0:
            # Try broader selector
            items = page.locator('div[role="feed"] a[href*="/maps/place/"]')
            count = await items.count()
            print(f"Broader selector found {count} links\n")

        for i in range(min(count, 2)):
            item = items.nth(i)
            aria = await item.get_attribute("aria-label") or "N/A"
            text = await item.inner_text()
            print(f"--- Card {i+1} ---")
            print(f"aria-label: {aria}")
            print(f"inner_text:\n{text}")
            print()

        # Debug 2: What does the detail page look like?
        print("\n" + "=" * 60)
        print("DETAIL PAGE")
        print("=" * 60)

        if count > 0:
            first = items.first
            href = await first.get_attribute("href")
            await page.goto(href, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Try h1
            h1s = page.locator("h1")
            h1_count = await h1s.count()
            print(f"\nh1 elements: {h1_count}")
            for j in range(h1_count):
                txt = await h1s.nth(j).inner_text()
                cls = await h1s.nth(j).get_attribute("class") or ""
                print(f"  h1[{j}]: text='{txt}', class='{cls}'")

            # Rating
            rating_els = page.locator('div[role="img"][aria-label*="star"], span[role="img"][aria-label*="star"]')
            rc = await rating_els.count()
            print(f"\nRating elements: {rc}")
            for j in range(rc):
                lbl = await rating_els.nth(j).get_attribute("aria-label")
                print(f"  [{j}]: {lbl}")

            # Info buttons
            info_btns = page.locator('button[data-item-id], a[data-item-id]')
            ic = await info_btns.count()
            print(f"\nInfo buttons (data-item-id): {ic}")
            for j in range(min(ic, 10)):
                did = await info_btns.nth(j).get_attribute("data-item-id") or ""
                aria = await info_btns.nth(j).get_attribute("aria-label") or ""
                try:
                    txt = (await info_btns.nth(j).inner_text()).strip()[:60]
                except:
                    txt = "(encoding error)"
                print(f"  [{j}]: id='{did}', aria='{aria[:50].encode('ascii', 'replace').decode()}'")
                print(f"         text='{txt.encode('ascii', 'replace').decode()}'")


            # Category button
            cat_btn = page.locator('button[jsaction*="category"]')
            cc = await cat_btn.count()
            print(f"\nCategory buttons: {cc}")
            if cc > 0:
                print(f"  text: {await cat_btn.first.inner_text()}")

            # Try broader category selector
            cat_link = page.locator('button[class*="DkEaL"], a[class*="DkEaL"]')
            cc2 = await cat_link.count()
            print(f"Category DkEaL: {cc2}")

    finally:
        await page.close()
        await ctx.close()
        await browser.cleanup()


asyncio.run(main())
