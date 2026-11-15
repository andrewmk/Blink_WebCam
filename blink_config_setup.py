import asyncio
import json
from pathlib import Path
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import BlinkURLHandler
import base64
import uuid

CONFIG_FILE = "blink_config.json"
TOKEN_FILE = "blink_token.json"


def extract_hardware_id(token_data):
    """Extract hardware_id from the JWT access token payload, with fallback."""
    try:
        token = token_data.get("token", "")
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        hw_id = decoded.get("hardware_id")
        if hw_id:
            return hw_id
    except Exception:
        pass
    return token_data.get("hardware_id") or str(uuid.uuid4()).upper()


def get_input_with_default(prompt, default_value, value_type=str):
    """Get user input with existing value as default"""
    if default_value is not None:
        if value_type == bool:
            default_str = "Y" if default_value else "N"
            display_prompt = f"{prompt} [{default_str}]: "
        else:
            display_prompt = f"{prompt} [{default_value}]: "
    else:
        display_prompt = f"{prompt}: "

    user_input = input(display_prompt).strip()

    if not user_input and default_value is not None:
        return default_value

    if value_type == int:
        try:
            return int(user_input) if user_input else default_value
        except ValueError:
            print(f"\u26A0 Invalid input, using default: {default_value}")
            return default_value
    elif value_type == bool:
        if user_input.upper() in ['Y', 'YES']:
            return True
        elif user_input.upper() in ['N', 'NO']:
            return False
        return default_value

    return user_input if user_input else default_value


async def setup_config():
    """Query Blink API for cameras and create configuration file"""

    # Load existing config if available
    existing_config = {}
    if Path(CONFIG_FILE).exists():
        print("=" * 60)
        print("\u25B6 Existing configuration found")
        print("  [V] View configuration")
        print("  [R] Re-run setup")
        choice = input("\nYour choice [V/R]: ").strip().upper()

        if choice == "V":
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                print("=" * 60)
                print("\u25B6 Configuration Summary")
                print("=" * 60)
                print("\u25B6 Cameras monitored:")
                for cam in config.get("cameras", []):
                    print(f"  \u2022 {cam}")
                poll_interval = config.get("poll_interval", 300)
                max_days = config.get("max_days", 7)
                max_images = int((max_days * 24 * 60) / (poll_interval // 60))
                print("\u23F1 Polling interval (seconds):", poll_interval)
                print("\u25A1 Max days:", max_days)
                print("\u25A1 Max images per camera (calculated):", max_images)
                print("\u25B6 Carousel images:", config.get("carousel_images", 5))

                print("=" * 60)
            except Exception as e:
                print(f"\u26A0 Could not read configuration: {e}")
            return
        elif choice == "R":
            print("\n\u25B6 Re-running setup...")
            print("\u25B6 Press Enter to keep existing values, or type new values\n")
            try:
                with open(CONFIG_FILE, "r") as f:
                    existing_config = json.load(f)
            except Exception as e:
                print(f"\u26A0 Could not load existing config: {e}")

    # Check Blink token
    if not Path(TOKEN_FILE).exists():
        print("\u274C Error: blink_token.json not found!")
        print("Please run 'python blink_token.py' first to authenticate.")
        return

    print("Loading authentication token...")
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    print("Connecting to Blink API...\n")

    async with ClientSession() as session:
        blink = Blink(session=session)

        host_url = token_data.get("host", "")
        region_id = host_url.replace("https://rest-", "").replace(".immedia-semi.com", "")

        blink.auth = Auth({"device_id": extract_hardware_id(token_data)}, session=session, no_prompt=True)
        blink.auth.region_id = region_id
        blink.auth.host = host_url
        blink.auth.token = token_data.get("token")
        blink.auth.refresh_token = token_data.get("refresh_token")
        blink.auth.client_id = token_data.get("client_id")
        blink.auth.account_id = token_data.get("account_id")
        blink.auth.user_id = token_data.get("user_id")
        blink.urls = BlinkURLHandler(region_id)

        try:
            await blink.setup_post_verify()

            camera_list = list(blink.cameras.keys())
            if not camera_list:
                print("\u26A0 No cameras found on your Blink account!")
                return

            print("=" * 60)
            print("\u2705 Found", len(camera_list), "camera(s):")
            print("=" * 60)
            for i, cam_name in enumerate(camera_list, 1):
                print(f"  {i}. {cam_name}")
            print("=" * 60)

            # --- Camera Selection ---
            print("\n\u25B6 Camera Selection")
            print("-" * 60)
            existing_cameras = existing_config.get("cameras", [])

            if existing_cameras:
                print("Current cameras monitored:")
                for cam in existing_cameras:
                    print(f"  \u2022 {cam}")
                print("\nChange camera selection?")
                print("  [N] No - keep current cameras (default)")
                print("  [A] All cameras")
                print("  [C] Choose specific cameras")
                choice = input("\nYour choice [N/A/C]: ").strip().upper()
            else:
                print("Select cameras to monitor:")
                print("  [A] All cameras (default)")
                print("  [C] Choose specific cameras")
                choice = input("\nYour choice [A/C]: ").strip().upper()

            selected_cameras = existing_cameras

            if choice == "C":
                print("\nEnter camera numbers to monitor (comma-separated), e.g., 1,3,4")
                selection = input("Camera numbers: ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    selected_cameras = [camera_list[i] for i in indices if 0 <= i < len(camera_list)]
                except:
                    print("Invalid selection, using existing cameras...")
                    selected_cameras = existing_cameras if existing_cameras else camera_list
            elif choice == "A":
                selected_cameras = camera_list
            elif not choice and not existing_cameras:
                selected_cameras = camera_list

            print("\n\u2705 Selected Cameras:")
            for cam in selected_cameras:
                print(f"  \u2022 {cam}")

            # --- Polling Interval ---
            print("\n\u25B6 Polling Interval")
            print("-" * 60)
            existing_poll = existing_config.get("poll_interval", 300) // 60
            print("How often should snapshots be taken?")
            print("  [1] Every 1 minute")
            print("  [5] Every 5 minutes (default)")
            print("  [10] Every 10 minutes")
            print("  [15] Every 15 minutes")
            print("  [30] Every 30 minutes")
            print("  [60] Every 60 minutes")
            poll_minutes = get_input_with_default("\nMinutes", existing_poll, int)
            poll_interval = poll_minutes * 60

            # --- Image Storage ---
            print("\n\u25B6 Image Storage")
            print("-" * 60)
            existing_days = existing_config.get("max_days", 7)
            print("How many days of images should be saved?")
            print("  1  = 1 day")
            print("  7  = 7 days (default)")
            print(" 14  = 14 days")
            print(" 30  = 30 days")
            max_days = get_input_with_default("\nDays", existing_days, int)
            max_images = int((max_days * 24 * 60) / poll_minutes)
            print("Estimated images per camera:", max_images)

            # --- Carousel ---
            print("\n\u25B6 Carousel Display")
            print("-" * 60)
            existing_carousel = existing_config.get("carousel_images", 5)
            print("How many recent images to show in the web carousel?")
            print("  3 images ")
            print("  5 images (default)")
            print(" 10 images ")
            carousel_images = get_input_with_default("\nCarousel images", existing_carousel, int)
            if carousel_images < 1:
                carousel_images = 1
            elif carousel_images > 20:
                carousel_images = 20
                print("\u26A0 Limited to maximum of 20 images")

            # --- Save Config ---
            config = {
                "cameras": selected_cameras,
                "poll_interval": poll_interval,
                "max_days": max_days,
                "carousel_images": carousel_images,
            }

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)

            print("\n" + "=" * 60)
            print("\u2705 Configuration saved to blink_config.json")
            print("=" * 60)
            print("\nConfiguration Summary:")
            print(f"  Cameras: {len(selected_cameras)}")
            print(f"  Poll interval: {poll_minutes} minutes")
            print(f"  Image retention: {max_days} days")
            print(f"  Carousel images: {carousel_images}")
            print("=" * 60)

        except Exception as e:
            print(f"\u274C Error during Blink setup: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("\u25B6 Blink Camera Configuration Setup")
    print("=" * 60)
    asyncio.run(setup_config())
