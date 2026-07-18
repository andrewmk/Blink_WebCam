import shutil

TARGETS = [
    "/home/beta-blink/Blink_WebCam/Blink_Web_Cam.py",
    "/home/beta-blink/Blink_WebCam/blink_config_setup.py",


]

OLD = b"        blink.auth = Auth({}, session=session, no_prompt=True)\n"
NEW = b'        blink.auth = Auth({"device_id": token_data.get("hardware_id")}, session=session, no_prompt=True)\n'

for TARGET in TARGETS:
    BACKUP = TARGET + ".bak"
    shutil.copy2(TARGET, BACKUP)
    print(f"Backup created: {BACKUP}")

    with open(TARGET, "rb") as f:
        content = f.read()

    count = content.count(OLD)
    if count == 0:
        print(f"FAIL ({TARGET}): OLD block not found. No changes made.")
    elif count > 1:
        print(f"FAIL ({TARGET}): OLD block found {count} times (expected exactly 1). No changes made.")
    else:
        new_content = content.replace(OLD, NEW)
        with open(TARGET, "wb") as f:
            f.write(new_content)
        print(f"PASS ({TARGET}): device_id now sourced from saved hardware_id.")
