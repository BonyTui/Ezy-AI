import json
import os
from datetime import datetime
import re

def count_comments_in_json(filename):
    """
    Count total comments in the scraped Facebook posts JSON file and generate a summary
    """
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_posts = 0
        total_comments = 0
        posts_with_content = 0
        posts_with_comments = 0
        posts_data = []
        
        # Analyze each post
        for post in data:
            if isinstance(post, dict):
                post_url = post.get('url', 'Unknown URL')
                post_text = post.get('post_text', '')
                comments = post.get('comments', [])
                scraping_timestamp = post.get('scraping_timestamp', 'Unknown')
                error = post.get('error', None)
                
                total_posts += 1
                comment_count = len(comments)
                total_comments += comment_count
                
                # Check if post has content
                has_content = bool(post_text and post_text.strip())
                if has_content:
                    posts_with_content += 1
                
                # Check if post has comments
                if comment_count > 0:
                    posts_with_comments += 1
                
                # Analyze comment content
                comments_with_mentions = 0
                comments_with_keywords = 0
                money_transfer_keywords = [
                    'remit', 'transfer', 'money', 'bank', 'ezyremit', 'wise', 'orbit',
                    'chuyển tiền', 'ngân hàng', 'tỷ giá', 'phí', 'fee', 'exchange rate'
                ]
                
                for comment in comments:
                    # Check for mentions (@)
                    if '@' in comment or 'tag' in comment.lower():
                        comments_with_mentions += 1
                    
                    # Check for money transfer keywords
                    comment_lower = comment.lower()
                    if any(keyword in comment_lower for keyword in money_transfer_keywords):
                        comments_with_keywords += 1
                
                # Extract group/page info from URL
                group_info = extract_group_info(post_url)
                
                post_analysis = {
                    'url': post_url,
                    'group_info': group_info,
                    'has_content': has_content,
                    'post_text_length': len(post_text) if post_text else 0,
                    'comment_count': comment_count,
                    'comments_with_mentions': comments_with_mentions,
                    'comments_with_keywords': comments_with_keywords,
                    'scraping_timestamp': scraping_timestamp,
                    'has_error': error is not None,
                    'error': error
                }
                
                posts_data.append(post_analysis)
        
        # Generate summary report
        summary = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_posts': total_posts,
            'total_comments': total_comments,
            'posts_with_content': posts_with_content,
            'posts_with_comments': posts_with_comments,
            'posts_without_comments': total_posts - posts_with_comments,
            'average_comments_per_post': total_comments / total_posts if total_posts > 0 else 0,
            'average_comments_per_post_with_comments': total_comments / posts_with_comments if posts_with_comments > 0 else 0,
            'posts_analysis': posts_data
        }
        
        # Group analysis by Facebook group
        group_summary = analyze_by_group(posts_data)
        summary['group_breakdown'] = group_summary
        
        # Save summary to file
        summary_filename = 'Facebook Scraping/comment_summary.json'
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Print summary to console
        print("\n" + "="*60)
        print("💬 FACEBOOK COMMENTS SUMMARY")
        print("="*60)
        print(f"📅 Analysis Date: {summary['analysis_date']}")
        print(f"📝 Total Posts: {summary['total_posts']:,}")
        print(f"💬 Total Comments: {summary['total_comments']:,}")
        print(f"📄 Posts with Content: {summary['posts_with_content']:,}")
        print(f"🗨️  Posts with Comments: {summary['posts_with_comments']:,}")
        print(f"📭 Posts without Comments: {summary['posts_without_comments']:,}")
        print(f"📊 Average Comments per Post: {summary['average_comments_per_post']:.1f}")
        print(f"📈 Average Comments per Post (with comments): {summary['average_comments_per_post_with_comments']:.1f}")
        
        print("\n📊 Group Breakdown:")
        for group_name, group_data in group_summary.items():
            print(f"\n🏢 {group_name}:")
            print(f"   📝 Posts: {group_data['post_count']:,}")
            print(f"   💬 Comments: {group_data['comment_count']:,}")
            print(f"   📊 Avg Comments/Post: {group_data['avg_comments_per_post']:.1f}")
            print(f"   🔗 Keywords Found: {group_data['total_keywords']:,}")
        
        # Find top posts by comments
        top_posts = sorted(posts_data, key=lambda x: x['comment_count'], reverse=True)[:5]
        if top_posts:
            print("\n🏆 Top 5 Posts by Comment Count:")
            for i, post in enumerate(top_posts, 1):
                group_name = post['group_info']
                comment_count = post['comment_count']
                url_short = post['url'][-30:] if len(post['url']) > 30 else post['url']
                print(f"   {i}. {group_name}: {comment_count} comments ({url_short})")
        
        print(f"\n💾 Detailed summary saved to: {summary_filename}")
        print("="*60)
        
        return summary
        
    except json.JSONDecodeError as e:
        print(f"❌ Error reading JSON file: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def extract_group_info(url):
    """
    Extract Facebook group information from URL
    """
    if not url:
        return "Unknown"
    
    # Extract group name from URL
    group_patterns = [
        r'/groups/([^/]+)/',
        r'/groups/([^/]+)',
        r'facebook\.com/([^/]+)/'
    ]
    
    for pattern in group_patterns:
        match = re.search(pattern, url)
        if match:
            group_id = match.group(1)
            
            # Map known group IDs to readable names
            group_name_mapping = {
                'vietnamnewzealand': 'Vietnam New Zealand',
                'vietnameseinnz': 'Vietnamese in NZ',
                '826048477881333': 'Money Transfer Group 1',
                'sovis': 'Students Overseas Vietnam',
                'svtaiuc': 'Vietnamese Students in Australia',
                '740872500956353': 'Money Transfer Group 2'
            }
            
            return group_name_mapping.get(group_id, group_id)
    
    return "Unknown Group"

def analyze_by_group(posts_data):
    """
    Analyze posts and comments by Facebook group
    """
    group_summary = {}
    
    for post in posts_data:
        group_name = post['group_info']
        
        if group_name not in group_summary:
            group_summary[group_name] = {
                'post_count': 0,
                'comment_count': 0,
                'total_keywords': 0,
                'posts_with_comments': 0
            }
        
        group_summary[group_name]['post_count'] += 1
        group_summary[group_name]['comment_count'] += post['comment_count']
        group_summary[group_name]['total_keywords'] += post['comments_with_keywords']
        
        if post['comment_count'] > 0:
            group_summary[group_name]['posts_with_comments'] += 1
    
    # Calculate averages
    for group_name, data in group_summary.items():
        if data['post_count'] > 0:
            data['avg_comments_per_post'] = data['comment_count'] / data['post_count']
        else:
            data['avg_comments_per_post'] = 0
    
    return group_summary

def analyze_comment_content(filename):
    """
    Analyze comment content for specific keywords and patterns
    """
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        money_transfer_services = {
            'ezyremit': 0,
            'wise': 0,
            'remitly': 0,
            'orbit': 0,
            'western union': 0,
            'bank': 0,
            'ngân hàng': 0
        }
        
        all_comments = []
        
        # Collect all comments
        for post in data:
            if isinstance(post, dict) and 'comments' in post:
                all_comments.extend(post.get('comments', []))
        
        # Analyze comment content
        for comment in all_comments:
            comment_lower = comment.lower()
            
            for service, count in money_transfer_services.items():
                if service in comment_lower:
                    money_transfer_services[service] += 1
        
        print("\n🔍 Comment Content Analysis:")
        print("-" * 40)
        print("Money Transfer Service Mentions:")
        for service, count in sorted(money_transfer_services.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  {service.title()}: {count} mentions")
        
        return money_transfer_services
        
    except Exception as e:
        print(f"❌ Error analyzing comment content: {e}")

def main():
    filename = 'Facebook Scraping/scraped_posts.json'
    print("🔍 Counting comments in scraped_posts.json...")
    
    summary = count_comments_in_json(filename)
    
    if summary:
        print("\n" + "="*40)
        analyze_comment_content(filename)

if __name__ == "__main__":
    main()
