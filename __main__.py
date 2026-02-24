import pathlib
import time
from pyplaner import Planer

base_path = pathlib.Path(__file__).parent
base = f"file://{base_path.as_posix()}/ff-2026.html"

planner = Planer("pages/feather-flow.html", base=base)

start_ts = time.perf_counter()
planer_html = planner.html()
elapsed_sec = time.perf_counter() - start_ts
print(f"HTML generation took {elapsed_sec:.3f}s")

with open("ff-2026.html", "w", encoding="utf-8") as f:
    f.write(planer_html)

start_ts = time.perf_counter()
planner_pdf = planner.pdf(planer_html, debug=True)
elapsed_sec = time.perf_counter() - start_ts
print(f"PDF generation took {elapsed_sec:.3f}s")

with open("ff-2026.pdf", "wb") as f:
    f.write(planner_pdf)
