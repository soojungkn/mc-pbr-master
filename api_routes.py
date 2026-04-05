"""
Custom API routes for MicroCreativity-PBR-Master.
Provides a native OS folder picker dialog.

Platform support:
  Windows  -> PowerShell FolderBrowserDialog  (native, always on top)
  macOS    -> osascript / AppleScript          (native Finder dialog)
"""

from aiohttp import web
import server
import asyncio
import subprocess
import sys


def _pick_folder_windows(initial_dir: str) -> str | None:
    """Use PowerShell's FolderBrowserDialog — reliable, always on top."""
    set_path = f'$d.SelectedPath = "{initial_dir}"' if initial_dir else ""
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
        '$d.Description = "Select Save Folder"; '
        "$d.ShowNewFolderButton = $true; "
        f"{set_path}; "
        "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        path = result.stdout.strip()
        return path if path else None
    except Exception as e:
        print(f"[MC PBR] PowerShell folder picker error: {e}")
        return None


def _pick_folder_macos(initial_dir: str) -> str | None:
    """Use osascript / AppleScript — opens native Finder folder chooser."""
    default_clause = (
        f' default location POSIX file "{initial_dir}"' if initial_dir else ""
    )
    script = f'POSIX path of (choose folder with prompt "Select Save Folder"{default_clause})'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        path = result.stdout.strip().rstrip("/")
        return path if path else None
    except Exception as e:
        print(f"[MC PBR] osascript folder picker error: {e}")
        return None


def _pick_folder_sync(initial_dir: str = "") -> str | None:
    if sys.platform == "win32":
        return _pick_folder_windows(initial_dir)
    elif sys.platform == "darwin":
        return _pick_folder_macos(initial_dir)
    else:
        print("[MC PBR] Folder picker is only supported on Windows and macOS.")
        return None


@server.PromptServer.instance.routes.post("/mc/pick_folder")
async def pick_folder_handler(request):
    """Open a native OS folder picker and return the chosen path."""
    data = await request.json() if request.can_read_body else {}
    initial_dir = data.get("initial_dir", "") or ""

    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _pick_folder_sync, initial_dir)

    return web.json_response({"path": path})
