import json
import os
from datetime import datetime

def count_reviews_in_json(filename):
    """
    Count total reviews in the scraped trustpilot JSON file and generate a summary
    """
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_reviews = 0
        companies_data = []
        
        # Check if data is in the new company structure or old flat structure
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict) and 'company' in data[0]:
                # New company structure
                print("📊 Analyzing company-structured data...")
                for company_data in data:
                    company_name = company_data.get('company', 'Unknown')
                    reviews = company_data.get('reviews', [])
                    review_count = len(reviews)
                    total_reviews += review_count
                    
                    # Analyze ratings distribution
                    ratings = [r.get('rating') for r in reviews if r.get('rating')]
                    rating_counts = {}
                    for rating in ratings:
                        if rating:
                            rating_counts[rating] = rating_counts.get(rating, 0) + 1
                    
                    # Count reviews with/without text
                    reviews_with_text = len([r for r in reviews if r.get('text', '').strip()])
                    reviews_without_text = review_count - reviews_with_text
                    
                    companies_data.append({
                        'company': company_name,
                        'total_reviews': review_count,
                        'reviews_with_text': reviews_with_text,
                        'reviews_without_text': reviews_without_text,
                        'rating_distribution': rating_counts
                    })
                    
                    print(f"🏢 {company_name}: {review_count} reviews")
            else:
                # Old flat structure (just reviews array)
                print("📊 Analyzing flat review data...")
                total_reviews = len(data)
                
                # Analyze ratings distribution
                ratings = [r.get('rating') for r in data if r.get('rating')]
                rating_counts = {}
                for rating in ratings:
                    if rating:
                        rating_counts[rating] = rating_counts.get(rating, 0) + 1
                
                # Count reviews with/without text
                reviews_with_text = len([r for r in data if r.get('text', '').strip()])
                reviews_without_text = total_reviews - reviews_with_text
                
                companies_data.append({
                    'company': 'Unknown/Mixed',
                    'total_reviews': total_reviews,
                    'reviews_with_text': reviews_with_text,
                    'reviews_without_text': reviews_without_text,
                    'rating_distribution': rating_counts
                })
        
        # Generate summary report
        summary = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_companies': len(companies_data),
            'total_reviews': total_reviews,
            'companies': companies_data
        }
        
        # Save summary to file
        summary_filename = 'Trust Pilot Scraping/review_summary.json'
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print summary to console
        print("\n" + "="*60)
        print("📈 TRUSTPILOT REVIEWS SUMMARY")
        print("="*60)
        print(f"📅 Analysis Date: {summary['analysis_date']}")
        print(f"🏢 Total Companies: {summary['total_companies']}")
        print(f"⭐ Total Reviews: {summary['total_reviews']:,}")
        print("\n📊 Company Breakdown:")
        
        for company in companies_data:
            print(f"\n🏢 {company['company']}:")
            print(f"   📝 Total Reviews: {company['total_reviews']:,}")
            print(f"   💬 With Text: {company['reviews_with_text']:,}")
            print(f"   📭 Without Text: {company['reviews_without_text']:,}")
            
            if company['rating_distribution']:
                print(f"   ⭐ Rating Distribution:")
                for rating in sorted(company['rating_distribution'].keys()):
                    count = company['rating_distribution'][rating]
                    percentage = (count / company['total_reviews']) * 100
                    print(f"      {rating} stars: {count:,} ({percentage:.1f}%)")
        
        print(f"\n💾 Detailed summary saved to: {summary_filename}")
        print("="*60)
        
        return summary
        
    except json.JSONDecodeError as e:
        print(f"❌ Error reading JSON file: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    filename = 'Trust Pilot Scraping/scraped_trust_pilot.json'
    print("🔍 Counting reviews in scraped_trust_pilot.json...")
    count_reviews_in_json(filename)

if __name__ == "__main__":
    main()
