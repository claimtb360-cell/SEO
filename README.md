# SEO Tool - All-in-One SEO Analysis Platform

A comprehensive SEO analysis tool built with Python, featuring a web UI, REST API, and CLI interface.

## Features

### Core Analysis
- **Meta Tag Analyzer** - Title, description, Open Graph, Twitter Cards
- **Heading Structure** - H1-H6 hierarchy validation
- **Link Analysis** - Internal/external links, anchor text distribution
- **Image Optimization** - Alt text, file size, lazy loading
- **Performance** - Core Web Vitals, page speed metrics
- **Content Quality** - Keyword density, readability score, word count

### Site Crawling
- Full site crawling with configurable depth
- Sitemap.xml parsing and validation
- JavaScript-rendered page support (Playwright)

### SEO Generators
- Sitemap.xml generator
- Robots.txt generator
- SEO audit reports (HTML/PDF/Excel)

### Health Checks
- Broken link detection
- Redirect chain analysis
- Canonical URL validation
- Mobile-friendly testing

### Competitor Analysis
- Side-by-side SEO comparison
- Keyword gap analysis
- Backlink profile comparison
- Content strategy insights

### Rank Tracking
- Daily keyword position monitoring
- SERP feature tracking
- Historical ranking data
- Automated scheduling

## Tech Stack

- **Backend:** Python 3.10+, FastAPI
- **Frontend:** Jinja2 templates, TailwindCSS, Alpine.js, Chart.js
- **Database:** SQLite (SQLAlchemy async)
- **Crawling:** httpx, BeautifulSoup4, Playwright
- **CLI:** Click + Rich

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/claimtb360-cell/SEO.git
cd SEO

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -m src.main init-db
```

### Run Web UI

```bash
python -m src.main serve
# Open http://localhost:8000
```

### Run CLI

```bash
# Analyze a single page
seo analyze https://example.com

# Crawl entire site
seo crawl https://example.com --depth 3

# Check broken links
seo check-links https://example.com

# Generate sitemap
seo generate-sitemap https://example.com

# Compare competitors
seo compare https://mysite.com https://competitor1.com https://competitor2.com

# Track rankings
seo track-rank --keyword "python seo tool" --domain example.com
```

### API Usage

```bash
# Start API server
python -m src.main serve

# Analyze a page
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Get crawl results
curl http://localhost:8000/api/v1/crawl/results/{task_id}
```

## Project Structure

```
SEO/
├── src/
│   ├── main.py                  # Entry point
│   ├── analyzers/               # SEO analysis modules
│   ├── crawlers/                # Site crawling
│   ├── generators/              # Report & file generators
│   ├── checkers/                # SEO health checks
│   ├── competitors/             # Competitor analysis
│   ├── rank_tracker/            # Keyword rank tracking
│   ├── api/                     # FastAPI routes
│   ├── cli/                     # CLI commands
│   ├── models/                  # Database models
│   ├── utils/                   # Shared utilities
│   └── templates/               # Jinja2 HTML templates
├── static/                      # CSS, JS, images
├── data/                        # SQLite DB, exports
├── tests/                       # Unit & integration tests
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Configuration

All configuration is managed via environment variables. See `.env.example` for available options.

## License

MIT License
