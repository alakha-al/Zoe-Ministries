import os
from datetime import datetime
import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

COLUMNS = [
    ("ID",         "id",        6),
    ("Source",     "source",    12),
    ("Keyword",    "keyword",   18),
    ("Name",       "name",      28),
    ("Email",      "email",     30),
    ("Phone",      "phone",     18),
    ("WhatsApp",   "whatsapp",  18),
    ("Location",   "location",  20),
    ("Website",    "website",   35),
    ("Twitter",    "twitter",   30),
    ("Instagram",  "instagram", 30),
    ("Facebook",   "facebook",  30),
    ("LinkedIn",   "linkedin",  30),
    ("YouTube",    "youtube",   30),
    ("Contacted",  "contacted", 12),
    ("Scraped At", "scraped_at",20),
]

# Purple header matching the UI
HEADER_FILL  = PatternFill("solid", fgColor="3C3489")
HEADER_FONT  = Font(color="FFFFFF", bold=True, size=10)
ALT_FILL     = PatternFill("solid", fgColor="F4F4F7")
BORDER_SIDE  = Side(style="thin", color="DDDDE8")
CELL_BORDER  = Border(
    left=BORDER_SIDE, right=BORDER_SIDE,
    top=BORDER_SIDE,  bottom=BORDER_SIDE,
)


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def export_leads(leads, job_id=None):
    """
    Write a list of lead dicts to a formatted .xlsx file.

    Args:
        leads  (list[dict]): lead rows from database.get_leads()
        job_id (int|None)  : used in the filename if provided

    Returns:
        str: absolute path to the saved .xlsx file
    """
    _ensure_export_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix    = f"_job{job_id}" if job_id else ""
    filename  = f"zoe_leads{suffix}_{timestamp}.xlsx"
    filepath  = os.path.join(EXPORT_DIR, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"

    # ── Header row ─────────────────────────────────────────────────────────────
    for col_idx, (header, _, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill      = HEADER_FILL
        cell.font      = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border    = CELL_BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"   # keep header visible when scrolling

    # ── Data rows ──────────────────────────────────────────────────────────────
    for row_idx, lead in enumerate(leads, start=2):
        fill = ALT_FILL if row_idx % 2 == 0 else None

        for col_idx, (_, field, _) in enumerate(COLUMNS, start=1):
            value = lead.get(field, "")
            if field == "contacted":
                value = "Yes" if value else "No"

            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border    = CELL_BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=False)
            if fill:
                cell.fill = fill

            # Make URL fields clickable
            if field in ("website", "twitter", "instagram",
                         "facebook", "linkedin", "youtube") and value:
                cell.hyperlink = value
                cell.font = Font(color="3C3489", underline="single")

            # Highlight rows that have an email in green
            if field == "email" and value:
                cell.font = Font(color="1A6B1A", bold=True)

        ws.row_dimensions[row_idx].height = 16

    # ── Summary sheet ──────────────────────────────────────────────────────────
    ws_sum = wb.create_sheet("Summary")
    ws_sum["A1"] = "Zoe Lead Generator — Export Summary"
    ws_sum["A1"].font = Font(bold=True, size=13, color="3C3489")
    ws_sum["A3"] = "Generated:"
    ws_sum["B3"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws_sum["A4"] = "Total leads:"
    ws_sum["B4"] = len(leads)
    ws_sum["A5"] = "With email:"
    ws_sum["B5"] = sum(1 for l in leads if l.get("email"))
    ws_sum["A6"] = "With phone:"
    ws_sum["B6"] = sum(1 for l in leads if l.get("phone"))
    ws_sum["A7"] = "Sources:"
    sources = list({l.get("source", "") for l in leads if l.get("source")})
    ws_sum["B7"] = ", ".join(sources)

    for row in ws_sum.iter_rows(min_row=3, max_row=7, min_col=1, max_col=2):
        for cell in row:
            cell.alignment = Alignment(vertical="center")

    ws_sum.column_dimensions["A"].width = 18
    ws_sum.column_dimensions["B"].width = 35

    wb.save(filepath)
    print(f"[excel] Saved {len(leads)} leads → {filepath}")
    return filepath
