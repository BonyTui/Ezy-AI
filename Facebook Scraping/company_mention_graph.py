import json
import matplotlib.pyplot as plt
import re
from collections import defaultdict

def analyze_company_mentions(filename):
    """
    Analyze company mentions in Facebook comments and create a graph
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            comment_data = json.load(f)
        
        # Load the actual Facebook posts to analyze comment content
        posts_filename = 'Facebook Scraping/scraped_posts.json'
        with open(posts_filename, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        # Define companies and their variations to search for
        companies = {
            'EzyRemit': ['ezyremit', 'ezy remit', 'ezy-remit'],
            'Remitly': ['remitly', 'remitli'],
            'Western Union': ['western union', 'western-union', 'westernunion'],
            'MoneyGram': ['moneygram', 'money gram'],
            'Wise': ['wise', 'transferwise', 'transfer wise'],
            'WorldRemit': ['worldremit', 'world remit'],
            'OrbitRemit': ['orbit', 'orbitremit', 'orbit remit'],
            'Ria': ['ria', 'riamoneytransfer', 'ria money transfer'],
            'OFX': ['ofx'],
        }
        
        # Count mentions for each company
        company_mentions = defaultdict(int)
        total_comments = 0
        comments_with_company_mentions = 0
        
        # Analyze all comments from all posts
        for post in posts_data:
            if isinstance(post, dict) and 'comments' in post:
                comments = post.get('comments', [])
                total_comments += len(comments)
                
                for comment in comments:
                    if comment and isinstance(comment, str):
                        comment_lower = comment.lower()
                        comment_has_mention = False
                        
                        # Check for each company's mentions
                        for company_name, variations in companies.items():
                            for variation in variations:
                                if variation in comment_lower:
                                    company_mentions[company_name] += 1
                                    if not comment_has_mention:
                                        comment_has_mention = True
                                    break  # Only count once per comment per company
                        
                        if comment_has_mention:
                            comments_with_company_mentions += 1
        
        # Calculate percentages based on comments that mentioned companies
        company_percentages = {}
        for company, count in company_mentions.items():
            if count > 0:  # Only include companies with mentions
                percentage = (count / comments_with_company_mentions) * 100 if comments_with_company_mentions > 0 else 0
                company_percentages[company] = percentage
        
        # Sort by percentage (descending)
        sorted_companies = sorted(company_percentages.items(), key=lambda x: x[1], reverse=True)
        
        # Print results
        print("\n" + "="*60)
        print("💼 COMPANY MENTIONS IN FACEBOOK COMMENTS")
        print("="*60)
        print(f"📊 Total Comments Analyzed: {total_comments:,}")
        print(f"� Comments Mentioning Companies: {comments_with_company_mentions:,}")
        print(f"�📈 Company Mention Analysis (% of company-mentioning comments):")
        print()
        
        for company, percentage in sorted_companies:
            count = company_mentions[company]
            print(f"  {company}: {count} mentions ({percentage:.1f}% of company mentions)")
        
        # Create the graph
        create_company_graph(sorted_companies, total_comments, company_mentions, comments_with_company_mentions)
        
        # Save detailed results
        results = {
            'analysis_date': comment_data.get('analysis_date', 'Unknown'),
            'total_comments_analyzed': total_comments,
            'comments_with_company_mentions': comments_with_company_mentions,
            'company_mentions': dict(company_mentions),
            'company_percentages': company_percentages,
            'sorted_results': sorted_companies
        }
        
        with open('Facebook Scraping/company_mentions_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed analysis saved to: company_mentions_analysis.json")
        print("📈 Graph saved as: company_mentions_graph.png")
        
        return results
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ Error analyzing company mentions: {e}")

def create_company_graph(sorted_companies, total_comments, company_mentions, comments_with_company_mentions):
    """
    Create a bar graph showing company mention percentages
    """
    # Extract data for plotting - exclude companies with 0 mentions
    companies = [item[0] for item in sorted_companies if item[1] > 0 and company_mentions[item[0]] > 0]
    percentages = [item[1] for item in sorted_companies if item[1] > 0 and company_mentions[item[0]] > 0]
    counts = [company_mentions[company] for company in companies]
    
    if not companies:
        print("⚠️ No company mentions found to graph")
        return
    
    print(f"\n📊 Creating graph for {len(companies)} companies with mentions...")
    print(f"📋 Total percentage: {sum(percentages):.1f}%")
    
    # Create the figure and axis
    plt.figure(figsize=(15, 12))
    
    # Create bars with different colors
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    bars = plt.bar(companies, percentages, color=colors[:len(companies)])
    
    # Customize the graph
    plt.title('Company Mentions in Facebook Comments\n(Money Transfer Services - % of Company-Mentioning Comments)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Companies/Services', fontsize=12, fontweight='bold')
    plt.ylabel('Percentage of Company-Mentioning Comments (%)', fontsize=12, fontweight='bold')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add percentage labels on top of bars
    for i, (bar, percentage, count) in enumerate(zip(bars, percentages, counts)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{percentage:.1f}%\n',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Set y-axis limit to give more space for labels
    plt.ylim(0, max(percentages) * 1.15)
    
    # Add grid for better readability
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)  # Add extra space at bottom for labels
    
    # Save the graph
    plt.savefig('Facebook Scraping/company_mentions_graph.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    
    # Show the graph
    plt.show()

def create_detailed_breakdown_graph(filename):
    """
    Create a more detailed breakdown including specific bank mentions
    """
    try:
        with open('Facebook Scraping/scraped_posts.json', 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        # More detailed company categorization
        detailed_companies = {
            'EzyRemit': ['ezyremit', 'ezy remit'],
            'Remitly': ['remitly'],
            'Western Union': ['western union'],
            'MoneyGram': ['moneygram', 'money gram'],
            'Wise': ['wise', 'transferwise'],
            'WorldRemit': ['worldremit', 'world remit'],
            'OrbitRemit': ['orbit'],
            'Ria': ['ria', 'riamoneytransfer'],
            'OFX': ['ofx'],
        }
        
        company_mentions = defaultdict(int)
        total_comments = 0
        comments_with_company_mentions = 0
        
        for post in posts_data:
            if isinstance(post, dict) and 'comments' in post:
                comments = post.get('comments', [])
                total_comments += len(comments)
                
                for comment in comments:
                    if comment and isinstance(comment, str):
                        comment_lower = comment.lower()
                        comment_has_mention = False
                        
                        for company_name, variations in detailed_companies.items():
                            for variation in variations:
                                if variation in comment_lower:
                                    company_mentions[company_name] += 1
                                    if not comment_has_mention:
                                        comment_has_mention = True
                                    break
                        
                        if comment_has_mention:
                            comments_with_company_mentions += 1
        
        # Filter out companies with no mentions and sort
        filtered_companies = {k: v for k, v in company_mentions.items() if v > 0}
        sorted_detailed = sorted(filtered_companies.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate percentages based on comments that mentioned companies
        detailed_percentages = [(company, (count/comments_with_company_mentions)*100) 
                              for company, count in sorted_detailed if comments_with_company_mentions > 0]
        
        # Create detailed graph
        if detailed_percentages:
            companies = [item[0] for item in detailed_percentages]
            percentages = [item[1] for item in detailed_percentages]
            counts = [filtered_companies[company] for company in companies]
            
            plt.figure(figsize=(16, 10))
            bars = plt.bar(companies, percentages, color=plt.cm.Set3(range(len(companies))))
            
            plt.title('Detailed Company/Service Mentions in Facebook Comments\n(% of Company-Mentioning Comments)', 
                      fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Companies/Services', fontsize=12, fontweight='bold')
            plt.ylabel('Percentage of Company-Mentioning Comments (%)', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            for i, (bar, percentage, count) in enumerate(zip(bars, percentages, counts)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{percentage:.1f}%\n({count})',
                        ha='center', va='bottom', fontweight='bold', fontsize=9)
            
            # Set y-axis limit to give more space for labels
            plt.ylim(0, max(percentages) * 1.15)
            
            # plt.grid(axis='y', alpha=0.3, linestyle='--')
            # plt.figtext(0.02, 0.02, f'Total Comments: {total_comments:,} | Comments with Company Mentions: {comments_with_company_mentions:,}', 
            #             fontsize=10, style='italic')
            plt.tight_layout()
            
            plt.savefig('Facebook Scraping/detailed_company_mentions_graph.png', 
                        dpi=300, bbox_inches='tight', facecolor='white')
            plt.show()
            
            print("\n📈 Detailed breakdown graph saved as: detailed_company_mentions_graph.png")
        
    except Exception as e:
        print(f"❌ Error creating detailed breakdown: {e}")

def main():
    print("📊 Analyzing company mentions in Facebook comments...")
    
    # Main analysis
    results = analyze_company_mentions('Facebook Scraping/comment_summary.json')
    
    if results:
        print("\n" + "="*40)
        print("Creating detailed breakdown...")
        create_detailed_breakdown_graph('Facebook Scraping/comment_summary.json')

if __name__ == "__main__":
    main()
