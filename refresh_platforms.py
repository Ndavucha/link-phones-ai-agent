from src.multi_platform import MultiPlatformPoster
import time

poster = MultiPlatformPoster()

print("🔄 Refreshing platform connections...")
# Try to get platforms with a fresh request
connected = poster.get_platforms()

print(f"\n🔍 Connected platforms: {connected}")

# If still empty, try a test post to wake up the API
if not connected:
    print("\n📤 Sending test ping to wake up API...")
    result = poster.post(
        caption="API connection test",
        platforms=["facebook"]  # Try with Facebook
    )
    print(f"Test result: {result}")
    
    # Check again after test
    time.sleep(5)
    connected = poster.get_platforms()
    print(f"\n🔍 After test: {connected}")