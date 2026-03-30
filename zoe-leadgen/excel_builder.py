# excel_builder.py
# Exports leads from SQLite to a formatted Excel (.xlsx) file.
# Functions:
#   - export_leads(output_path, filters=None) : queries DB and writes Excel file
#   - apply_formatting(worksheet)             : header styles, column widths,
#                                               conditional formatting
# Uses openpyxl. Saved to /exports and served for download by app.py.
