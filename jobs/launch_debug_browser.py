from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


EDGE_CANDIDATES = [
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Edge with a Chrome DevTools Protocol port.")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--user-data-dir", default="browser_profiles/edge_cdp")
    parser.add_argument(
        "--use-default-user-data",
        action="store_true",
        help="Use the normal Edge user data directory. Close all Edge windows before using this option.",
    )
    parser.add_argument("--profile-directory", default="")
    parser.add_argument("--proxy", default="", help="Proxy server for the browser, for example http://host:port")
    parser.add_argument("--url", default="https://www.jd.com/")
    args = parser.parse_args()

    edge = _find_edge()
    if args.use_default_user_data:
        user_data_dir = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "User Data"
        if _edge_is_running():
            raise SystemExit(
                "Edge is already running. To use the normal Edge profile with CDP, "
                "请先关闭所有 Edge 窗口和后台进程，然后重新运行本命令。"
            )
    else:
        user_data_dir = Path(args.user_data_dir).resolve()
    user_data_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(edge),
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={args.port}",
    ]
    if args.proxy:
        command.append(f"--proxy-server={args.proxy}")
    if args.profile_directory:
        command.append(f"--profile-directory={args.profile_directory}")
    command.append(str(args.url))
    subprocess.Popen(command, cwd=str(user_data_dir))

    cdp_url = f"http://127.0.0.1:{args.port}"
    if _wait_for_cdp(cdp_url):
        print(f"debug browser launched and verified: cdp={cdp_url}")
        print(f"user_data_dir={user_data_dir}")
        return

    raise SystemExit(
        f"Edge was launched, but {cdp_url} is not reachable. "
        "如果你使用 --use-default-user-data，请先关闭所有 Edge 窗口后重试；"
        "否则请关闭刚打开的调试浏览器并换一个 --port。"
    )


def _find_edge() -> Path:
    for candidate in EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit("Cannot find msedge.exe. Please install Microsoft Edge or start Chrome with --remote-debugging-port manually.")


def _wait_for_cdp(cdp_url: str, timeout: float = 12.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"{cdp_url}/json/version", timeout=1.0) as response:
                return response.status == 200
        except (OSError, URLError):
            time.sleep(0.5)
    return False


def _edge_is_running() -> bool:
    try:
        output = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq msedge.exe"], text=True, errors="ignore")
    except Exception:
        return False
    return "msedge.exe" in output.lower()


if __name__ == "__main__":
    main()
