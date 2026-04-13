from __future__ import annotations

import os


def configure_runtime() -> None:
    chromium_flags = [
        "--disable-gpu",
        "--disable-gpu-compositing",
        "--disable-features=UseSkiaRenderer,Vulkan",
        "--no-sandbox",
    ]
    existing_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    merged_flags = " ".join(flag for flag in [existing_flags, *chromium_flags] if flag).strip()

    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = merged_flags
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")


configure_runtime()

from src.train_ticket_app.main_window import run


if __name__ == "__main__":
    run()
