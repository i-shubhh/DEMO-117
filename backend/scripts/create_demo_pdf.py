"""Create demo inspection report PDF using Python stdlib only.

Generates a minimal but text-rich PDF so that PyMuPDF's get_text()
can extract meaningful content during the document agent workflow.
No external dependencies required — uses raw PDF 1.4 syntax.
"""

from pathlib import Path
import sys

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "demo" / "inspection_report_P102A.pdf"

PAGES = [
    # Page 1: Cover & Summary
    (
        "MRPL REFINERY - FIELD INSPECTION REPORT",
        [
            "Mangalore Refinery and Petrochemicals Limited",
            "",
            "REPORT NUMBER:   INS-2026-P102A-0087",
            "EQUIPMENT TAG:   P-102A",
            "EQUIPMENT DESC:  Crude Feed Booster Centrifugal Pump",
            "UNIT / PLANT:    Crude Distillation Unit (CDU-1)",
            "INSPECTION DATE: 04 September 2026",
            "INSPECTOR:       Ravi Shankar (Cert. Inspector, ASME VI)",
            "REVIEW STATUS:   PENDING APPROVAL",
            "",
            "EXECUTIVE SUMMARY",
            "-----------------------------------------------------------",
            "Pump P-102A was inspected during planned shutdown.",
            "Bearing vibration increased from 2.6 mm/s (baseline) to 7.4 mm/s RMS.",
            "This exceeds ISO 10816-3 Zone D limit of greater than 7.1 mm/s.",
            "Mechanical seal shows visible leakage of 3-5 drops per minute.",
            "Impeller wear ring clearance measured at 0.82 mm.",
            "Allowable limit is 0.60 mm per SOP-402 Rev 4.",
            "",
            "RECOMMENDATION: Immediate controlled shutdown and replacement.",
            "",
            "RISK LEVEL: HIGH",
            "ACTION: IMMEDIATE CONTROLLED SHUTDOWN AND REPLACEMENT",
        ],
    ),
    # Page 2: Vibration & Temperature
    (
        "VIBRATION AND TEMPERATURE MEASUREMENTS",
        [
            "Vibration Data - ISO 10816-3 Classification",
            "-----------------------------------------------------------",
            "Date        Location                Vib mm/s  Zone  Status",
            "2026-03-10  Drive-End Bearing       2.6       A     ACCEPTABLE",
            "2026-05-15  Drive-End Bearing       3.1       B     ACCEPTABLE",
            "2026-07-20  Drive-End Bearing       4.2       B     MONITOR",
            "2026-08-28  Drive-End Bearing       5.8       C     ACTION REQUIRED",
            "2026-09-04  Drive-End Bearing       7.4       D     DANGER ZONE D",
            "2026-09-04  Non-Drive-End Bearing   4.9       C     ACTION REQUIRED",
            "",
            "Temperature Readings",
            "-----------------------------------------------------------",
            "Bearing Housing Drive-End:       87C   Limit 80C   STATUS EXCEEDED",
            "Bearing Housing Non-Drive-End:   74C   Limit 80C   STATUS ACCEPTABLE",
            "Pump Casing:                     68C   Normal <85C STATUS ACCEPTABLE",
            "Motor Winding:                   91C   Limit 95C   STATUS CAUTION",
        ],
    ),
    # Page 3: Seal & Checklist
    (
        "MECHANICAL SEAL AND SOP-402 INSPECTION CHECKLIST",
        [
            "Mechanical Seal Condition",
            "-----------------------------------------------------------",
            "Seal Type:          John Crane Type 21 Single Mechanical",
            "Seal Leakage Rate:  3-5 drops per minute (LIMIT less than 1 drop per min) EXCEEDED",
            "Seal Face Cond:     Moderate scoring visible on stationary face",
            "Gland Plate:        Corrosion pitting observed - replacement recommended",
            "Flushing Line:      Clear, no blockage",
            "Quench Pot:         Residue buildup - cleaned during inspection",
            "Seal Flush Plan:    API Plan 11 operational",
            "",
            "SOP-402 INSPECTION CHECKLIST Rev 4",
            "-----------------------------------------------------------",
            "[X] FAIL  Bearing vibration within Zone A/B         7.4 mm/s Zone D",
            "[X] FAIL  Bearing temperature less than 80C         87C on DE bearing",
            "[X] FAIL  Mechanical seal leakage <1 drop per min   3-5 drops per minute",
            "[X] FAIL  Impeller wear ring clearance <0.60 mm     0.82 mm measured",
            "[OK] PASS Coupling alignment within tolerance        0.03mm angular, 0.02mm parallel",
            "[OK] PASS Lube oil level adequate                   Level at max mark",
            "[OK] PASS Discharge pressure within rated range     8.2 bar rated 7.5-9.5 bar",
            "[OK] PASS Flow rate within rated range              380 m3/h rated 350-420 m3/h",
            "[X] FAIL  Noise level within 85 dB                  89 dB measured",
            "[OK] PASS Suction strainer clear                    Clean, no blockage",
        ],
    ),
    # Page 4: Conclusions & Approvals
    (
        "CONCLUSIONS RECOMMENDATIONS AND APPROVALS",
        [
            "Findings Summary",
            "-----------------------------------------------------------",
            "1. Bearing vibration at 7.4 mm/s RMS has entered ISO 10816-3 ZONE D Danger.",
            "   Trend analysis shows exponential growth over last 6 months.",
            "2. Drive-end bearing temperature at 87C exceeds SOP-402 maximum of 80C.",
            "3. Mechanical seal leakage at 3-5 drops per min exceeds allowable threshold.",
            "4. Wear ring clearance of 0.82 mm exceeds maximum allowable of 0.60 mm.",
            "5. Noise level at 89 dB exceeds occupational safety limit of 85 dB.",
            "",
            "Recommended Actions",
            "-----------------------------------------------------------",
            "A. Initiate immediate controlled shutdown procedure per SOP-118.",
            "B. Replace drive-end and non-drive-end bearings with FAG 6313-2Z.",
            "C. Replace mechanical seal assembly John Crane Type 21.",
            "D. Replace impeller wear rings both suction and pressure side.",
            "E. Re-align coupling after replacement target less than 0.05 mm TIR.",
            "F. Perform hydrostatic test after reassembly per SOP-402 Section 8.",
            "G. Estimated downtime 72-96 hours. Standby pump P-102B to be activated.",
            "",
            "SOP REFERENCES:",
            "SOP-402 Rev 4 - Centrifugal Pump Inspection and Maintenance",
            "SOP-118 Rev 2 - Emergency Shutdown and Isolation Procedures",
            "ISO 10816-3:2009 - Vibration Classification Zones A B C D",
            "",
            "APPROVALS",
            "-----------------------------------------------------------",
            "Inspector:       Ravi Shankar        ___________________  04-Sep-2026",
            "Lead Engineer:   A.K. Krishnan       ___________________  PENDING",
            "Maintenance Mgr: S. Venkatesh        ___________________  PENDING",
        ],
    ),
]


def _pdf_escape(text: str) -> bytes:
    """Escape text for PDF string literal (parentheses and backslash)."""
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", errors="replace")


def build_page_stream(title: str, lines: list) -> bytes:
    """Build a PDF content stream for one page."""
    parts = [b"BT\n/F1 12 Tf\n20 820 Td\n"]
    # Title
    parts.append(b"(" + _pdf_escape(title) + b") Tj\n")
    parts.append(b"/F1 9 Tf\n0 -18 Td\n")
    for line in lines:
        if line == "":
            parts.append(b"0 -6 Td\n")
        else:
            parts.append(b"(" + _pdf_escape(line) + b") Tj\n0 -13 Td\n")
    parts.append(b"ET\n")
    return b"".join(parts)


def build_pdf(pages: list) -> bytes:
    """Build a minimal but valid PDF 1.4 binary."""
    # Object layout:
    # 1 = Catalog, 2 = Pages, 3 = Font
    # 4,5 = page1_dict, page1_stream
    # 6,7 = page2_dict, page2_stream ...

    n_pages = len(pages)
    page_dict_ids = [4 + i * 2 for i in range(n_pages)]
    content_ids = [4 + i * 2 + 1 for i in range(n_pages)]
    total = 4 + n_pages * 2  # exclusive upper bound

    catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = b" ".join(f"{oid} 0 R".encode() for oid in page_dict_ids)
    pages_dict = (
        b"<< /Type /Pages /Kids [" + kids + b"] "
        b"/Count " + str(n_pages).encode() + b" >>"
    )
    font = (
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>"
    )

    # Build ordered object list: index = object number
    obj_bodies = {1: catalog, 2: pages_dict, 3: font}
    for i, (title, lines) in enumerate(pages):
        stream_bytes = build_page_stream(title, lines)
        stream_len = len(stream_bytes)
        obj_bodies[page_dict_ids[i]] = (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 595 842] "
            b"/Contents " + str(content_ids[i]).encode() + b" 0 R "
            b"/Resources << /Font << /F1 3 0 R >> >> >>"
        )
        obj_bodies[content_ids[i]] = (
            b"<< /Length " + str(stream_len).encode() + b" >>\nstream\n"
            + stream_bytes
            + b"\nendstream"
        )

    buf = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for obj_num in range(1, total):
        offsets[obj_num] = len(buf)
        buf += f"{obj_num} 0 obj\n".encode()
        buf += obj_bodies[obj_num]
        buf += b"\nendobj\n"

    xref_start = len(buf)
    buf += b"xref\n"
    buf += f"0 {total}\n".encode()
    buf += b"0000000000 65535 f \n"
    for obj_num in range(1, total):
        buf += f"{offsets[obj_num]:010d} 00000 n \n".encode()

    buf += b"trailer\n<< /Size " + str(total).encode() + b" /Root 1 0 R >>\n"
    buf += b"startxref\n" + str(xref_start).encode() + b"\n%%EOF\n"
    return bytes(buf)


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = build_pdf(PAGES)
    output.write_bytes(pdf_bytes)
    print(f"PDF created: {output}  ({len(pdf_bytes):,} bytes, {len(PAGES)} pages)")


if __name__ == "__main__":
    main()
