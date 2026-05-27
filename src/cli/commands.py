"""CLI commands for SEO Tool using Click + Rich."""

import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_async(coro):
    """Helper to run async functions from sync CLI."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.version_option(version="1.0.0", prog_name="SEO Tool")
def cli():
    """SEO Tool - All-in-One SEO Analysis Platform."""
    pass


@cli.command()
@click.argument("url")
@click.option("--keyword", "-k", default=None, help="Target keyword for analysis")
def analyze(url: str, keyword: str):
    """Analyze a page for SEO issues."""
    from src.utils.http_client import HttpClient
    from src.analyzers import (
        MetaAnalyzer, HeadingAnalyzer, LinkAnalyzer,
        ImageAnalyzer, PerformanceAnalyzer, ContentAnalyzer,
    )

    async def _analyze():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Fetching page...", total=None)
            async with HttpClient() as client:
                html = await client.fetch_page(url)
            if not html:
                console.print("[red]Failed to fetch URL[/red]")
                return

            progress.update(task, description="Analyzing...")
            results = {
                "Meta Tags": MetaAnalyzer().analyze(html, url),
                "Headings": HeadingAnalyzer().analyze(html, url),
                "Links": LinkAnalyzer().analyze(html, url),
                "Images": ImageAnalyzer().analyze(html, url),
                "Performance": PerformanceAnalyzer().analyze(html, url),
                "Content": ContentAnalyzer().analyze(html, url, keyword),
            }

        # Overall score
        scores = [r.score for r in results.values()]
        overall = sum(scores) / len(scores)
        color = "green" if overall >= 80 else "yellow" if overall >= 60 else "red"
        console.print(Panel(f"[bold {color}]{overall:.0f}/100[/bold {color}]", title=f"SEO Score: {url}"))

        # Score table
        table = Table(title="Module Scores")
        table.add_column("Module", style="cyan")
        table.add_column("Score", justify="center")
        table.add_column("Issues", justify="center")

        for name, result in results.items():
            s = result.score
            sc = "green" if s >= 80 else "yellow" if s >= 60 else "red"
            issues_count = len(result.issues)
            table.add_row(name, f"[{sc}]{s:.0f}[/{sc}]", str(issues_count))

        console.print(table)

        # Show issues
        for name, result in results.items():
            if result.issues:
                console.print(f"\n[bold]{name} Issues:[/bold]")
                for issue in result.issues:
                    sev_color = {"error": "red", "warning": "yellow", "info": "blue"}.get(issue.severity, "white")
                    console.print(f"  [{sev_color}]{issue.severity.upper()}[/{sev_color}] {issue.message}")
                    if hasattr(issue, 'suggestion') and issue.suggestion:
                        console.print(f"         [dim]{issue.suggestion}[/dim]")

    run_async(_analyze())



@cli.command()
@click.argument("url")
@click.option("--max-pages", "-m", default=50, help="Max pages to crawl")
@click.option("--depth", "-d", default=3, help="Max crawl depth")
def crawl(url: str, max_pages: int, depth: int):
    """Crawl an entire website."""
    from src.crawlers import SiteCrawler

    async def _crawl():
        console.print(f"[bold]Crawling {url}[/bold] (max: {max_pages} pages, depth: {depth})")
        crawler = SiteCrawler(max_pages=max_pages, max_depth=depth)
        result = await crawler.crawl(url)

        table = Table(title=f"Crawl Results - {result.total_pages} pages")
        table.add_column("URL", style="cyan", max_width=60)
        table.add_column("Status", justify="center")
        table.add_column("Time", justify="center")
        table.add_column("Words", justify="center")

        for page in result.pages[:50]:
            status_color = "green" if page.status_code == 200 else "red"
            table.add_row(
                page.url[:60],
                f"[{status_color}]{page.status_code}[/{status_color}]",
                f"{page.response_time_ms:.0f}ms",
                str(page.word_count),
            )

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {result.total_pages} pages, {result.total_errors} errors, avg {result.avg_response_time:.0f}ms, took {result.crawl_duration_sec:.1f}s")

    run_async(_crawl())


@cli.command("check-links")
@click.argument("url")
def check_links(url: str):
    """Check for broken links on a page."""
    from src.checkers import BrokenLinkChecker

    async def _check():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("Checking links...", total=None)
            checker = BrokenLinkChecker()
            result = await checker.check_page(url)

        console.print(f"\n[bold]Checked {result.total_links_checked} links on {url}[/bold]")
        console.print(f"  [green]Healthy:[/green] {result.healthy_links}")
        console.print(f"  [red]Broken:[/red] {result.broken_count}")

        if result.broken_links:
            table = Table(title="Broken Links")
            table.add_column("URL", style="red", max_width=60)
            table.add_column("Status", justify="center")
            table.add_column("Anchor", max_width=30)

            for bl in result.broken_links:
                table.add_row(bl.url[:60], str(bl.status_code) or "ERR", bl.anchor_text[:30])
            console.print(table)

    run_async(_check())


@cli.command("generate-sitemap")
@click.argument("url")
@click.option("--output", "-o", default="sitemap.xml", help="Output file path")
@click.option("--max-pages", "-m", default=100, help="Max pages to include")
def generate_sitemap(url: str, output: str, max_pages: int):
    """Generate sitemap.xml by crawling a site."""
    from src.crawlers import SiteCrawler
    from src.generators import SitemapGenerator

    async def _generate():
        console.print(f"[bold]Crawling {url} for sitemap...[/bold]")
        crawler = SiteCrawler(max_pages=max_pages, max_depth=3)
        crawl_result = await crawler.crawl(url)

        pages = [{"url": p.url, "status_code": p.status_code, "error": p.error} for p in crawl_result.pages]
        generator = SitemapGenerator()
        result = generator.generate_from_crawl(pages, output_path=output)

        console.print(f"[green]Sitemap generated with {result.total_urls} URLs[/green]")
        console.print(f"Saved to: [cyan]{output}[/cyan]")

    run_async(_generate())


@cli.command()
@click.argument("my_url")
@click.argument("competitor_urls", nargs=-1)
def compare(my_url: str, competitor_urls: tuple):
    """Compare your site with competitors."""
    from src.competitors import CompetitorAnalyzer

    if not competitor_urls:
        console.print("[red]Please provide at least one competitor URL[/red]")
        return

    async def _compare():
        console.print(f"[bold]Comparing {my_url} vs {len(competitor_urls)} competitors...[/bold]")
        analyzer = CompetitorAnalyzer()
        result = await analyzer.compare(my_url, list(competitor_urls))

        # Comparison table
        table = Table(title="Competitor Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Your Site", style="bold")
        for c in result.competitors:
            table.add_column(c.url[:30])

        my = result.my_site
        metrics = [
            ("Score", my.overall_score, [c.overall_score for c in result.competitors]),
            ("Words", my.word_count, [c.word_count for c in result.competitors]),
            ("Speed (ms)", my.load_time_ms, [c.load_time_ms for c in result.competitors]),
            ("Int Links", my.internal_links, [c.internal_links for c in result.competitors]),
        ]

        for name, my_val, comp_vals in metrics:
            row = [name, str(my_val)] + [str(v) for v in comp_vals]
            table.add_row(*row)

        console.print(table)

        if result.recommendations:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for r in result.recommendations:
                console.print(f"  > {r}")

    run_async(_compare())


@cli.command("track-rank")
@click.option("--keyword", "-k", required=True, help="Keyword to track")
@click.option("--domain", "-d", required=True, help="Domain to find")
def track_rank(keyword: str, domain: str):
    """Track keyword ranking position."""
    from src.rank_tracker import RankTracker

    async def _track():
        console.print(f"[bold]Checking rank for '[cyan]{keyword}[/cyan]' on {domain}...[/bold]")
        tracker = RankTracker()
        entry = await tracker.check_keyword(keyword, domain)

        if entry.position:
            color = "green" if entry.position <= 10 else "yellow" if entry.position <= 30 else "red"
            console.print(f"\n  Position: [{color}]#{entry.position}[/{color}]")
            console.print(f"  URL: {entry.url}")
            console.print(f"  Title: {entry.title}")
        else:
            console.print("\n  [red]Not found in top 100 results[/red]")

    run_async(_track())


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", "-p", default=8000, help="Port to listen on")
def serve(host: str, port: int):
    """Start the web UI server."""
    import uvicorn
    from src.api import create_app

    console.print(f"[bold green]Starting SEO Tool server on http://{host}:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    app = create_app()
    uvicorn.run(app, host=host, port=port)
