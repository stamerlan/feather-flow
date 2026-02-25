import pathlib
import time
from pyplaner import Planer

def _pdf_time_cb(phase: str, seconds: float) -> None:
    print(f"{phase:15s}: {seconds:.3f}s")


base_path = pathlib.Path(__file__).parent
base = f"file://{base_path.as_posix()}/ff-2026.html"

planner = Planer("pages/ff-2026.html", base=base)

start_ts = time.perf_counter()
planer_html = planner.html()
elapsed_sec = time.perf_counter() - start_ts

with open("ff-2026.html", "w", encoding="utf-8") as f:
    f.write(planer_html)

start_ts = time.perf_counter()
planner_pdf = planner.pdf(timing_cb=_pdf_time_cb)
elapsed_sec = time.perf_counter() - start_ts

with open("ff-2026.pdf", "wb") as f:
    f.write(planner_pdf)
