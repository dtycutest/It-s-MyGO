"""Download tab bar icons from icons8.com - free Material Design icons."""
import urllib.request
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = r"d:\上课\大三下\计算机综合项目实践\ycg-project\frontend\src\static"
SIZE = 81
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

icons = [
    ("home-active.png", "https://img.icons8.com/material-outlined/81/FF6B35/home.png"),
    ("home-inactive.png", "https://img.icons8.com/material-outlined/81/999999/home.png"),
    ("user-active.png", "https://img.icons8.com/material-outlined/81/FF6B35/user.png"),
    ("user-inactive.png", "https://img.icons8.com/material-outlined/81/999999/user.png"),
]

for filename, url in icons:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        data = resp.read()
        path = os.path.join(BASE, filename)
        with open(path, "wb") as f:
            f.write(data)
        print(f"Downloaded {filename} ({len(data)} bytes)")
    except Exception as e:
        print(f"Failed {filename}: {e}")

print("Done")