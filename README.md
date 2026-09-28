# NessusForge

NessusForge is a lightweight Python-based tool for parsing **Nessus HTML vulnerability reports** and converting the extracted vulnerability information into structured **JSON**. It can optionally generate a formatted **PDF vulnerability report** from the generated JSON.

The tool is designed for security professionals, penetration testers, vulnerability analysts, and security teams who need a simple way to transform Nessus HTML reports into reusable JSON and professional PDF reports.

---

## Features

- Parse Nessus HTML reports
- Extract vulnerability information automatically
- Generate structured JSON output
- Optional PDF report generation
- Supports multiple hosts
- Supports multiple CVEs per vulnerability
- Extracts:
  - Host
  - Vulnerability Name
  - Description
  - CVE
  - CVSS v2 Base Score
  - Protocol
  - Port
  - Risk
  - Remediation / Solution
  - Reference / See Also
- Supports:
  - Critical
  - High
  - Medium
  - Low
- Automatically ignores vulnerabilities where the Nessus `Risk Factor` is missing or `None`
- Clickable vulnerability index in generated PDF reports
- Custom output directory
- Command-line interface
- Version information
- Works on Linux, macOS, and Windows

---

## Requirements

### Python

Python **3.9 or newer** is recommended.

Check your Python version:

```bash
python3 --version
````

On Windows:

```cmd
python --version
```

---

# Installation

## Linux

Clone the repository:

```bash
git clone https://github.com/dext34-morgan/NessusForge.git
cd NessusForge
```

Make the installation script executable:

```bash
chmod +x install.sh
```

Run the installer:

```bash
./install.sh
```

The installer will:

1. Check for the NessusForge files
2. Install Python dependencies
3. Make the main script executable
4. Create a symbolic link named `nessusforge`
5. Install the command into:

```text
~/.local/bin/nessusforge
```

After installation, verify the tool:

```bash
nessusforge --version
```

Display help:

```bash
nessusforge --help
```

### PATH Configuration

If the installer reports that `~/.local/bin` is not in your `PATH`, add it to your shell configuration.

For Bash:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For Zsh:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Then verify:

```bash
nessusforge --version
```

---

# Installation on macOS

NessusForge works on both Intel and Apple Silicon Macs.

Clone the repository:

```bash
git clone https://github.com/dext34-morgan/NessusForge.git
cd NessusForge
```

Make the installer executable:

```bash
chmod +x install.sh
```

Run:

```bash
./install.sh
```

Verify the installation:

```bash
nessusforge --version
```

Display help:

```bash
nessusforge --help
```

### macOS PATH

If `nessusforge` is not found after installation, add `~/.local/bin` to your PATH.

For Zsh:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Then:

```bash
nessusforge --version
```

---

# Installation on Windows

Clone the repository:

```cmd
git clone https://github.com/dext34-morgan/NessusForge.git
cd NessusForge
```

Run the Windows installer:

```cmd
install.bat
```

The installer will:

1. Check for `main.py`
2. Check for `requirements.txt`
3. Install Python dependencies
4. Create a Windows directory junction
5. Create a `nessusforge.cmd` launcher

After installation, verify:

```cmd
nessusforge --version
```

Display help:

```cmd
nessusforge --help
```

---

## Windows PATH

The installer creates the launcher in:

```text
%USERPROFILE%\bin
```

If Windows cannot find `nessusforge`, add this directory to your user `PATH`:

```text
%USERPROFILE%\bin
```

After updating the PATH, open a **new Command Prompt or PowerShell window**.

Then run:

```cmd
nessusforge --version
```

---

# Usage

## Linux / macOS

### Basic Usage

Place your Nessus HTML report in the current directory as:

```text
report.html
```

Run:

```bash
nessusforge
```

The tool generates:

```text
nessus_vulnerabilities.json
```

---

### Specify an HTML Report

You can provide a Nessus HTML file explicitly:

```bash
nessusforge report.html
```

For example:

```bash
nessusforge scan-192.168.1.0.html
```

---

### Generate JSON and PDF

Use the `-pdf` option:

```bash
nessusforge report.html -pdf report.pdf
```

This generates:

```text
nessus_vulnerabilities.json
report.pdf
```

---

### Specify an Output Directory

Use `-o`:

```bash
nessusforge report.html -o results
```

The output will be:

```text
results/
└── nessus_vulnerabilities.json
```

---

### JSON + PDF + Custom Output Directory

```bash
nessusforge report.html -pdf report.pdf -o results
```

Output:

```text
results/
├── nessus_vulnerabilities.json
└── report.pdf
```

---

### Check Version

```bash
nessusforge --version
```

or:

```bash
nessusforge -v
```

---

### Display Help

```bash
nessusforge --help
```

---

# Windows Usage

The same commands can be used from Command Prompt or PowerShell.

### Basic Usage

If the report is named:

```text
report.html
```

run:

```cmd
nessusforge
```

Output:

```text
nessus_vulnerabilities.json
```

---

### Specify a Nessus HTML File

```cmd
nessusforge report.html
```

For example:

```cmd
nessusforge nessus-scan.html
```

---

### Generate JSON and PDF

```cmd
nessusforge report.html -pdf report.pdf
```

Output:

```text
nessus_vulnerabilities.json
report.pdf
```

---

### Specify an Output Directory

```cmd
nessusforge report.html -o results
```

Output:

```text
results\
└── nessus_vulnerabilities.json
```

---

### Generate JSON and PDF in a Custom Directory

```cmd
nessusforge report.html -pdf report.pdf -o results
```

Output:

```text
results\
├── nessus_vulnerabilities.json
└── report.pdf
```

---

### Check Version

```cmd
nessusforge --version
```

or:

```cmd
nessusforge -v
```

---

### Display Help

```cmd
nessusforge --help
```

---

# Command Reference

| Command                                              | Description                               |
| ---------------------------------------------------- | ----------------------------------------- |
| `nessusforge`                                        | Parse the default `report.html`           |
| `nessusforge report.html`                            | Parse a specified Nessus HTML report      |
| `nessusforge -pdf report.pdf`                        | Generate JSON and PDF                     |
| `nessusforge report.html -pdf report.pdf`            | Parse HTML and generate PDF               |
| `nessusforge -o results`                             | Store output in `results/`                |
| `nessusforge report.html -o results`                 | Parse report and store JSON in `results/` |
| `nessusforge report.html -pdf report.pdf -o results` | Generate JSON and PDF in `results/`       |
| `nessusforge -v`                                     | Display version                           |
| `nessusforge --version`                              | Display version                           |
| `nessusforge -h`                                     | Display help                              |
| `nessusforge --help`                                 | Display help                              |

---

# Output

## JSON

The generated JSON file is:

```text
nessus_vulnerabilities.json
```

Each vulnerability contains:

```json
{
    "Host": "192.168.100.2",
    "Name": "JQuery 1.2 < 3.5.0 Multiple XSS",
    "Description": "...",
    "CVE": "CVE-2020-11022, CVE-2020-11023",
    "CVSS": "5.0",
    "Protocol": "tcp",
    "Port": "80",
    "Risk": "Medium",
    "Remediation (Solution)": "...",
    "Reference(See also)": "..."
}
```

---

# PDF Report

When the `-pdf` option is used, NessusForge generates a formatted PDF report using the generated JSON data.

The PDF includes:

* Vulnerability summary
* Severity information
* Host information
* Vulnerability names
* CVE information
* CVSS scores
* Protocol and port
* Risk
* Description
* Remediation
* References
* Multiple hosts
* Multiple CVEs
* Clickable findings index

Example vulnerability heading:

```text
192.168.100.2 | Medium: JQuery 1.2 < 3.5.0 Multiple XSS | CVE-2020-11022, CVE-2020-11023
```

---

# Supported Severity Levels

NessusForge processes the following severity levels:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

The tool uses the severity information from the Nessus HTML report to determine whether vulnerability processing should continue.

---

# Project Structure

```text
NessusForge/
│
├── main.py
│   └── Main Nessus HTML parser and CLI
│
├── report.py
│   └── JSON-to-PDF report generator
│
├── requirements.txt
│   └── Python dependencies
│
├── install.sh
│   └── Linux/macOS installation script
│
├── install.bat
│   └── Windows installation script
│
└── README.md
    └── Project documentation
```

---

# Example Workflow

## Linux / macOS

```bash
git clone https://github.com/dext34-morgan/NessusForge.git
cd NessusForge

chmod +x install.sh
./install.sh

nessusforge report.html -pdf report.pdf -o results
```

Result:

```text
results/
├── nessus_vulnerabilities.json
└── report.pdf
```

---

## Windows

```cmd
git clone https://github.com/dext34-morgan/NessusForge.git
cd NessusForge

install.bat

nessusforge report.html -pdf report.pdf -o results
```

Result:

```text
results\
├── nessus_vulnerabilities.json
└── report.pdf
```

---

# Troubleshooting

## `nessusforge: command not found`

On Linux/macOS, check whether `~/.local/bin` is in your PATH:

```bash
echo $PATH
```

Add it if necessary:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

For a permanent configuration, add the same line to your shell configuration file.

---

## Windows: `'nessusforge' is not recognized`

Check that:

```text
%USERPROFILE%\bin
```

is included in your Windows PATH.

After modifying PATH, open a new terminal.

---

## Python Not Found

Check:

```bash
python3 --version
```

or:

```bash
python --version
```

On Windows:

```cmd
python --version
```

Install Python if it is not available.

---

## Missing Python Dependencies

Run:

### Linux/macOS

```bash
python3 -m pip install -r requirements.txt
```

### Windows

```cmd
python -m pip install -r requirements.txt
```

---

# Version

Current version:

```text
1.0.0
```

Check the installed version:

```bash
nessusforge --version
```

---

# License

Add your preferred license here.

For example:

```text
MIT License
```

---

# Disclaimer

NessusForge is intended for authorized security assessment, vulnerability management, and defensive security purposes.

Only use NessusForge with vulnerability reports and systems that you are authorized to assess.

```
```
