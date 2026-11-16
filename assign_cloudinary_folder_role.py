import getpass
import json
from urllib.parse import quote

import requests

CLOUD_NAME = "dx4vyfh38"
TARGET_FOLDER = "haybatalsultan"

root_api_key = input("Root API Key: ").strip()
root_api_secret = getpass.getpass("Root API Secret: ").strip()
target_api_key = input("HaybatAlsultan-Store API Key: ").strip()

if not root_api_key or not root_api_secret or not target_api_key:
    raise SystemExit("Missing required value.")

base_url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}"

# 1. Find the target folder and obtain its external ID.
response = requests.get(
    f"{base_url}/folders",
    auth=(root_api_key, root_api_secret),
    timeout=20,
)

if not response.ok:
    print("Folder lookup failed.")
    print("Status:", response.status_code)
    print("Response:", response.text)
    raise SystemExit(1)

folders = response.json().get("folders", [])

folder = next(
    (item for item in folders if item.get("name") == TARGET_FOLDER),
    None,
)

if not folder:
    raise SystemExit(f"Folder '{TARGET_FOLDER}' was not found.")

folder_external_id = folder.get("external_id")

if not folder_external_id:
    raise SystemExit("Folder external_id was not returned by Cloudinary.")

print("Folder found:", TARGET_FOLDER)
print("Folder external_id:", folder_external_id)


# 2. Assign Folder Editor role to the application API key.
payload = {
    "principal": {
        "id": target_api_key,
        "type": "apiKey",
    },
    "operation": "add",
    "roles": [
        "cld::role::content::folder::editor",
    ],
}

response = requests.post(
    (f"{base_url}/folder_operations/invite/{quote(folder_external_id, safe='')}"),
    auth=(root_api_key, root_api_secret),
    json=payload,
    timeout=20,
)

if not response.ok:
    print()
    print("Folder role assignment failed.")
    print("Status:", response.status_code)
    print("Response:", response.text)
    raise SystemExit(1)

print()
print("Folder role assignment completed successfully.")

try:
    print(
        json.dumps(
            response.json(),
            indent=2,
        )
    )
except ValueError:
    print(response.text)
