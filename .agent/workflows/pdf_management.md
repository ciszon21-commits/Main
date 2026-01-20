---
description: Guide for creating, reading, and reviewing PDF documents
---

# PDF Management Workflow

Use this workflow when you need to create or read PDF documents directly.
The primary library for creation is `reportlab`. For reading/verification, use `pdfplumber` or `pdftoppm`.

## 1. Tooling
- **Creation**: `reportlab` (standard for programmatic PDF generation).
- **Reading/Verification**: `pdfplumber` (Python) or `pdftoppm` (System tool) for visual rendering.
- **Alternatives**: `pypdf`, `pyMuPDF` (install via pip if needed).

## 2. Quality Expectations
- **Visual Design**: Consistent typography, spacing, and margins.
- **Rendering**: No clipped text, overlapping elements, or unreadable glyphs.
- **Legibility**: Text readable at normal size; avoid walls of text.
- **Citations**: Human-readable standard citation formats.

## 3. Implementation Steps

### Creating a PDF with ReportLab
1.  Import `reportlab` (e.g., `from reportlab.pdfgen import canvas`).
2.  Initialize Canvas: `c = canvas.Canvas("filename.pdf")`.
3.  Draw content:
    - Text: `c.drawString(100, 750, "Hello World")`.
    - Shapes: `c.rect(...)`, `c.line(...)`.
4.  Save: `c.save()`.

### Verification (If tools available)
// turbo
1.  Render to Images: `pdftoppm -png <file.pdf> <output_prefix>`
2.  **Inspect**: Check for layout issues and visual correctness.

## 4. User Communication
- **System Dependencies**: If providing scripts that use `pdftoppm`, **explicitly inform the user** that this is a system-level tool (Poppler).
    - If the user is on Windows, suggest downloading Poppler binaries and adding `bin/` to Environment Variables.
    - If using `reportlab` or `pdfplumber`, remind user to `pip install` them if not present.
