"""SEO audit report generator (HTML format)."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.utils.config import settings
from src.utils.logger import logger


@dataclass
class ReportGeneratorResult:
    html_content: str = ""
    file_path: Optional[str] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "success": self.success,
        }


class ReportGenerator:
    """Generates comprehensive SEO audit reports in HTML."""

    def generate(
        self,
        url: str,
        analysis_data: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> ReportGeneratorResult:
        """Generate an HTML SEO audit report."""
        result = ReportGeneratorResult()

        overall_score = self._calculate_overall_score(analysis_data)
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = self._build_html(url, analysis_data, overall_score, generated_at)
        result.html_content = html
        result.success = True

        if output_path is None:
            reports_dir = settings.reports_dir
            safe_name = url.replace("https://", "").replace("http://", "")
            safe_name = safe_name.replace("/", "_").replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(reports_dir / f"seo_report_{safe_name}_{timestamp}.html")

        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            result.file_path = output_path
            logger.info(f"Report saved to {output_path}")
        except IOError as e:
            logger.error(f"Failed to save report: {e}")
            result.success = False

        return result

    def _calculate_overall_score(self, data: Dict[str, Any]) -> float:
        scores = []
        for key, value in data.items():
            if isinstance(value, dict) and "score" in value:
                scores.append(value["score"])
        return round(sum(scores) / len(scores), 1) if scores else 0.0


    def _build_html(self, url: str, data: Dict[str, Any], score: float, generated_at: str) -> str:
        """Build the HTML report content."""
        score_color = self._score_color(score)
        sections_html = ""

        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                sections_html += self._build_section(section_name, section_data)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Report - {url}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-4xl mx-auto py-8 px-4">
        <header class="bg-white rounded-lg shadow p-6 mb-6">
            <h1 class="text-2xl font-bold text-gray-800">SEO Audit Report</h1>
            <p class="text-gray-600 mt-1">URL: <a href="{url}" class="text-blue-600">{url}</a></p>
            <p class="text-gray-500 text-sm">Generated: {generated_at}</p>
            <div class="mt-4 flex items-center gap-4">
                <div class="text-4xl font-bold {score_color}">{score:.0f}</div>
                <div class="text-gray-500">/ 100 Overall Score</div>
            </div>
        </header>
        {sections_html}
    </div>
</body>
</html>"""

    def _build_section(self, name: str, data: Dict[str, Any]) -> str:
        """Build HTML for a single analysis section."""
        title = name.replace("_", " ").title()
        score = data.get("score", 0)
        issues = data.get("issues", [])
        score_color = self._score_color(score)

        issues_html = ""
        for issue in issues:
            sev = issue.get("severity", "info")
            badge_cls = {"error": "bg-red-100 text-red-700", "warning": "bg-yellow-100 text-yellow-700"}.get(sev, "bg-blue-100 text-blue-700")
            issues_html += f"""
            <div class="flex items-start gap-3 py-2 border-b border-gray-100">
                <span class="px-2 py-0.5 rounded text-xs font-medium {badge_cls}">{sev}</span>
                <div>
                    <p class="text-gray-800 text-sm">{issue.get('message', '')}</p>
                    <p class="text-gray-500 text-xs mt-0.5">{issue.get('suggestion', '')}</p>
                </div>
            </div>"""

        return f"""
        <section class="bg-white rounded-lg shadow p-6 mb-4">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-semibold text-gray-800">{title}</h2>
                <span class="text-xl font-bold {score_color}">{score:.0f}</span>
            </div>
            <div class="space-y-1">{issues_html if issues_html else '<p class="text-green-600 text-sm">No issues found!</p>'}</div>
        </section>"""

    def _score_color(self, score: float) -> str:
        if score >= 80:
            return "text-green-600"
        elif score >= 60:
            return "text-yellow-600"
        return "text-red-600"
