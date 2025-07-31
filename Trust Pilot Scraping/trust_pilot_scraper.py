import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
from datetime import datetime

def scrape_trustpilot_reviews(company_name, max_pages=5):
    """
    Scrape Trustpilot reviews for a given company and save to JSON file
    """
    base_url = f"https://www.trustpilot.com/review/{company_name}"  
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print(f"🔍 Starting to scrape Trustpilot for: {company_name}")
    print(f"📋 Base URL: {base_url}")
    print("=" * 80)
    
    # Check if company already exists in the file
    filename = 'Trust Pilot Scraping/scraped_trust_pilot.json'
    if check_company_exists(company_name, filename):
        print(f"🚫 Company '{company_name}' already exists in {filename}")
        print(f"⏭️ Skipping scraping for this company...")
        return 0
    
    scraped_reviews = []
    total_reviews = 0
    seen_reviews = set()  # Track duplicates across all pages
    
    for page in range(1, max_pages + 1):
        # Fixed pagination URL format
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"
        
        print(f"\n📄 Scraping page {page}: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"🌐 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to get page {page}: Status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all review containers - these contain all review data together
            review_containers = soup.find_all('article', {'data-service-review-card-paper': True})
            
            if not review_containers:
                # Try alternative selectors
                review_containers = soup.find_all('div', {'data-service-review-card-paper': True})
            
            if not review_containers:
                # Try more generic selectors
                review_containers = soup.select('[data-service-review-card-paper]')
            
            print(f"✅ Found {len(review_containers)} review containers on page {page}")
            
            page_review_count = 0
            
            for i, container in enumerate(review_containers):
                print(f"\n--- Processing Review {i + 1} ---")
                
                # Extract reviewer name
                reviewer = "Anonymous"
                reviewer_selectors = [
                    'span[data-consumer-name-typography="true"]',
                    '.typography_heading-xxs__QKBS8.typography_appearance-default__AAY17',
                    'span.typography_heading-xxs__QKBS8',
                    '[data-consumer-name-typography] span',
                    'span[class*="consumer-name"]'
                ]
                
                for selector in reviewer_selectors:
                    reviewer_elem = container.select_one(selector)
                    if reviewer_elem:
                        reviewer = reviewer_elem.get_text(strip=True)
                        print(f"👤 Reviewer: {reviewer}")
                        break
                
                # Extract rating
                rating = None
                rating_selectors = [
                    '[data-service-review-rating]',
                    'img[alt*="star"]',
                    '[class*="star-rating"]'
                ]
                
                for selector in rating_selectors:
                    rating_elem = container.select_one(selector)
                    if rating_elem:
                        if rating_elem.has_attr('data-service-review-rating'):
                            rating = int(rating_elem['data-service-review-rating'])
                        elif rating_elem.name == 'img' and 'alt' in rating_elem.attrs:
                            alt_text = rating_elem['alt']
                            import re
                            rating_match = re.search(r'(\d)', alt_text)
                            if rating_match:
                                rating = int(rating_match.group(1))
                        print(f"⭐ Rating: {rating}")
                        break
                
                # Extract title
                title = ""
                title_selectors = [
                    'h2[data-service-review-title-typography="true"]',
                    '[data-service-review-title-typography]',
                    'h2',
                    'h3'
                ]
                
                for selector in title_selectors:
                    title_elem = container.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if len(title) > 5:  # Only use meaningful titles
                            print(f"📝 Title: {title}")
                            break
                        else:
                            title = ""
                
                # Extract review text
                text = ""
                text_selectors = [
                    'p[data-service-review-text-typography="true"]',
                    '[data-service-review-text-typography]',
                    '.styles_reviewContent__0Q2Tg',
                    'p[class*="review-text"]',
                    'div[class*="review-content"] p'
                ]
                
                for selector in text_selectors:
                    text_elem = container.select_one(selector)
                    if text_elem:
                        text = text_elem.get_text(strip=True)
                        if len(text) > 10:  # Only use meaningful text
                            # Clean up "See more" endings
                            if text.endswith('See more'):
                                text = text[:-8].strip()
                            elif text.endswith('...See more'):
                                text = text[:-11].strip()
                            print(f"💬 Text ({len(text)} chars): {text[:100]}...")
                            break
                
                # Extract date
                date = ""
                date_selectors = [
                    'time[datetime]',
                    '[datetime]',
                    '.styles_reviewHeader__iU9Px time',
                    'time'
                ]
                
                for selector in date_selectors:
                    date_elem = container.select_one(selector)
                    if date_elem:
                        if date_elem.has_attr('datetime'):
                            try:
                                # Parse ISO datetime and format it
                                date_obj = datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00'))
                                date = date_obj.strftime('%Y-%m-%d')
                            except:
                                date = date_elem['datetime']
                        else:
                            date = date_elem.get_text(strip=True)
                        print(f"📅 Date: {date}")
                        break
                
                # Create unique identifier to avoid duplicates
                review_signature = f"{reviewer}_{rating}_{date}_{text[:50]}"
                
                if review_signature in seen_reviews:
                    print(f"⚠️ Duplicate review detected, skipping...")
                    continue
                
                seen_reviews.add(review_signature)
                
                # Create review data structure
                review_data = {
                    "reviewer": reviewer,
                    "rating": rating,
                    "title": title,
                    "text": text,
                    "date": date
                }

                if not title.strip() and not text.strip():
                    print(f"⚠️ Skipping review with empty title and text")
                    continue
                
                scraped_reviews.append(review_data)
                page_review_count += 1
                total_reviews += 1
                
                print(f"✅ Successfully extracted review #{total_reviews}")
            
            print(f"\n📊 Page {page} summary: {page_review_count} new reviews extracted")
            print(f"🎯 Total reviews so far: {total_reviews}")
            
            # Break if no reviews found (reached end)
            if page_review_count == 0:
                print(f"🔚 No new reviews found on page {page}, stopping...")
                break
            
            # Add delay between pages
            if page < max_pages:
                delay = random.uniform(2, 4)
                print(f"⏳ Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
            
        except requests.RequestException as e:
            print(f"❌ Error scraping page {page}: {e}")
            break
        except Exception as e:
            print(f"❌ Unexpected error on page {page}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # Save to JSON file with company structure
    save_company_reviews(company_name, scraped_reviews, 'Trust Pilot Scraping/scraped_trust_pilot.json')
    
    print(f"\n🎯 Scraping completed! Total reviews processed: {total_reviews}")
    print(f"💾 Reviews saved to scraped_trust_pilot.json")
    return total_reviews

def check_company_exists(company_name, filename):
    """
    Check if a company already exists in the JSON file
    """
    if not os.path.exists(filename):
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if data is a list of company objects
        if isinstance(data, list):
            for company_data in data:
                if company_data.get('company') == company_name:
                    return True
        
        return False
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def save_company_reviews(company_name, reviews, filename):
    """
    Save reviews to JSON file with company structure
    """
    existing_data = []
    
    # Try to load existing data
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"📁 Found existing file with {len(existing_data)} companies")
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"📁 Creating new file {filename}")
            existing_data = []
    
    # Create new company data structure
    new_company_data = {
        "company": company_name,
        "reviews": reviews
    }
    
    # Append new company data
    existing_data.append(new_company_data)
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(reviews)} reviews for {company_name}")
    print(f"📊 Total companies in file: {len(existing_data)}")

def save_to_json(reviews, filename):
    """
    Save reviews to JSON file, appending to existing data if file exists
    """
    existing_reviews = []
    
    # Try to load existing data
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_reviews = json.load(f)
            print(f"📁 Found existing file with {len(existing_reviews)} reviews")
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"📁 Creating new file {filename}")
            existing_reviews = []
    
    # Append new reviews
    all_reviews = existing_reviews + reviews
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(all_reviews)} total reviews to {filename}")
    print(f"➕ Added {len(reviews)} new reviews")

def main():
    # List of companies to scrape
    companies = [
        "ezyremit.com",
        "remitly.com",
        "westernunion.com",
        "moneygram.com",
        "wise.com",
        "worldremit.com",
        "orbitremit.com",
        "riamoneytransfer.com",
        "ofx.com",
        "xe.com",
    ]
    
    print("🚀 Trustpilot Multi-Company Scraper")
    print("=" * 50)
    
    total_companies_scraped = 0
    
    for company in companies:
        print(f"\n🏢 Processing company: {company}")
        print("-" * 40)
        
        reviews_count = scrape_trustpilot_reviews(company, max_pages=5)
        
        if reviews_count > 0:
            total_companies_scraped += 1
            print(f"✅ Successfully scraped {reviews_count} reviews for {company}")
        else:
            print(f"⏭️ Skipped {company} (already exists or no reviews found)")
        
        # Add delay between companies
        if company != companies[-1]:  # Not the last company
            print(f"⏳ Waiting 1 seconds before next company...")
            time.sleep(1)
    
    print(f"\n🎯 Scraping completed for all companies!")
    print(f"📊 Total companies processed: {total_companies_scraped}/{len(companies)}")

if __name__ == "__main__":
    main()