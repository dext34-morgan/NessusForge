#!/usr/bin/env python3
"""
Create a Nessus-style PDF report from a JSON vulnerability report.

Only these severities are included:
    CRITICAL, HIGH, MEDIUM, LOW

Expected JSON format:
[
    {
        "Host": "192.168.100.1",
        "Name": "Vulnerability name",
        "Description": "Description",
        "CVE": "CVE-XXXX-XXXX",
        "CVSS": "10.0",
        "Protocol": "tcp",
        "Port": "445",
        "Risk": "Critical",
        "Remediation (Solution)": "Upgrade...",
        "Reference(See also)": "http://..."
    }
]

Usage:
    pip install reportlab
    python nessus_json_to_pdf.py report.json
    python nessus_json_to_pdf.py report.json -o report.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
import re
from collections import Counter
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    AnchorFlowable,
)

PAGE_SIZE = landscape(A4)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
LEFT_MARGIN = 14 * mm
RIGHT_MARGIN = 14 * mm
TOP_MARGIN = 12 * mm
BOTTOM_MARGIN = 12 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

NAVY = colors.HexColor("#073E5C")
LIGHT_GREY = colors.HexColor("#EDF1F2")
BODY_GREY = colors.HexColor("#555555")
BORDER_GREY = colors.HexColor("#D5D5D5")

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

SEVERITY_COLORS = {
    "CRITICAL": colors.HexColor("#91243E"),
    "HIGH": colors.HexColor("#DD4B50"),
    "MEDIUM": colors.HexColor("#F18C43"),
    "LOW": colors.HexColor("#F8C851"),
}


def clean(value):
    if value is None:
        return "N/A"
    return str(value).strip() or "N/A"


def normalize_multivalue(value):
    """Convert a JSON string/list of hosts or references into readable text."""
    if value is None:
        return "N/A"

    if isinstance(value, (list, tuple, set)):
        values = [clean(item) for item in value if clean(item) != "N/A"]
        return "; ".join(dict.fromkeys(values)) if values else "N/A"

    return clean(value)


def normalize_hosts(value):
    """Keep all hosts when Host is a list or a delimited string."""
    if isinstance(value, (list, tuple, set)):
        hosts = [clean(item) for item in value if clean(item) != "N/A"]
        return "; ".join(dict.fromkeys(hosts)) if hosts else "N/A"

    value = clean(value)
    if value == "N/A":
        return value

    # Support common formats: comma, semicolon, newline, or pipe separated.
    parts = [part.strip() for part in re.split(r"[,;|\n]+", value) if part.strip()]
    return "; ".join(dict.fromkeys(parts)) if parts else "N/A"


def normalize_cves(value):
    """Return all CVE IDs in a readable, de-duplicated form."""
    if value is None:
        return "N/A"

    if isinstance(value, (list, tuple, set)):
        raw = " ".join(str(item) for item in value)
    else:
        raw = str(value)

    cves = re.findall(r"CVE-\d{4}-\d{4,}", raw, flags=re.IGNORECASE)
    if cves:
        normalized = []
        for cve in cves:
            cve = cve.upper()
            if cve not in normalized:
                normalized.append(cve)
        return "; ".join(normalized)

    return clean(value)


def cve_list(value):
    normalized = normalize_cves(value)
    if normalized == "N/A":
        return []
    return [item.strip() for item in normalized.split(";") if item.strip()]


def normalize_severity(value):
    value = clean(value).upper()
    for item in SEVERITIES:
        if item in value:
            return item
    return None


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        # Support either {"vulnerabilities": [...]} or a single object.
        if isinstance(data.get("vulnerabilities"), list):
            data = data["vulnerabilities"]
        else:
            data = [data]

    if not isinstance(data, list):
        raise ValueError("JSON must contain an array of vulnerability objects.")

    valid = []
    skipped = 0

    for item in data:
        if not isinstance(item, dict):
            skipped += 1
            continue

        risk = normalize_severity(item.get("Risk"))
        if risk not in SEVERITIES:
            skipped += 1
            continue

        record = {
            "Host": normalize_hosts(item.get("Host")),
            "Name": clean(item.get("Name")),
            "Description": clean(item.get("Description")),
            "CVE": normalize_cves(item.get("CVE")),
            "CVSS": clean(item.get("CVSS")),
            "Protocol": clean(item.get("Protocol")),
            "Port": clean(item.get("Port")),
            "Risk": risk.title(),
            "Remediation (Solution)": clean(item.get("Remediation (Solution)")),
            "Reference(See also)": normalize_multivalue(item.get("Reference(See also)")),
        }
        valid.append(record)

    return valid, skipped


class NessusPDF(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=PAGE_SIZE,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            title="Nessus JSON Vulnerability Report",
            author="Nessus JSON to PDF Generator",
        )

        frame = Frame(
            LEFT_MARGIN,
            BOTTOM_MARGIN,
            CONTENT_WIDTH,
            PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
            id="main",
        )

        self.addPageTemplates([
            PageTemplate(
                id="nessus",
                frames=[frame],
                onPage=self.draw_footer,
            )
        ])

    @staticmethod
    def draw_footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN,
            7 * mm,
            f"Page {document.page}",
        )
        canvas.restoreState()


def make_styles():
    base = getSampleStyleSheet()

    return {
        "host": ParagraphStyle(
            "Host",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=22,
            textColor=colors.white,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=NAVY,
        ),
        "summary_label": ParagraphStyle(
            "SummaryLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            alignment=1,
            textColor=NAVY,
        ),
        "summary_value": ParagraphStyle(
            "SummaryValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            alignment=1,
        ),
        "detail_title": ParagraphStyle(
            "DetailTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
        ),
        "field_label": ParagraphStyle(
            "FieldLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=NAVY,
        ),
        "field_value": ParagraphStyle(
            "FieldValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=BODY_GREY,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=BODY_GREY,
        ),
    }


def para(value, style):
    # ReportLab Paragraph supports basic markup. Escaping prevents JSON
    # content such as "<" and "&" from being interpreted as markup.
    return Paragraph(escape(clean(value)), style)


def colored_bar(label, width, height, background, style):
    table = Table(
        [[para(label, style)]],
        colWidths=[width],
        rowHeights=[height],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    return table


def host_parts(value):
    """Return unique host values from a normalized host string."""
    parts = []
    for host in re.split(r";\s*", clean(value)):
        host = host.strip()
        if host and host not in parts:
            parts.append(host)
    return parts


def anchor_id(record_index):
    """Create a stable internal PDF destination for a finding."""
    return f"finding_{record_index}"


def summary_index(records, width, st):
    """Create a clickable severity/host index for the summary page."""
    rows = [[
        para("Severity", st["summary_label"]),
        para("Host IP", st["summary_label"]),
        para("Findings", st["summary_label"]),
    ]]

    # First occurrence of each severity + host is the jump destination.
    destinations = {}
    counts = Counter()
    for index, record in enumerate(records):
        risk = record["Risk"].upper()
        for host in host_parts(record["Host"]):
            key = (risk, host)
            counts[key] += 1
            destinations.setdefault(key, anchor_id(index))

    for risk in SEVERITIES:
        matching_hosts = sorted(
            host for (severity, host) in counts if severity == risk
        )
        for host in matching_hosts:
            key = (risk, host)
            destination = destinations[key]
            link_text = escape(host)
            linked_host = Paragraph(
                f'<link href="#{destination}" color="#073E5C"><u>{link_text}</u></link>',
                st["field_value"],
            )
            rows.append([
                para(risk.title(), st["field_label"]),
                linked_host,
                para(counts[key], st["field_value"]),
            ])

    if len(rows) == 1:
        rows.append([
            para("N/A", st["field_value"]),
            para("N/A", st["field_value"]),
            para("0", st["field_value"]),
        ])

    table = Table(
        rows,
        colWidths=[38 * mm, width - 38 * mm - 35 * mm, 35 * mm],
        repeatRows=1,
    )
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F7F8F9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]

    for row_index in range(1, len(rows)):
        risk = rows[row_index][0].getPlainText().upper()
        if risk in SEVERITY_COLORS:
            commands.append(("TEXTCOLOR", (0, row_index), (0, row_index), SEVERITY_COLORS[risk]))

    table.setStyle(TableStyle(commands))
    return table


def summary_table(records, width, st):
    counts = Counter(record["Risk"].upper() for record in records)
    labels = ["Critical", "High", "Medium", "Low", "Total"]
    keys = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "TOTAL"]

    values = [
        counts.get("CRITICAL", 0),
        counts.get("HIGH", 0),
        counts.get("MEDIUM", 0),
        counts.get("LOW", 0),
        len(records),
    ]

    label_row = [para(label, st["summary_label"]) for label in labels]
    value_row = []

    for key, value in zip(keys, values):
        value_style = ParagraphStyle(
            "SummaryValue" + key,
            parent=st["summary_value"],
            textColor=SEVERITY_COLORS.get(key, NAVY),
        )
        value_row.append(para(value, value_style))

    table = Table(
        [label_row, value_row],
        colWidths=[width / 5] * 5,
        rowHeights=[8 * mm, 10 * mm],
    )
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def vulnerability_block(record, st, record_index):
    risk = record["Risk"].upper()
    risk_color = SEVERITY_COLORS[risk]

    cves = cve_list(record.get("CVE"))
    if len(cves) > 1:
        cve_heading = " | " + ", ".join(cves)
    else:
        cve_heading = ""

    title = (
        f'{record["Host"]} | {record["Risk"]}: '
        f'{record["Name"]}{cve_heading}'
    )
    title_table = Table(
        [[para(title, st["detail_title"])]],
        colWidths=[CONTENT_WIDTH],
    )
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))

    fields = [
        ("Host", record["Host"]),
        ("Name", record["Name"]),
        ("Description", record["Description"]),
        ("CVE", record["CVE"]),
        ("CVSS", record["CVSS"]),
        ("Protocol", record["Protocol"]),
        ("Port", record["Port"]),
        ("Risk", record["Risk"]),
        ("Remediation (Solution)", record["Remediation (Solution)"]),
        ("Reference(See also)", record["Reference(See also)"]),
    ]

    rows = []
    for label, value in fields:
        rows.append([
            para(label, st["field_label"]),
            para(value, st["field_value"]),
        ])

    detail_table = Table(
        rows,
        colWidths=[47 * mm, CONTENT_WIDTH - 47 * mm],
        repeatRows=0,
    )

    commands = [
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7F8F9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]

    # Add a colored left marker for the risk field.
    risk_row = next(index for index, row in enumerate(fields) if row[0] == "Risk")
    commands.append(("BACKGROUND", (0, risk_row), (0, risk_row), risk_color))
    commands.append(("TEXTCOLOR", (0, risk_row), (0, risk_row), colors.white))

    detail_table.setStyle(TableStyle(commands))

    return KeepTogether([
        AnchorFlowable(anchor_id(record_index)),
        title_table,
        detail_table,
        Spacer(1, 5 * mm),
    ])


def generate_pdf(input_json, output_pdf):
    records, skipped = load_json(input_json)

    if not records:
        raise ValueError(
            "No Critical, High, Medium, or Low vulnerability objects were found."
        )

    host_values = []
    for record in records:
        for host in re.split(r";\s*", record["Host"]):
            host = host.strip()
            if host and host not in host_values:
                host_values.append(host)

    host_title = ", ".join(host_values) if len(host_values) <= 3 else f"{len(host_values)} hosts"

    st = make_styles()
    story = [
        colored_bar(host_title, CONTENT_WIDTH, 9 * mm, NAVY, st["host"]),
        colored_bar("Summary", CONTENT_WIDTH, 8 * mm, LIGHT_GREY, st["section"]),
        Spacer(1, 2 * mm),
        summary_table(records, CONTENT_WIDTH, st),
        Spacer(1, 5 * mm),
        colored_bar("Findings Index - Click a Host IP to Jump to Details", CONTENT_WIDTH, 8 * mm, LIGHT_GREY, st["section"]),
        Spacer(1, 2 * mm),
        summary_index(records, CONTENT_WIDTH, st),
        Spacer(1, 5 * mm),
        colored_bar("Details", CONTENT_WIDTH, 8 * mm, LIGHT_GREY, st["section"]),
        Spacer(1, 3 * mm),
    ]

    for record_index, record in enumerate(records):
        story.append(vulnerability_block(record, st, record_index))

    document = NessusPDF(str(output_pdf))
    document.build(story)

    return records, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Create a Nessus-style PDF from a JSON vulnerability report."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to the JSON vulnerability report",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PDF path; defaults to the input JSON name with .pdf",
    )
    args = parser.parse_args()

    if not args.input_json.exists():
        print(f"[!] Input JSON does not exist: {args.input_json}", file=sys.stderr)
        return 1

    output_pdf = args.output or args.input_json.with_suffix(".pdf")

    try:
        records, skipped = generate_pdf(args.input_json, output_pdf)
    except json.JSONDecodeError as exc:
        print(f"[!] Invalid JSON: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[!] PDF generation failed: {exc}", file=sys.stderr)
        return 1

    counts = Counter(record["Risk"].upper() for record in records)

    print(f"[+] PDF created: {output_pdf}")
    print(f"[+] Included vulnerabilities: {len(records)}")
    print(f"[+] Skipped objects: {skipped}")
    print(
        "[+] Included severity counts: "
        f"Critical={counts.get('CRITICAL', 0)}, "
        f"High={counts.get('HIGH', 0)}, "
        f"Medium={counts.get('MEDIUM', 0)}, "
        f"Low={counts.get('LOW', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
