# excel_builder.py
# Exports leads from the SQLite database to a formatted Excel (.xlsx) file.
# Functions:
#   - export_leads(output_path, filters=None) : queries the DB and writes an Excel file
#   - apply_formatting(worksheet)             : applies header styles, column widths,
#                                               and conditional formatting
# Uses openpyxl to build the workbook.
# The exported file is saved to the /exports directory and served for download by app.py.
