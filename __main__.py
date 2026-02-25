from pyplaner import Planer

def _pdf_time_cb(phase: str, seconds: float) -> None:
    print(f"{phase:15s}: {seconds:.3f}s")


planner = Planer("pages/ff-2026.html")

planer_html = planner.html()
with open("ff-2026.html", "w", encoding="utf-8") as f:
    f.write(planer_html)

planner_pdf = planner.pdf(timing_cb=_pdf_time_cb)
with open("ff-2026.pdf", "wb") as f:
    f.write(planner_pdf)
