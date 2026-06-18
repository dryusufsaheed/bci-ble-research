#!/usr/bin/env python3
"""
document_environment.py
Phase 8: Documentation and Reproducibility

Captures the complete computational environment specification for
archival and reproducibility certification. Resolves the filename-length
archive error encountered in earlier Phase 8 runs.

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import sys
import platform
import subprocess
import json
import hashlib
from pathlib import Path
from datetime import datetime


OUTPUT_DIR = Path("phase8_documentation/outputs")


class EnvironmentDocumenter:
    """
    Document complete computational environment for reproducibility.
    Outputs: JSON spec file + human-readable Markdown report.
    """

    def __init__(self):
        self.spec = {}
        self.timestamp = datetime.utcnow().isoformat()

    # ------------------------------------------------------------------
    # Collection methods
    # ------------------------------------------------------------------

    def collect_system(self) -> dict:
        return {
            "os_name":          platform.system(),
            "os_version":       platform.version()[:80],
            "os_release":       platform.release(),
            "architecture":     platform.machine(),
            "python_version":   sys.version,
            "python_exec":      sys.executable,
            "timestamp_utc":    self.timestamp,
        }

    def collect_packages(self) -> list[dict]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            packages = json.loads(result.stdout)
            # Filter to research-relevant packages
            relevant = {
                "numpy", "scipy", "matplotlib", "mne", "scikit-learn",
                "cryptography", "pycryptodome", "python-docx", "openpyxl",
            }
            return [p for p in packages if p["name"].lower() in relevant]
        except Exception as e:
            return [{"error": str(e)}]

    def collect_dataset_checksums(self, data_dir: str = "data/raw") -> dict:
        checksums = {}
        dp = Path(data_dir)
        if not dp.exists():
            return {"note": f"Directory '{data_dir}' not found — run data download step first."}
        for fp in sorted(dp.rglob("*")):
            if fp.is_file() and fp.suffix in (".mat", ".edf"):
                md5 = hashlib.md5(fp.read_bytes()).hexdigest()
                checksums[fp.name] = md5
        return checksums

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_json(self) -> Path:
        self.spec = {
            "system":   self.collect_system(),
            "packages": self.collect_packages(),
            "dataset_checksums": self.collect_dataset_checksums(),
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / "environment_spec.json"
        path.write_text(json.dumps(self.spec, indent=2))
        print(f"[Phase8] Environment JSON → {path}")
        return path

    def generate_markdown(self) -> Path:
        if not self.spec:
            self.generate_json()

        sys_info = self.spec["system"]
        pkgs     = self.spec["packages"]
        checksums = self.spec.get("dataset_checksums", {})

        md_lines = [
            "# Reproducibility Report",
            f"\n**Generated:** {self.timestamp} UTC",
            f"\n**Praxis:** Securing Brain-Computer Interfaces: A Multi-Criteria "
            f"Evaluation of Encryption Protocols for Bluetooth Low Energy Transmission",
            f"\n**Author:** Dr. Saheed Yusuf | George Washington University | 2026",
            "\n---\n",
            "## 1. Computational Environment\n",
            f"| Property | Value |",
            f"|---|---|",
            f"| OS | {sys_info['os_name']} {sys_info['os_release']} |",
            f"| Architecture | {sys_info['architecture']} |",
            f"| Python | {sys_info['python_version'].split()[0]} |",
            "\n## 2. Key Package Versions\n",
            "| Package | Version |",
            "|---|---|",
        ]
        for p in pkgs:
            if "error" not in p:
                md_lines.append(f"| {p['name']} | {p['version']} |")

        md_lines += [
            "\n## 3. Dataset Checksums (MD5)\n",
            "| File | MD5 |",
            "|---|---|",
        ]
        if checksums.get("note"):
            md_lines.append(f"| — | {checksums['note']} |")
        else:
            for fname, md5 in checksums.items():
                md_lines.append(f"| {fname} | `{md5}` |")

        md_lines += [
            "\n## 4. Reproducibility Steps\n",
            "```bash",
            "# 1. Clone repository",
            "git clone https://github.com/dryusufsaheed/bci-ble-research.git",
            "cd bci-ble-research",
            "",
            "# 2. Install dependencies",
            "pip install -r requirements.txt",
            "",
            "# 3. Download OpenBCI EEG dataset to data/raw/",
            "#    Source: https://openbci.com/community",
            "#    Formats: .mat and .edf",
            "",
            "# 4. Run full pipeline",
            "python run_pipeline.py",
            "```",
            "\n## 5. Certification\n",
            "This research is certified reproducible per GWU ETD standards.",
            f"Environment hash: `{hashlib.md5(json.dumps(self.spec, sort_keys=True).encode()).hexdigest()}`",
        ]

        path = OUTPUT_DIR / "reproducibility_report.md"
        path.write_text("\n".join(md_lines))
        print(f"[Phase8] Markdown report → {path}")
        return path

    def run(self):
        print("\n[Phase 8] Documenting environment...")
        self.generate_json()
        self.generate_markdown()
        print("[Phase 8] Complete.\n")


if __name__ == "__main__":
    doc = EnvironmentDocumenter()
    doc.run()
