import re

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
        r'\d+[wdhms]$',  # Remove time stamps like "1w", "2d", etc. at end
        r'Like$',        # Remove "Like" at end
        r'Reply$',       # Remove "Reply" at end
        r'Share$',       # Remove "Share" at end
        r'See translation$',  # Remove "See translation" at end
        r'Edited$',      # Remove "Edited" at end
        r'Follow$',      # Remove "Follow" at end
        r'LikeSee translation$',  # Remove combined "LikeSee translation"
        r'LikeShare$',   # Remove combined "LikeShare"
        r'LikeReply$',   # Remove combined "LikeReply"
        r'ReplyShare$',  # Remove combined "ReplyShare"
        r'LikeReplyShare$',  # Remove combined "LikeReplyShare"
        r'LikeSee translationEdited$',  # Remove "LikeSee translationEdited"
        r'LikeSee translation\d+$',  # Remove "LikeSee translation2" etc.
        r'LikeSee translationEdited$',  # Remove "LikeSee translationEdited"
        r'\n\d+[wdhms]\n',  # Remove time stamps with newlines
        r'\nLike\n',
        r'\nReply\n', 
        r'\nShare\n',
        r'\nSee translation\n',
        r'\nEdited\n',
        r'\nFollow\n',
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
    
    return cleaned_text

# Test with sample comments from the scraped data
test_comments = [
    "Quynh Ho\nLiên hệ em bên shb ạLikeSee translation",
    "Mỹ Oanh\nNCB HCM chuyển tiền Sunh hoạt phí, học phí. Tỷ giá cạnh tranh, miễn phí chuyển tiền\nZalo 0962194724LikeSee translation",
    "Lê Thị Thuý Duyên\nHcm ib em lh em 0374967967 DuyêbLikeShare",
    "Hằng Nga Nguyễn\nFollowLikeShare",
    "Nguyễn Thu Trang\n· ib e chuyển tiền nhanh miễn phí 0972.180.823LikeSee translationEdited"
]

print("Testing comment cleaning:")
print("=" * 50)

for i, comment in enumerate(test_comments):
    print(f"\nOriginal comment {i+1}:")
    print(f"'{comment}'")
    
    cleaned = clean_comment_text(comment)
    print(f"Cleaned comment {i+1}:")
    print(f"'{cleaned}'")
    print("-" * 30)
