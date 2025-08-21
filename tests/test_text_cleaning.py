#!/usr/bin/env python3
"""
Simple test for TTS text cleaning function.
"""

import sys
import re

def clean_text_for_tts(text: str) -> str:
    """Clean text by removing emojis, special characters, and formatting for better TTS."""
    if not text:
        return ""
    
    # Remove emojis (Unicode emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+", 
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove special markdown and formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code` -> code
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strike~~ -> strike
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove excessive punctuation (keep single instances)
    text = re.sub(r'[!]{2,}', '!', text)  # Multiple ! -> single !
    text = re.sub(r'[?]{2,}', '?', text)  # Multiple ? -> single ?
    text = re.sub(r'[.]{3,}', '...', text)  # Multiple . -> ellipsis
    
    # Remove special symbols but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\'-]', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def test_text_cleaning():
    """Test the text cleaning function."""
    test_cases = [
        {
            "input": "Hello! 😊 This is a test with emojis 🎉 and **bold text** that should be cleaned.",
            "expected_changes": ["Remove emojis", "Remove markdown bold"]
        },
        {
            "input": "What's the weather like today? ☀️🌧️ It's quite lovely, isn't it? 🇬🇧",
            "expected_changes": ["Remove weather emojis", "Remove flag emoji"]
        },
        {
            "input": "I can't believe it's working!!! 🚀🚀🚀 Amazing... ***fantastic*** `code snippet` here.",
            "expected_changes": ["Remove rocket emojis", "Remove code markdown", "Clean excessive punctuation"]
        },
        {
            "input": "Visit https://example.com for more info! ~~strikethrough~~ text here.",
            "expected_changes": ["Remove URL", "Remove strikethrough markdown"]
        },
        {
            "input": "Simple text without any special characters.",
            "expected_changes": ["No changes needed"]
        }
    ]
    
    print("🧹 Testing Text Cleaning for TTS")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        input_text = case["input"]
        expected_changes = case["expected_changes"]
        
        print(f"\n📝 Test {i}:")
        print(f"Input:  '{input_text}'")
        
        cleaned_text = clean_text_for_tts(input_text)
        
        print(f"Output: '{cleaned_text}'")
        print(f"Length: {len(input_text)} -> {len(cleaned_text)}")
        print(f"Changes: {', '.join(expected_changes)}")
        
        if len(cleaned_text) < len(input_text):
            print("✅ Text was cleaned (shorter)")
        elif cleaned_text == input_text:
            print("✅ No cleaning needed (text was clean)")
        else:
            print("⚠️ Unexpected result")
        
        print("-" * 40)
    
    print("\n🎯 Text Cleaning Test Complete!")
    print("The cleaned text should be safe for all TTS engines.")

if __name__ == "__main__":
    test_text_cleaning()
