---
description: Guide for creating, editing, and reviewing DOCX documents
---

# DOCX Management Workflow

Use this workflow when you need to create or edit Word documents (.docx).
The primary library is `python-docx`.

## 1. Tooling
- **Creation/Editing**: Use `python-docx`.
- **Rendering (Optional but Recommended)**: If `soffice` (LibreOffice) is installed, use it to convert to PDF for verification.

## 2. Quality Expectations
- **Layout**: Consistent typography, spacing, and margins. Heading levels should be obvious.
- **Formatting**: No clipped text, overlapping elements, or broken tables.
- **Content**: Concise, relevant, and free of AI boilerplate.
- **Citations**: Human-readable standard citation formats. No internal tokens.

## 3. Implementation Steps

### Creating a DOCX
1.  Initialize `Document` from `python-docx`.
2.  Add Sections:
    - **Title**: `doc.add_heading('Title', 0)`
    - **Headers**: Use appropriate levels (`level=1`, `level=2`).
    - **Text**: `doc.add_paragraph('content')`.
3.  **Styles**: Use built-in styles or define custom styles for consistency.
4.  **Tables**:
    - Create: `table = doc.add_table(rows, cols)`.
    - Apply style: `table.style = 'Table Grid'`.
5.  **Images**: Use `doc.add_picture()` with defined width/height.

### Verification Loop (If tools available)
// turbo
1.  Render to PDF: `soffice --headless --convert-to pdf --outdir <output_dir> <input.docx>`
2.  Convert PDF to Images (optional): `pdftoppm -png <file.pdf> <output_prefix>`
3.  **Inspect**: Check for layout issues, widows/orphans, and image alignment.

## 4. User Communication
- **System Dependencies**: If providing scripts that use `soffice` or `pdftoppm`, **explicitly inform the user** that these are system-level tools (not just Python packages).
    - Remind them to install LibreOffice (and add `soffice` to PATH) and Poppler (for `pdftoppm`).
    - If the user is on Windows, suggest downloading Poppler binaries and adding `bin/` to Environment Variables.

## 5. Final Finalization
- Ensure all placeholders are removed.
- Verify file can be opened.
