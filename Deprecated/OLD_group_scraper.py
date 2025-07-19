import time
from playwright.sync_api import sync_playwright
import os

GROUP_URL = "https://www.facebook.com/groups/vietnamnewzealand"
KEYWORDS = ["ezyremit"]
USER_DATA_DIR = "./playwright_session"
HEADLESS_MODE = False
SCROLL_TIMES = 5  # How many times to scroll to load more results

def search_and_scrape_posts():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=['--disable-notifications']
        )
        page = context.new_page()
        for keyword in KEYWORDS:
            print(f"Searching for keyword: {keyword}")
            page.goto(GROUP_URL)
            time.sleep(5)  # Wait for group page to load

            # --- Click the search icon to reveal the search bar ---
            try:
                # This selector may need to be updated if Facebook changes their UI
                search_icon_selector = '[aria-label="Search"]'
                page.locator(search_icon_selector).first.click(timeout=5000)
                print("Clicked search icon to reveal search bar.")
                time.sleep(1)
            except Exception:
                print("Search icon not found or already open.")

            # --- Find the search bar and enter the keyword ---
            try:
                search_selector = 'input[placeholder*="Search this group"]'
                page.wait_for_selector(search_selector, timeout=10000)
                page.fill(search_selector, keyword)
                page.keyboard.press("Enter")
                print(f"Filled search bar with '{keyword}' and pressed Enter.")
            except Exception as e:
                print(f"Could not find or fill the search bar: {e}")
                continue  # Skip to next keyword if search fails

            time.sleep(5)  # Wait for search results to load

            # --- Scroll to load more results ---
            for _ in range(SCROLL_TIMES):
                page.mouse.wheel(0, 10000)
                time.sleep(2)

            time.sleep(3)

            # --- Scrape visible posts on the page ---
            post_containers = page.query_selector_all('div[class="x1n2onr6 x1ja2u2z x1jx94hy xw5cjc7 x1dmpuos x1vsv7so xau1kf4 x9f619 xh8yej3 x6ikm8r x10wlt62 xquyuld"]')
            print(f"Found {len(post_containers)} post containers for keyword '{keyword}'.")

            for idx, post in enumerate(post_containers):
                try:
                    # post_text = post.inner_text()
                    # post_text = " ".join(line.strip() for line in post_text.splitlines() if line.strip() and line.strip() != "Facebook")
                    # print(f"\n[Post {idx} for '{keyword}']:\n{post_text[:500]}\n{'-'*40}")

                    # --- Extract comments (try common comment container selectors) ---
                    comment_divs = post.query_selector_all('div[class="xdj266r x14z9mp xat24cr x1lziwak x1vvkbs"]')

                    for cidx, comment in enumerate(comment_divs):
                        comment_text = comment.inner_text().strip()
                        if comment_text:
                            print(f"    [Comment {cidx}]: {comment_text}")
                except Exception as e:
                    print(f"Could not extract post or comments: {e}")

        context.close()

def manual_browse():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=['--disable-notifications']
        )
        page = context.new_page()
        print("Manual browsing mode enabled. Navigate as you wish.")
        page.goto(GROUP_URL)
        input("Press Enter to close the browser and end manual mode...")
        context.close()

if __name__ == "__main__":
    if not os.path.exists(USER_DATA_DIR):
        print("Please run your login script first to create a session.")
    else:
        mode = input("Enter 'auto' for automation or 'manual' to browse manually: ").strip().lower()
        if mode == "m":
            manual_browse()
        elif mode == "a":
            search_and_scrape_posts()