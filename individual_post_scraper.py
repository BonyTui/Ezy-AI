import time
from playwright.sync_api import sync_playwright
import os
import json
import re
from typing import List, Dict

# Configuration
USER_DATA_DIR = "./playwright_session"
HEADLESS_MODE = False
SCROLL_TIMES = 5  # How many times to scroll to load more comments

# List of individual post URLs to scrape
POST_URLS = [
    "https://www.facebook.com/groups/826048477881333/posts/2153243345161833/",
    "https://www.facebook.com/groups/vietnamnewzealand/posts/1654872355087334/",
]

def clean_comment_text(comment_text: str) -> str:
    """
    Clean Facebook comment text by removing interface elements and metadata.
    
    Args:
        comment_text: Raw comment text from Facebook
        
    Returns:
        Cleaned comment text
    """
    if not comment_text:
        return ""
    
    # Remove common Facebook interface elements
    noise_patterns = [
        r'\n\d+[wdhms]\n',  # Remove time stamps with newlines
        r'Like',
        r'Reply', 
        r'Share',
        r'See translation',
        r'Edited',
        r'Follow',
        r'\n·\n',
        r'^\s*·\s*',  # Remove leading dots
        r'\s+·\s+Follow\s*$',  # Remove trailing "· Follow"
    ]
    
    cleaned_text = comment_text
    
    # Apply all noise removal patterns
    for pattern in noise_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Multiple newlines to single
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text)  # Strip leading/trailing whitespace
    
    # Remove lines that are just interface elements
    lines = cleaned_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not is_interface_line(line):
            filtered_lines.append(line)
    
    # Separate username from comment content with tab
    if len(filtered_lines) >= 2:
        # First line is typically the username, rest is the comment
        username = filtered_lines[0]
        comment_content = '\n'.join(filtered_lines[1:])
        return f"{username}\t{comment_content}"
    elif len(filtered_lines) == 1:
        # Only one line - could be just username or username with short comment
        return filtered_lines[0]
    else:
        return ""

def is_interface_line(line: str) -> bool:
    """
    Check if a line is just Facebook interface text that should be removed.
    
    Args:
        line: A single line of text
        
    Returns:
        True if the line should be filtered out
    """
    line_lower = line.lower().strip()
    
    # Interface elements to remove
    interface_elements = [
        'like', 'reply', 'share', 'see translation', 'edited', 'follow',
        '·', 'anonymous participant', 'likesee translation', 'likeShare',
        'likereply', 'replyshare', 'likereplyshare', 'likesee translationedited'
    ]
    
    # Check if line is only interface elements
    if line_lower in interface_elements:
        return True
    
    # Check for combined interface elements at the end of lines
    interface_endings = [
        'like', 'reply', 'share', 'see translation', 'edited', 'follow',
        'likesee translation', 'likeshare', 'likereply', 'replyshare'
    ]
    
    for ending in interface_endings:
        if line_lower.endswith(ending):
            # Check if removing this ending leaves meaningful content
            remaining = line_lower[:-len(ending)].strip()
            if not remaining or len(remaining) < 5:
                return True
    
    # Check if line is just a time stamp (like "1w", "2d", etc.)
    if re.match(r'^\d+[wdhms]$', line_lower):
        return True
    
    # Check if line is very short and likely not meaningful content
    if len(line) <= 3:
        return True
    
    return False

def is_noise_comment(comment: str) -> bool:
    """
    Check if the entire comment is just noise/interface elements.
    
    Args:
        comment: Cleaned comment text
        
    Returns:
        True if the comment should be filtered out
    """
    if not comment or len(comment.strip()) == 0:
        return True
    
    # Check if comment is just a username or very short
    lines = [line.strip() for line in comment.split('\n') if line.strip()]
    
    # If only one line and it's short, likely just a username
    if len(lines) == 1 and len(lines[0]) < 20:
        return True
    
    # Check if all lines are short (likely just metadata)
    if all(len(line) < 15 for line in lines):
        return True
    
    return False

def scrape_individual_posts(post_urls: List[str]) -> List[Dict]:
    """
    Scrape comments from individual Facebook posts.
    
    Args:
        post_urls: List of Facebook post URLs to scrape
        
    Returns:
        List of dictionaries containing post data and comments
    """
    results = []
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=['--disable-notifications']
        )
        page = context.new_page()
        
        for idx, post_url in enumerate(post_urls):
            print(f"\n[{idx + 1}/{len(post_urls)}] Scraping post: {post_url}")
            
            try:
                # Navigate to the post
                page.goto(post_url)
                time.sleep(3)  # Wait for page to load
                
                # Try to expand "View more comments" if available
                try:
                    view_more_buttons = page.query_selector_all('div[role="button"]:has-text("View more comments")')
                    for button in view_more_buttons:
                        if button.is_visible():
                            button.click()
                            time.sleep(2)
                            print("Clicked 'View more comments'")
                except Exception as e:
                    print(f"Could not click 'View more comments': {e}")
                
                # Scroll to load more comments
                print(f"Scrolling to load more comments...")

                # First, find the actual scrollable comment container
                comment_container = page.query_selector('div[class="xb57i2i x1q594ok x5lxg6s x78zum5 xdt5ytf x6ikm8r x1ja2u2z x1pq812k x1rohswg xfk6m8 x1yqm8si xjx87ck xx8ngbg xwo3gff x1n2onr6 x1oyok0e x1odjw0f x1iyjqo2 xy5w88m"]')

                for scroll_count in range(SCROLL_TIMES):
                    if comment_container:
                        # Check scroll capability
                        # scroll_height = page.evaluate("(element) => element.scrollHeight", comment_container)
                        # client_height = page.evaluate("(element) => element.clientHeight", comment_container)
                        # print(f"Comment container - Scroll height: {scroll_height}, Client height: {client_height}")
                        
                        # Scroll within the comment container
                        page.evaluate("""
                            (element) => {
                                element.scrollTop += 10000;
                            }
                        """, comment_container)
                        print(f"Scrolled comment container {scroll_count + 1}/{SCROLL_TIMES}")
                        time.sleep(1)
                    else:
                        # Fallback to page scroll
                        page.mouse.wheel(0, 1000)
                        print(f"Fallback scroll {scroll_count + 1}/{SCROLL_TIMES}")
                
                # Wait a bit after scrolling
                time.sleep(2)
                
                # Extract post content
                post_data = {
                    "url": post_url,
                    "post_text": "",
                    "comments": [],
                    "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Try to get the main post text
                try:
                    # Multiple selectors for post content
                    post_content_selectors = [
                        'div[class="x1iorvi4 xjkvuk6 x1g0dm76 xpdmqnj"]',
                        'div[dir="auto"][style="text-align: start;"]',
                        '[data-ad-preview="message"]',
                        'div[data-testid="post_message"]',
                        'div[class*="userContent"]',
                        'div[class*="x11i5rnm xat24cr x1mh8g0r x1vvkbs"]'  # Common post text container
                    ]
                    
                    for selector in post_content_selectors:
                        post_content_element = page.query_selector(selector)
                        if post_content_element:
                            post_data["post_text"] = post_content_element.inner_text().strip()
                            break
                    
                    if not post_data["post_text"]:
                        print("Could not extract main post text")
                        
                except Exception as e:
                    print(f"Error extracting post text: {e}")
                
                # Extract comments using multiple selectors
                comment_selectors = [
                    'div[class*="xdj266r"][class*="x11i5rnm"][class*="xat24cr"]',  # Common comment container
                    'div[data-testid="comment"]',
                    'div[class*="comment"]',
                    'div[aria-label*="Comment"]',
                    'li[data-testid="comment"]'
                ]
                
                all_comments = []
                
                for selector in comment_selectors:
                    try:
                        comment_elements = page.query_selector_all(selector)
                        if comment_elements:                            
                            for comment_element in comment_elements:
                                try:
                                    comment_text = comment_element.inner_text().strip()
                                    
                                    # Clean the comment text
                                    cleaned_comment = clean_comment_text(comment_text)
                                    
                                    # Filter out empty comments and common noise
                                    if (cleaned_comment and 
                                        len(cleaned_comment) > 1 and  # Ensure meaningful content
                                        not is_noise_comment(cleaned_comment)):  # Check if it's just noise
                                        
                                        all_comments.append(cleaned_comment)
                                        
                                except Exception as e:
                                    print(f"Error extracting individual comment: {e}")
                            
                            # If we found comments with this selector, break
                            if all_comments:
                                break
                                
                    except Exception as e:
                        print(f"Error with selector {selector}: {e}")
                
                # Remove duplicates while preserving order
                seen = set()
                unique_comments = []
                for comment in all_comments:
                    if comment not in seen:
                        seen.add(comment)
                        unique_comments.append(comment)
                
                post_data["comments"] = unique_comments
                print(f"Extracted {len(unique_comments)} unique comments")
                
                results.append(post_data)
                
            except Exception as e:
                print(f"Error scraping post {post_url}: {e}")
                results.append({
                    "url": post_url,
                    "error": str(e),
                    "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # Small delay between posts
            time.sleep(2)
        
        context.close()
    
    return results

def save_results_to_json(results: List[Dict], filename: str = "scraped_posts.json"):
    """Save scraping results to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {filename}")

def print_summary(results: List[Dict]):
    """Print a summary of the scraping results."""
    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")
    
    total_posts = len(results)
    successful_posts = len([r for r in results if "error" not in r])
    total_comments = sum(len(r.get("comments", [])) for r in results if "error" not in r)
    
    print(f"Total posts processed: {total_posts}")
    print(f"Successfully scraped: {successful_posts}")
    print(f"Failed: {total_posts - successful_posts}")
    print(f"Total comments collected: {total_comments}")
    
    for i, result in enumerate(results):
        if "error" not in result:
            print(f"\nPost {i+1}: {len(result['comments'])} comments")
            print(f"  URL: {result['url']}")
            if result['post_text']:
                print(f"  Post preview: {result['post_text'][:100]}{'...' if len(result['post_text']) > 100 else ''}")
        else:
            print(f"\nPost {i+1}: ERROR - {result['error']}")
            print(f"  URL: {result['url']}")

def manual_browse():
    """Open browser for manual testing/verification."""
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=['--disable-notifications']
        )
        page = context.new_page()
        print("Manual browsing mode enabled. Navigate to any post you want to test.")
        
        if POST_URLS:
            page.goto(POST_URLS[0])
        else:
            page.goto("https://www.facebook.com")
            
        input("Press Enter to close the browser and end manual mode...")
        context.close()

if __name__ == "__main__":
    if not os.path.exists(USER_DATA_DIR):
        print("Please run your login script first to create a session.")
        print("The script needs an authenticated browser session to access Facebook.")
    else:
        print("Individual Post Scraper")
        print("=" * 30)
        
        if not POST_URLS:
            print("No post URLs configured!")
            print("Please edit the POST_URLS list in this file and add your Facebook post URLs.")
            print("Example format: https://www.facebook.com/groups/vietnamnewzealand/posts/123456789/")
        else:
            print(f"Found {len(POST_URLS)} post URLs to scrape")
        
        mode = input("\nEnter 'auto' for automation, 'manual' to browse manually, or 'q' to quit: ").strip().lower()
        
        if mode in ['m', 'manual']:
            manual_browse()
        elif mode in ['a', 'auto']:
            if not POST_URLS:
                print("Cannot run automation without post URLs. Please configure POST_URLS first.")
            else:
                print("\nStarting automatic scraping...")
                results = scrape_individual_posts(POST_URLS)
                
                # Save and display results
                save_results_to_json(results)
                print_summary(results)
        elif mode in ['q', 'quit']:
            print("Goodbye!")
        else:
            print("Invalid option. Please run the script again.")
