
import os
import image_factory
import wp_utils
from dotenv import load_dotenv

load_dotenv('credentials.env')

def test_featured_image():
    print("Testing Featured Image Generation...")
    
    # 1. Generate Image
    ticker = "TEST_TICKER"
    subtext = "S&P500 & Dividend King"
    filename = f"test_badge_{ticker}.png"
    
    path = image_factory.create_text_image(ticker, subtext, output_filename=filename)
    if not path:
        print("❌ Image generation failed")
        return
        
    print(f"✅ Image generated at: {path}")
    
    # 2. Upload to WP
    print("Uploading to WordPress...")
    media_id = wp_utils.upload_image_to_wordpress(path)
    
    if media_id:
        print(f"✅ Upload successful! Media ID: {media_id}")
    else:
        print("❌ Upload failed")

    # 3. Cleanup
    if os.path.exists(path):
        os.remove(path)
        print("Cleaned up temp file")

if __name__ == "__main__":
    test_featured_image()
