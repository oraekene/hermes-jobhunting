# ATS-Safe Formatting Rules

Source: Splendor thread's formatting checklist, applied literally.

- **File format**: `.docx`, not PDF — unless the specific posting requests
  PDF. Word documents parse more reliably across ATS platforms
  (Greenhouse, Workable, Lever) than PDF exports of styled layouts.
- **Layout**: single column only. No tables, no text boxes, no graphics.
- **Fonts**: Calibri, Arial, or Times New Roman. Nothing decorative.
- **Bullets**: standard round/square bullets only. No custom symbols or icons.
- **Headers**: plain, conventional section labels — PROFESSIONAL
  EXPERIENCE, EDUCATION, SKILLS — not stylized or graphic headers.
- **Avoid**: page headers/footers (often unreadable by parsers), images,
  logos, photos, infographics, floated elements, multi-column layouts.

## Build instructions for this skill

Use the `docx` skill's script-based approach (docx via npm, or
python-docx) to generate the file directly — do not generate HTML/CSS and
convert to PDF, and do not use a visual template with floats or tables.
A flat, boring, single-column `.docx` is the goal, not a design
showcase. Every experience entry: job title line, company/dates line,
plain bullet list underneath. No exceptions without an explicit
posting-specific reason logged in the change-log.
