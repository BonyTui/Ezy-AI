import time
from playwright.sync_api import sync_playwright
import os

GROUP_URL = "https://www.facebook.com/groups/vietnamnewzealand"
KEYWORDS = ["remittance"]
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
                search_selector = 'input[placeholder*="Search"]'
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

            # --- Scrape visible posts on the page ---
            post_links = set()
            post_containers = page.query_selector_all('div[role="article"]')
            print(f"Found {len(post_containers)} post containers for keyword '{keyword}'.")

            for idx, post in enumerate(post_containers):
                # Try to get the first <span> or <div> with text content
                try:
                     # Get all divs/spans with dir="auto"
                    text_blocks = post.query_selector_all('div[dir="auto"], span[dir="auto"]')
                    
                    # Extract text, skip the first one (name)
                    texts = [tb.inner_text() for tb in text_blocks]

                    # Skip if "Sponsored" or "Paid for by" is in any block
                    if any("Sponsored" in t or "Paid for by" in t for t in texts):
                        continue

                    # Heuristic: skip first block (name), join the next 1-2 blocks as post body
                    post_body = ""
                    if len(texts) > 2:
                        post_body = "\n".join(texts[1:3])
                    elif len(texts) > 1:
                        post_body = texts[1]
                    else:
                        post_body = texts[0] if texts else ""

                    # Only print if it looks like a real post
                    if "Like" in post.inner_text() and "Comment" in post.inner_text():
                        print(f"\n--- Post {idx} for '{keyword}' ---\n{post_body.strip()[:500]}\n{'-'*40}")
                except Exception:
                    continue

            # --- Visit each post and scrape content ---
            for post_url in post_links:
                print(f"Scraping post: {post_url}")
                page.goto(post_url)
                time.sleep(3)
                try:
                    post_content = page.inner_text('div[role="article"]')
                    print(post_content[:300])  # Print first 300 chars
                except Exception:
                    print("Could not extract post content.")

        context.close()

if __name__ == "__main__":
    if not os.path.exists(USER_DATA_DIR):
        print("Please run your login script first to create a session.")
    else:
        search_and_scrape_posts()