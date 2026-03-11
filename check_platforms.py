from src.multi_platform import MultiPlatformPoster
import logging

logging.basicConfig(level=logging.INFO)

poster = MultiPlatformPoster()
connected = poster.get_platforms()

print("\n🔍 CONNECTED PLATFORMS:")
print("=" * 40)
if connected:
    for platform in connected:
        print(f"✅ {platform}")
else:
    print("❌ No platforms connected yet")
print("=" * 40)