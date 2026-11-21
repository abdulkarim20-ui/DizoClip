"""
Times ListView.rebuild() with N prompt cards. Uses a temp data folder, never real data.
Usage: python scripts/benchmark_search.py 1000
"""
import os
import sys
import tempfile
import time

os.environ["DIZOCLIP_DATA_DIR"] = tempfile.mkdtemp(prefix="dizoclip_bench_")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.window.main_window import MainWindow  # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    app = QApplication(sys.argv)
    win = MainWindow()
    win.settings["welcome_seen"] = True
    win.prompts[:] = [
        {"id": str(i), "name": f"Prompt {i}", "prompt": f"text {i} " * 20, "color": "#e8794a"}
        for i in range(n)
    ]
    win.list_view.select_tab("prompt", animate=False)
    for query in ("", "prompt 99", "zzz-no-match"):
        win.list_view.search.setText(query)
        start = time.perf_counter()
        win.list_view.rebuild(animate_resize=False)
        ms = (time.perf_counter() - start) * 1000
        print(f"{n} items, query {query!r:>16}: {ms:8.1f} ms")
    win.close()


if __name__ == "__main__":
    main()
