#!/usr/bin/env python3
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import re
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

HTML_FILE = "report.html"
OUTPUT_JSON = "nessus_vulnerabilities.json"

FIELDS = [
    "Host",
    "Name",
    "Description",
    "CVE",
    "CVSS",
    "Protocol",
    "Port",
    "Risk",
    "Remediation (Solution)",
    "Reference(See also)",
]

SEVERITY_COLORS = {
    "#91243E": "CRITICAL",
    "#DD4B50": "HIGH",
    "#F18C43": "MEDIUM",
    "#F8C851": "LOW",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value):
    """Normalize whitespace and remove unnecessary spaces."""
    if not value:
        return "N/A"

    value = re.sub(r"\s+", " ", value).strip()

    return value if value else "N/A"


def direct_text(element):
    """
    Return only direct text from an element.
    This avoids including text from nested clear/toggle divs.
    """
    if element is None:
        return "N/A"

    parts = []

    for text_node in element.find_all(string=True, recursive=False):
        text = text_node.strip()

        if text:
            parts.append(text)

    return clean_text(" ".join(parts))


def section_value(header):
    """
    Get the first meaningful content element after a details-header.
    Stops at the next details-header.
    """
    if header is None:
        return "N/A"

    for sibling in header.find_next_siblings():

        if sibling.name == "div" and "details-header" in sibling.get("class", []):
            break

        if sibling.name == "div":
            text = sibling.get_text(" ", strip=True)

            if text:
                return clean_text(text)

    return "N/A"


def find_header(container, header_text):
    """
    Find a details-header with exact normalized text.
    """
    for header in container.find_all(
        "div",
        class_="details-header"
    ):
        text = header.get_text(" ", strip=True)

        if text.strip().lower() == header_text.lower():
            return header

    return None


def find_section_text(container, header_text):
    """
    Extract the value after a named details-header.
    """
    header = find_header(container, header_text)

    return section_value(header)


def unique_join(values):
    """Remove duplicates while preserving order."""
    result = []
    seen = set()

    for value in values:
        value = clean_text(value)

        if value == "N/A":
            continue

        if value not in seen:
            seen.add(value)
            result.append(value)

    return "; ".join(result) if result else "N/A"


# ============================================================
# SEVERITY SUMMARY CHECK
# ============================================================

def get_severity_summary(soup):
    """
    Read the CRITICAL, HIGH, MEDIUM and LOW summary counts.

    The expected order in the report is:
    CRITICAL, HIGH, MEDIUM, LOW.

    The function uses the known background colors and reads
    the numeric value from the nested div.
    """

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for td in soup.find_all("td"):

        classes = td.get("class", [])

        if not classes:
            continue

        color = next(
            (
                class_name.upper()
                for class_name in classes
                if class_name.upper() in SEVERITY_COLORS
            ),
            None
        )

        if color is None:
            continue

        severity = SEVERITY_COLORS[color]

        value_div = td.find("div")

        if value_div is None:
            continue

        raw_value = value_div.get_text(strip=True)

        if raw_value.isdigit():

            severity_counts[severity] = int(raw_value)

    return severity_counts


def should_continue(severity_counts):
    """
    Continue only when at least one severity count is > 0.
    """

    return any(
        count > 0
        for count in severity_counts.values()
    )


# ============================================================
# HOST EXTRACTION
# ============================================================

def extract_host_from_ip_table(container, soup):
    """
    Find the host IP associated with a vulnerability.

    Nessus commonly places the IP table before the vulnerability
    header, outside the vulnerability's section-wrapper.

    Strategy:
    1. Search the complete document for all rows containing IP:.
    2. Find the nearest preceding IP row relative to the
       vulnerability container.
    3. Return the IP value from that row.
    """

    ip_rows = []

    for row in soup.find_all("tr"):

        cells = row.find_all("td", recursive=False)

        for index, cell in enumerate(cells):

            label = cell.get_text(
                " ",
                strip=True
            ).strip().lower()

            if label == "ip:" and index + 1 < len(cells):

                host = cells[index + 1].get_text(
                    " ",
                    strip=True
                )

                if re.fullmatch(
                    r"(?:\d{1,3}\.){3}\d{1,3}",
                    host
                ):

                    ip_rows.append(
                        (row, host)
                    )

                    break

    if not ip_rows:
        return "N/A"

    # Determine document order.
    container_position = container.sourceline or 0

    preceding_hosts = [
        (row, host)
        for row, host in ip_rows
        if (row.sourceline or 0) <= container_position
    ]

    if preceding_hosts:
        return preceding_hosts[-1][1]

    # Fallback: use the first discovered host.
    return ip_rows[0][1]


def extract_host_by_document_position(soup, container):
    """
    More reliable host association based on HTML element order.

    Finds the last IP row before the vulnerability container
    in the parsed document.
    """

    all_elements = soup.find_all(True)

    try:
        container_index = all_elements.index(container)
    except ValueError:
        return "N/A"

    latest_host = "N/A"

    for element in all_elements[:container_index + 1]:

        if element.name != "tr":
            continue

        cells = element.find_all("td", recursive=False)

        for index, cell in enumerate(cells):

            label = cell.get_text(
                " ",
                strip=True
            ).strip().lower()

            if label == "ip:" and index + 1 < len(cells):

                host = cells[index + 1].get_text(
                    " ",
                    strip=True
                )

                if re.fullmatch(
                    r"(?:\d{1,3}\.){3}\d{1,3}",
                    host
                ):
                    latest_host = host

    return latest_host


# ============================================================
# CVSS EXTRACTION
# ============================================================

def extract_cvss_v2(container):
    """
    Extract only CVSS v2.0 Base Score.

    Example:
    4.3 (CVSS2#AV:N/AC:M/Au:N/C:N/I:P/A:N)

    Output:
    4.3
    """

    header = find_header(
        container,
        "CVSS v2.0 Base Score"
    )

    if header is None:
        return "N/A"

    value = section_value(header)

    match = re.search(
        r"(?<!\d)(\d+(?:\.\d+)?)",
        value
    )

    return match.group(1) if match else "N/A"


# ============================================================
# CVE EXTRACTION
# ============================================================

def extract_cves(container):
    """
    Extract all CVE values from the References table.
    """

    references_header = find_header(
        container,
        "References"
    )

    if references_header is None:
        return "N/A"

    references_table = None

    for sibling in references_header.find_next_siblings():

        if sibling.name == "div" and "details-header" in sibling.get("class", []):
            break

        if sibling.name == "div":
            references_table = sibling.find("table")

            if references_table:
                break

    if references_table is None:
        return "N/A"

    cves = []

    for row in references_table.find_all("tr"):

        cells = row.find_all("td", recursive=False)

        if len(cells) < 2:
            continue

        reference_type = cells[0].get_text(
            " ",
            strip=True
        ).upper()

        reference_value = cells[1].get_text(
            " ",
            strip=True
        )

        if reference_type == "CVE":

            matches = re.findall(
                r"CVE-\d{4}-\d{4,}",
                reference_value,
                flags=re.IGNORECASE
            )

            cves.extend(matches)

    return unique_join(cves)


# ============================================================
# SEE ALSO EXTRACTION
# ============================================================

def extract_see_also(container):
    """
    Extract links from the See Also section.
    """

    header = find_header(
        container,
        "See Also"
    )

    if header is None:
        return "N/A"

    links = []

    for sibling in header.find_next_siblings():

        if sibling.name == "div" and "details-header" in sibling.get("class", []):
            break

        if sibling.name == "div":

            for anchor in sibling.find_all("a", href=True):

                href = anchor.get("href", "").strip()

                if href:
                    links.append(href)

    return unique_join(links)


# ============================================================
# PROTOCOL AND PORT EXTRACTION
# ============================================================

def extract_protocol_port(container):
    """
    Extract protocol and port from Plugin Output heading.

    Example:
    tcp/80/www

    Protocol = tcp
    Port = 80
    """

    plugin_output_header = find_header(
        container,
        "Plugin Output"
    )

    if plugin_output_header is None:
        return "N/A", "N/A"

    for sibling in plugin_output_header.find_next_siblings():

        if sibling.name == "div" and "details-header" in sibling.get("class", []):
            break

        if sibling.name == "h2":

            value = sibling.get_text(
                " ",
                strip=True
            )

            match = re.search(
                r"(?i)\b([a-z][a-z0-9+.-]*)/(\d{1,5})\b",
                value
            )

            if match:
                return match.group(1), match.group(2)

            return "N/A", "N/A"

    return "N/A", "N/A"


# ============================================================
# VULNERABILITY EXTRACTION
# ============================================================

def is_vulnerability_header(element):
    """
    Detect vulnerability header divs.

    Nessus vulnerability headers contain:
    - An ID such as id75
    - An onclick calling toggleSection(...)
    - A nested toggletext div
    """

    if element.name != "div":
        return False

    element_id = element.get("id", "")

    onclick = element.get("onclick", "")

    toggle = element.find(
        "div",
        id=re.compile(r".*-toggletext$")
    )

    return (
        bool(re.fullmatch(r"id\d+", element_id))
        and "toggleSection" in onclick
        and toggle is not None
    )


def extract_vulnerability_containers(soup):
    """
    Yield each vulnerability header and its corresponding
    section-wrapper container.
    """

    for header in soup.find_all("div"):

        if not is_vulnerability_header(header):
            continue

        header_id = header.get("id")

        container = soup.find(
            "div",
            id=f"{header_id}-container"
        )

        if container is None:
            continue

        name = direct_text(header)

        # Remove the visual toggle text from the name.
        name = re.sub(
            r"\s+-\s*$",
            "",
            name
        ).strip()

        # Remove leading Nessus plugin ID, for example:
        # "136929 - JQuery 1.2 < 3.5.0 Multiple XSS"
        # becomes:
        # "JQuery 1.2 < 3.5.0 Multiple XSS"
        name = re.sub(
            r"^\s*\d+\s*-\s*",
            "",
            name
        ).strip()

        yield header, container, clean_text(name)


def parse_vulnerability(host, container, name):
    """
    Parse one vulnerability.

    Entire vulnerability records are excluded when the Risk Factor
    is missing, None, N/A, or empty. Valid records retain Risk.
    """

    risk = find_section_text(
        container,
        "Risk Factor"
    )

    # IMPORTANT:
    # Do not create or append any JSON record for missing/None risk.
    normalized_risk = str(risk).strip().lower()

    if normalized_risk in ("", "none", "n/a", "null"):
        return None

    protocol, port = extract_protocol_port(container)

    record = {
        "Host": host,
        "Name": name,
        "Description": find_section_text(
            container,
            "Description"
        ),
        "CVE": extract_cves(container),
        "CVSS": extract_cvss_v2(container),
        "Protocol": protocol,
        "Port": port,
        "Risk": risk,
        "Remediation (Solution)": find_section_text(
            container,
            "Solution"
        ),
        "Reference(See also)": extract_see_also(
            container
        ),
    }

    return record


# ============================================================
# JSON OUTPUT
# ============================================================

def save_json(records, output_file):
    """Write extracted vulnerabilities to JSON."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="nessus-tool",
        description="Nessus HTML report generator. Produces JSON and optionally PDF.",
        add_help=False,
    )

    parser.add_argument("-h", "--help", action="help", help="show this help message and exit")
    parser.add_argument(
        "-pdf",
        metavar="FILE",
        nargs="?",
        const="nessus_vulnerabilities.pdf",
        help="Generate PDF report. FILE is the PDF filename.",
    )
    parser.add_argument(
        "-o",
        metavar="DIRECTORY",
        default=".",
        help="Directory for generated output files (default: current directory)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="nessus-tool 1.0.0",
    )
    parser.add_argument(
        "html_file",
        nargs="?",
        default=HTML_FILE,
        help="Nessus HTML input file (default: report.html)",
    )

    args = parser.parse_args()
    output_dir = Path(args.o)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = Path(args.html_file)

    if not html_path.exists():
        print(f"[-] HTML file not found: {html_path}")
        return 1

    print("=" * 60)
    print("Nessus HTML Report Generator")
    print("=" * 60)

    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    severity_counts = get_severity_summary(soup)
    print("\n[+] Severity Summary")
    for severity, count in severity_counts.items():
        print(f"    {severity}: {count}")

    if not should_continue(severity_counts):
        print("\n[-] All severity counts are 0.")
        print("[-] No further scraping required.")
        return 0

    print("\n[+] At least one severity count is greater than 0.")
    print("[+] Continuing vulnerability extraction...")

    records = []
    for header, container, name in extract_vulnerability_containers(soup):
        host = extract_host_by_document_position(soup, container)
        record = parse_vulnerability(host=host, container=container, name=name)

        if record is None:
            print(f"[-] Skipped: {host} | {name} | Risk is None")
            continue

        records.append(record)
        print(f"[+] Extracted: {host} | {name}")

    if not records:
        print("\n[-] No vulnerability sections found.")
        return 0

    # JSON is always generated. CSV and TXT are intentionally not generated.
    json_output = output_dir / OUTPUT_JSON
    save_json(records, json_output)

    print("\n[+] JSON extraction completed.")
    print(f"[+] Total vulnerabilities: {len(records)}")
    print(f"[+] JSON: {json_output}")

    # -pdf FILE generates the PDF from the JSON just created.
    if args.pdf is not None:
        try:
            from report import generate_pdf
        except ImportError as exc:
            print("\n[-] Could not import report.py.")
            print("[-] Keep report.py in the same directory as main(1).py.")
            print(f"[-] Details: {exc}")
            return 1

        pdf_name = Path(args.pdf).name
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name += ".pdf"

        pdf_output = output_dir / pdf_name
        print("\n[+] Generating PDF from JSON...")

        try:
            generate_pdf(json_output, pdf_output)
        except Exception as exc:
            print(f"[-] PDF generation failed: {exc}")
            return 1

        print(f"[+] PDF: {pdf_output}")

    print("\n[+] Completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
