"""
Custom API routes for MicroCreativity-PBR-Master.
Provides server-side folder picker dialog.
"""

from aiohttp import web
import server
import threading


def _pick_folder_sync(initial_dir=None):
    """Open a native OS folder picker dialog (runs on the SERVER machine).
    Must run in the main thread on macOS, so we use threading for safety."""
    result = {"path": None}

    def _run():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)  # Bring to front
            path = filedialog.askdirectory(
                title="Select Save Folder",
                initialdir=initial_dir
            )
            root.destroy()
            if path:
                result["path"] = path
        except Exception as e:
            print(f"[MC PBR] Folder picker error: {e}")

    # Run in a thread to avoid blocking the event loop
    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=120)  # Wait up to 2 minutes for user to pick

    return result["path"]


@server.PromptServer.instance.routes.post("/mc/pick_folder")
async def pick_folder_handler(request):
    """API endpoint that opens a native folder picker on the server."""
    import asyncio

    data = await request.json() if request.can_read_body else {}
    initial_dir = data.get("initial_dir", None)

    # Run the blocking tkinter dialog in a thread pool
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _pick_folder_sync, initial_dir)

    if path:
        return web.json_response({"path": path})
    else:
        return web.json_response({"path": None})
