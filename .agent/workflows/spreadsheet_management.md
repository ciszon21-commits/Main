---
description: Guide for creating, editing, and analyzing spreadsheets using standard Python libraries
---

# Spreadsheet Management Workflow

Use this workflow when you need to create, edit, or analyze spreadsheets (.xlsx, .csv).
Standard libraries `openpyxl` (primary) and `pandas` (for data analysis) should be used.

## 1. Tool Selection
- **Creating/Editing**: Use `openpyxl`. It allows fine-grained control over formatting, formulas, and styles.
- **Analysis/Reading**: Use `pandas`. It is efficient for filtering, aggregating, and computing metrics.

## 2. Best Practices

### Formatting
- **Headers**: Format headers differently (bold, background color) to distinguish from data.
- **Layout**: Use sensible column widths and row heights. Ensure logical separation of sections with whitespace.
- **Data Types**:
    - **Dates**: Use proper date formats (e.g., `dd-mm-yyyy`), not strings.
    - **Currencies**: Use currency formats (e.g., `$#,##0.00`).
    - **Percentages**: Default to one decimal point (0.0%).
- **Color Coding**:
    - **Blue**: User inputs / assumptions.
    - **Black**: Formulas / derived values.
    - **Green**: Linked / imported data.
    - **Red**: Error flags or external links.

### Formulas
- **Use Standard Formulas**: Stick to standard Excel functions (SUM, AVERAGE, IF, VLOOKUP).
- **Avoid Dynamic Arrays**: Avoid `FILTER`, `SORT`, `SEQUENCE` if broad compatibility is required.
- **Static References**: Use absolute references (`$A$1`) where appropriate for robust copy-pasting.
- **Legibility**: Use helper cells for complex logic rather than massive single-cell formulas.

### Financial Models
- **Formatting**: Zeros as "-". Negative numbers in red parentheses.
- **Citations**: Cite sources in cell comments or a dedicated column/sheet.

## 3. Implementation Steps

### Creating a New Spreadsheet
1.  Initialize `Workbook` using `openpyxl`.
2.  Create/Rename sheets as needed.
3.  Populate data:
    - Write headers first.
    - Write data rows.
4.  Apply formatting (Styles, Borders, Fonts).
5.  Save using `wb.save()`.

### Editing an Existing Spreadsheet
1.  Load workbook: `openpyxl.load_workbook(filename)`.
2.  Modify cells.
3.  **Preserve Styles**: Be careful not to clobber existing conditional formatting or complex styles unless necessary.
4.  Save.

## 4. Verification
- **Code Review**: Ensure no generic placeholders are used.
- **Formula Check**: Verify logic of applied formulas.
- **Visual Check**: If possible, read back the file using `pandas` or `openpyxl` to confirm data integrity.
