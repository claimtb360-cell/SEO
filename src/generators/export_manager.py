"""Export Manager - Generate PDF, JSON, CSV reports from analysis data."""

import json
import csv
import io
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExportManager:
    """Generate PDF, JSON, CSV reports from SEO analysis data."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Export full structured data as JSON."""
        if not filename:
            filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self.output_dir, filename)
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "seo_analysis",
            **data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filepath

    def export_json_string(self, data: Dict[str, Any]) -> str:
        """Export as JSON string (for API response)."""
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "seo_analysis",
            **data,
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)


    def export_csv(self, data: Dict[str, Any], data_type: str = "full",
                   filename: Optional[str] = None) -> str:
        """
        Export flat table format as CSV.

        Args:
            data: Analysis data dictionary.
            data_type: One of 'links', 'headings', 'images', 'keywords', 'full'.
            filename: Optional output filename.

        Returns:
            Filepath of the generated CSV.
        """
        if not filename:
            filename = f"seo_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(self.output_dir, filename)

        rows = self._extract_csv_rows(data, data_type)

        if rows:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                f.write("No data available for this export type.\n")

        return filepath

    def export_csv_string(self, data: Dict[str, Any], data_type: str = "full") -> str:
        """Export as CSV string (for API response)."""
        rows = self._extract_csv_rows(data, data_type)
        if not rows:
            return "No data available.\n"

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _extract_csv_rows(self, data: Dict[str, Any], data_type: str) -> List[Dict]:
        """Extract rows for CSV based on data type."""
        rows = []

        if data_type == "links":
            links_data = data.get("categories", {}).get("links", {}).get("factors", [])
            for factor in links_data:
                rows.append({
                    "factor": factor.get("name", ""),
                    "passed": factor.get("passed", ""),
                    "score": factor.get("score", 0),
                    "message": factor.get("message", ""),
                    "recommendation": factor.get("recommendation", ""),
                })

        elif data_type == "headings":
            headings_data = data.get("categories", {}).get("headings_structure", {}).get("factors", [])
            for factor in headings_data:
                rows.append({
                    "factor": factor.get("name", ""),
                    "passed": factor.get("passed", ""),
                    "score": factor.get("score", 0),
                    "message": factor.get("message", ""),
                    "recommendation": factor.get("recommendation", ""),
                })

        elif data_type == "images":
            images_data = data.get("categories", {}).get("images_media", {}).get("factors", [])
            for factor in images_data:
                rows.append({
                    "factor": factor.get("name", ""),
                    "passed": factor.get("passed", ""),
                    "score": factor.get("score", 0),
                    "message": factor.get("message", ""),
                    "recommendation": factor.get("recommendation", ""),
                })

        elif data_type == "keywords":
            kw_data = data.get("categories", {}).get("content_keywords", {}).get("factors", [])
            for factor in kw_data:
                rows.append({
                    "factor": factor.get("name", ""),
                    "passed": factor.get("passed", ""),
                    "score": factor.get("score", 0),
                    "message": factor.get("message", ""),
                    "recommendation": factor.get("recommendation", ""),
                })

        else:  # full
            categories = data.get("categories", {})
            for cat_name, cat_data in categories.items():
                for factor in cat_data.get("factors", []):
                    rows.append({
                        "category": cat_name,
                        "factor": factor.get("name", ""),
                        "passed": factor.get("passed", ""),
                        "score": factor.get("score", 0),
                        "message": factor.get("message", ""),
                        "priority": factor.get("priority", ""),
                        "recommendation": factor.get("recommendation", ""),
                    })

        return rows


    def export_pdf(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Export as PDF using simple HTML template.

        Generates an HTML file that can be printed to PDF from browser.
        No external PDF library dependency.
        """
        if not filename:
            filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        filepath = os.path.join(self.output_dir, filename)
        html_content = self._generate_pdf_html(data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath

    def export_pdf_string(self, data: Dict[str, Any]) -> str:
        """Export as HTML string formatted for PDF printing."""
        return self._generate_pdf_html(data)

    def _generate_pdf_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML report formatted for PDF printing."""
        url = data.get("url", "Unknown")
        overall_score = data.get("overall_score", 0)
        categories = data.get("categories", {})
        recommendations = data.get("recommendations", [])
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build category sections
        category_html = ""
        for cat_name, cat_data in categories.items():
            cat_score = cat_data.get("score", 0)
            passed = cat_data.get("passed_count", 0)
            total = cat_data.get("total_count", 0)
            color = "#22c55e" if cat_score >= 80 else "#eab308" if cat_score >= 60 else "#ef4444"

            factors_html = ""
            for factor in cat_data.get("factors", []):
                icon = "&#10004;" if factor.get("passed") else "&#10008;"
                icon_color = "#22c55e" if factor.get("passed") else "#ef4444"
                factors_html += f"""
                <tr>
                    <td style="color:{icon_color};font-size:16px;width:30px;">{icon}</td>
                    <td><strong>{factor.get('name', '')}</strong></td>
                    <td>{factor.get('score', 0)}/100</td>
                    <td>{factor.get('message', '')}</td>
                </tr>"""

            category_html += f"""
            <div class="category">
                <h3 style="color:{color};">{cat_name.replace('_', ' ').title()} — {cat_score}/100 ({passed}/{total} passed)</h3>
                <table>
                    <thead><tr><th></th><th>Factor</th><th>Score</th><th>Details</th></tr></thead>
                    <tbody>{factors_html}</tbody>
                </table>
            </div>"""

        # Build recommendations
        recs_html = ""
        for rec in recommendations[:15]:
            priority_color = "#ef4444" if rec.get("priority") == "high" else "#eab308" if rec.get("priority") == "medium" else "#3b82f6"
            recs_html += f"""
            <li>
                <span style="color:{priority_color};font-weight:bold;">[{rec.get('priority', 'medium').upper()}]</span>
                <strong>{rec.get('factor', '')}</strong>: {rec.get('recommendation', '')}
            </li>"""

        score_color = "#22c55e" if overall_score >= 80 else "#eab308" if overall_score >= 60 else "#ef4444"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SEO Analysis Report - {url}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; color: #1f2937; line-height: 1.6; }}
        h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }}
        h2 {{ color: #374151; margin-top: 30px; }}
        h3 {{ margin-top: 20px; }}
        .score-badge {{ display: inline-block; font-size: 48px; font-weight: bold; color: {score_color}; border: 4px solid {score_color}; border-radius: 50%; width: 100px; height: 100px; line-height: 100px; text-align: center; }}
        .category {{ margin: 20px 0; padding: 15px; border: 1px solid #e5e7eb; border-radius: 8px; page-break-inside: avoid; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th, td {{ padding: 6px 10px; text-align: left; border-bottom: 1px solid #f3f4f6; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
        .meta {{ color: #6b7280; font-size: 14px; }}
        @media print {{ body {{ margin: 20px; }} .category {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <h1>SEO & GEO Analysis Report</h1>
    <p class="meta">URL: <a href="{url}">{url}</a> | Generated: {generated_at}</p>

    <div style="text-align:center;margin:30px 0;">
        <div class="score-badge">{overall_score}</div>
        <p style="font-size:18px;color:#374151;margin-top:10px;">Overall Score</p>
    </div>

    <h2>Top Recommendations</h2>
    <ol>{recs_html}</ol>

    <h2>Detailed Results by Category</h2>
    {category_html}

    <footer style="margin-top:40px;padding-top:20px;border-top:1px solid #e5e7eb;color:#9ca3af;font-size:12px;">
        Generated by SEO & GEO Analyzer | {generated_at}
    </footer>
</body>
</html>"""

        return html
