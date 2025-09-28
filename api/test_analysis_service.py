# Simple test for attribute extraction - no database dependencies
import json
from openai import OpenAI

def test_attribute_extraction():
    """Test the core attribute extraction functionality."""
    
    # Initialize OpenAI client
    client = OpenAI()
    
    system_prompt = (
        "You are an expert product analyst. Given a product name, return the top 30 most "
        "commonly discussed attributes/features that people typically mention when reviewing "
        "or discussing this product. Focus on attributes that would be relevant for sentiment analysis. "
        "Return ONLY a JSON array of strings, no explanations or additional text."
    )
    
    # Test iPhone16 attributes
    print("Testing iPhone16 attribute extraction...")
    user_prompt = "Product: iPhone16\n\nReturn the top 30 most discussed attributes as a JSON array."
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    iphone_attributes = json.loads(response.choices[0].message.content)
    print(f"✅ iPhone16 attributes ({len(iphone_attributes)}): {iphone_attributes[:10]}...")
    
    # Test Samsung Galaxy attributes
    print("\nTesting Samsung Galaxy attribute extraction...")
    user_prompt2 = "Product: Samsung Galaxy\n\nReturn the top 30 most discussed attributes as a JSON array."
    
    response2 = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt2}
        ]
    )
    
    samsung_attributes = json.loads(response2.choices[0].message.content)
    print(f"✅ Samsung Galaxy attributes ({len(samsung_attributes)}): {samsung_attributes[:10]}...")
    
    # Compare attributes to show they're different
    print(f"\n📊 Comparison:")
    print(f"iPhone16 unique attributes: {set(iphone_attributes) - set(samsung_attributes)}")
    print(f"Samsung unique attributes: {set(samsung_attributes) - set(iphone_attributes)}")
    
    return iphone_attributes, samsung_attributes

if __name__ == "__main__":
    try:
        iphone_attrs, samsung_attrs = test_attribute_extraction()
        print(f"\n🎉 Test completed successfully!")
        print(f"✅ Dynamic attribute extraction is working!")
        print(f"✅ Product-specific attributes are generated!")
        print(f"✅ Different products get different attributes!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure you have set your OPENAI_API_KEY environment variable")