# InsightHub

<div align="center">

A powerful async Python workflow for aggregating technical intelligence from multiple sources, intelligently scoring and summarizing content using LLM, and distributing insights to multiple platforms.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]() [![License](https://img.shields.io/badge/license-MIT-green)]()

</div>

## 馃搵 Overview

InsightHub is a production-ready, composable workflow engine that:

- **Aggregates** technical signals from diverse sources (GitHub Trending, Hacker News, V2EX, Zhihu, Slashdot)
- **Scores** content using deterministic rules and/or LLM-based analysis
- **Summarizes** high-value items with configurable prompt structures and styles
- **Distributes** formatted content to multiple sinks (Markdown files, Feishu documents)
- **Manages** deduplication, history tracking, and delivery state across runs
- **Observes** operations with structured JSON logging and context correlation

Perfect for teams building tech briefings, knowledge bases, or automated content curation systems.

## 鉁?Key Features

- **Multi-source aggregation**: Fetch from GitHub Trending, Hacker News, V2EX, Zhihu Hot, and Slashdot
- **Flexible LLM support**: Primary/fallback providers (Zhipu AI, OpenRouter) with automatic failover
- **Intelligent content scoring**: Rule-based + optional LLM scoring with customizable weights
- **Multiple output formats**: Markdown files and Feishu documents with templated rendering
- **Composable workflows**: Run individual stages (fetch 鈫?score 鈫?summarize 鈫?distribute) or full pipeline
- **Deduplication & history**: Track processed items and avoid duplicates across runs
- **Structured observability**: JSON-formatted logs with run context tracking
- **Extensible architecture**: Plugin-based sources and sinks with consistent interfaces
- **Async-first design**: Non-blocking concurrent fetching and processing

## 馃幆 Quick Start

### Installation

**Prerequisites**: Python 3.10+

```bash
# Clone the repository
git clone <repo-url>
cd InsightHub

# Install with UV (recommended)
uv sync

# Or with pip
pip install -e .
```

### Basic Configuration

1. Copy the example config:
   ```bash
   cp configs/config.example.yaml configs/config.yaml
   ```

2. Set required environment variables:
   ```bash
   export ZHIPUAI_API_KEY="your_zhipuai_key"
   ```

3. Update `configs/config.yaml` with your sources and sinks

### Run the Full Workflow

```bash
# Run complete pipeline: fetch 鈫?score 鈫?summarize 鈫?distribute
insighthub run
```

### Run Individual Stages

```bash
# Fetch items from sources
insighthub fetch --output output/raw_data.json

# Score fetched items
insighthub score --input output/raw_data.json

# Summarize items using LLM
insighthub summarize --input output/raw_data.json --output output/summary.md

# Distribute to sinks
insighthub distribute --input output/summary.md --items output/raw_data.json
```

## 馃彈锔?Architecture

### Data Flow

```
Sources 鈫?Fetch & Content Extraction 鈫?Deduplication
    鈫?Score (Rule-based + Optional LLM)
    鈫?Filter & Select
    鈫?Summarize (LLM with Prompt Template)
    鈫?Render & Distribute (Markdown, Feishu)
    鈫?Track History & Delivery State
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **InsightEngine** | Orchestrator for the complete workflow lifecycle |
| **Sources** | Plugins that fetch content from different platforms |
| **LLMProvider** | Abstracts LLM calls with primary/fallback support |
| **ContentScorer** | Evaluates item quality using rules and/or LLM |
| **PromptRenderer** | Renders LLM prompts with configurable structure/style |
| **Sinks** | Outputs formatted content to Markdown or Feishu |
| **RetryPolicy** | Exponential backoff for resilient external calls |

## 馃摝 Supported Sources

| Source | Type ID | Description |
|--------|---------|-------------|
| GitHub Trending | `github_trending` | Trending repositories |
| Hacker News | `hacker_news` | Top stories from HN |
| V2EX | `v2ex_hot` | Hot topics on V2EX |
| Slashdot | `slashdot` | Latest stories from Slashdot |
| Zhihu Hot | `zhihu_hot` | Hot content from Zhihu (with keyword filtering) |

## 馃攲 Supported Sinks

| Sink | Type ID | Description |
|-----|---------|-------------|
| Markdown File | `markdown_file` | Write to local Markdown files |
| Feishu Document | `feishu_doc` | Create/update Feishu wiki docs |

## 鈿欙笍 Configuration

### Main Config File

Create `configs/config.yaml` (based on `configs/config.example.yaml`):

```yaml
llm:
  primary:
    provider: "zhipuai"
    model: "glm-4.7-flash"
  fallbacks: []

sources:
  defaults:
    max_items: 8
    content_fetch_concurrency: 4
    content_fetch_timeout: 10.0
  items:
    - id: "github_main"
      type: "github_trending"
      enabled: true
      max_items: 10
    - id: "hn_main"
      type: "hacker_news"
      enabled: true
    - id: "zhihu_ai"
      type: "zhihu_hot"
      enabled: false
      params:
        keyword_filter: "缂栫▼|AI|Python|鏈哄櫒瀛︿範"

sinks:
  defaults:
    enabled: true
  items:
    - id: "markdown_local"
      type: "markdown_file"
      params:
        output_dir: "output"
    - id: "feishu_daily"
      type: "feishu_doc"
      enabled: false
      params:
        space_id: "your_feishu_space_id"

publishing:
  title:
    template: "每日技术趋势观察 {date}"
    date_format: "%Y-%m-%d"
    strip_leading_h1: true

prompt:
  structure: "professional_briefing_v1"
  style: "professional_neutral_v1"
  variables:
    min_items: 12

scoring:
  enabled: true
  use_llm: false
  min_score_for_summary: 4.0
  keep_top_n: 20
  weights:
    technical_depth_and_novelty: 0.30
    potential_impact: 0.25
    writing_quality: 0.15
    community_discussion: 0.15
    engagement_signals: 0.15

state:
  max_history_records: 3000
  max_delivery_item_records: 2000
  max_delivery_runs: 100

runtime:
  paths:
    prompts_dir: "prompts"
    history_file: "history.json"
    delivery_state_file: "delivery_state.json"
    logs_dir: "logs"
  retry:
    source_fetch:
      max_attempts: 3
      base_delay_seconds: 1.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0
    llm_summarize:
      max_attempts: 3
      base_delay_seconds: 2.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0
    sink_render:
      max_attempts: 2
      base_delay_seconds: 1.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0
  timeouts:
    source_discover_timeout_seconds: 20.0
  dedup:
    normalize_url: true
    strip_query_params: ["utm_source", "utm_medium", "ref", "source"]
  observability:
    level: "INFO"
    format: "json"
    console_enabled: true
    file_enabled: true
    file_name_prefix: "insighthub"
```

### Configuration Sections

#### LLM (`llm`)

Configure primary and fallback LLM providers:

```yaml
llm:
  primary:
    provider: "zhipuai"           # Primary provider
    model: "glm-4.7-flash"
  fallbacks:
    - provider: "openrouter"      # Fallback used if primary fails
      model: "xiaomi/mimo-v2-flash:free"
```

- **provider**: `"zhipuai"` or `"openrouter"`
- **model**: Model identifier from the provider
- **api_key**: Loaded from environment variables (not in config)
- Fallbacks are tried in order when the primary provider fails

#### Sources (`sources`)

Define data sources to fetch from:

```yaml
sources:
  defaults:
    max_items: 8                        # Default items per source
    content_fetch_concurrency: 4        # Concurrent fetch tasks
    content_fetch_timeout: 10.0         # Timeout per request (seconds)
  items:
    - id: "github_main"                 # Unique instance ID
      type: "github_trending"           # Source type
      enabled: true
      max_items: 10                     # Override default
      params:                           # Source-specific options
        # No params for github_trending
    - id: "zhihu_ai"
      type: "zhihu_hot"
      enabled: false
      params:
        keyword_filter: "缂栫▼|AI"       # Regex filter for Zhihu
```

#### Sinks (`sinks`)

Configure output destinations:

```yaml
sinks:
  defaults:
    enabled: true                       # Enable by default
  items:
    - id: "markdown_local"
      type: "markdown_file"
      params:
        output_dir: "output"            # Directory for markdown files
    - id: "feishu_daily"
      type: "feishu_doc"
      enabled: false
      params:
        space_id: "your_feishu_space_id"
```

#### Publishing (`publishing`)

Global title policy for markdown, Feishu, and static pages:

```yaml
publishing:
  title:
    template: "每日技术趋势观察 {date}"
    date_format: "%Y-%m-%d"
    strip_leading_h1: true
```

#### Prompt Configuration (`prompt`)

Customize AI summarization:

```yaml
prompt:
  structure: "professional_briefing_v1"  # Template from prompts/structure/
  style: "professional_neutral_v1"       # Template from prompts/style/
  variables:                             # Variables passed to templates
    min_items: 12
    report_date: "2024-01-15"
```

Prompt templates are loaded from:
- `prompts/structure/{structure_name}.md`
- `prompts/style/{style_name}.md`
- `prompts/summarize_prompt.md`

#### Scoring Configuration (`scoring`)

Enable content quality evaluation:

```yaml
scoring:
  enabled: true                      # Enable/disable scoring
  use_llm: false                     # Blend rule scores with LLM scores
  llm_blend_alpha: 0.7               # Weight for rule score (higher = rely more on rules)
  min_score_for_summary: 4.0         # Items below this are filtered out
  keep_top_n: 20                     # Keep only top N items (optional)
  max_items_for_llm_scoring: 20      # Batch size for LLM scoring
  weights:                           # Score dimension weights
    technical_depth_and_novelty: 0.30
    potential_impact: 0.25
    writing_quality: 0.15
    community_discussion: 0.15
    engagement_signals: 0.15
```

**Scoring Tiers**:
- 9.0+: "Groundbreaking"
- 7.0+: "High Value"  
- 5.0+: "Interesting"
- 3.0+: "Low Priority"
- <3.0: "Noise"

#### Runtime Configuration (`runtime`)

Control execution behavior:

```yaml
runtime:
  paths:
    prompts_dir: "prompts"              # Prompt templates directory
    history_file: "history.json"        # File tracking processed items
    delivery_state_file: "delivery_state.json"    # Delivery metadata
    logs_dir: "logs"                    # Log files directory

  retry:                                # Retry policies for each stage
    source_fetch:
      max_attempts: 3
      base_delay_seconds: 1.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0
    llm_summarize:
      max_attempts: 3
      base_delay_seconds: 2.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0
    sink_render:
      max_attempts: 2
      base_delay_seconds: 1.0
      backoff_multiplier: 2.0
      max_delay_seconds: 30.0

  timeouts:
    source_discover_timeout_seconds: 20.0

  dedup:
    normalize_url: true                 # Normalize URLs for comparison
    strip_query_params:                 # Query params to ignore in dedup
      - "utm_source"
      - "utm_medium"
      - "ref"
      - "source"

  observability:
    level: "INFO"                       # Log level
    format: "json"                      # Format: "json" or "text"
    console_enabled: true
    file_enabled: true
    file_name_prefix: "insighthub"
```

## 馃攼 Environment Variables

### LLM Providers

- `ZHIPUAI_API_KEY`: API key for Zhipu AI (GLM models)
- `OPENROUTER_API_KEY`: API key for OpenRouter (fallback provider)

### Feishu Sink

- `FEISHU_APP_ID`: Feishu application ID
- `FEISHU_APP_SECRET`: Feishu application secret
- `FEISHU_SPACE_ID`: (Optional) Default space ID for documents
- `FEISHU_DOC_ID`: (Optional) Default document ID for updates

## 馃搳 Content Scoring

InsightHub uses a multi-dimensional scoring system to prioritize valuable content:

### Scoring Dimensions

1. **Technical Depth & Novelty** (30%): Novel research, new tools, breaking changes
2. **Potential Impact** (25%): Relevance to industry, audience size affected
3. **Writing Quality** (15%): Clarity, structure, professionalism
4. **Community Discussion** (15%): Comments, discourse signal
5. **Engagement Signals** (15%): Stars, upvotes, trending indicators

### Rule-Based Scoring

Deterministic scoring based on keyword presence and metadata:

```python
# Examples of scoring keywords
"research", "paper", "release", "beta", "critical", "vulnerability",
"framework", "library", "tool", "update", "announcement"
```

### LLM-Enhanced Scoring

Optional LLM-based scoring for nuanced evaluation:

```yaml
scoring:
  enabled: true
  use_llm: true
  llm_blend_alpha: 0.7  # 70% rule-based + 30% LLM = more stable
```

When enabled, InsightHub:
1. Computes rule-based scores for all items
2. Sends top items to LLM for evaluation (bounded by `max_items_for_llm_scoring`)
3. Blends scores using alpha parameter
4. Uses LLM's reasoning for summary generation

## 馃洜锔?Advanced Usage

### Source-Specific Parameters

**Zhihu Hot (`zhihu_hot`)**:
```yaml
params:
  keyword_filter: "缂栫▼|AI|娣卞害瀛︿範|Python"  # Regex filter on title
```

### Running Individual Stages

The CLI supports running specific workflow phases:

```bash
# 1. Fetch only (saves raw items)
insighthub fetch --output data.json --ignore-history

# 2. Summarize pre-fetched items
insighthub summarize --input data.json --output summary.md

# 3. Distribute content to sinks
insighthub distribute --input summary.md --items data.json --no-history
```

### Custom Prompt Templates

Create custom templates in `prompts/`:

- `prompts/structure/{name}.md`: Item structure template
- `prompts/style/{name}.md`: Writing style template
- `prompts/summarize_prompt.md`: Main summarization prompt

Template variables are passed via config's `prompt.variables`.

## 馃И Development

### Install Dev Dependencies

```bash
uv sync --all-extras
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/test_scoring.py -v  # Specific test
```

### Code Quality

```bash
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

### Project Structure

```
InsightHub/
鈹溾攢鈹€ src/insighthub/
鈹?  鈹溾攢鈹€ core/              # Engine and retry logic
鈹?  鈹溾攢鈹€ llm_providers/     # LLM integrations (Zhipu, OpenRouter)
鈹?  鈹溾攢鈹€ sources/           # Data source implementations
鈹?  鈹溾攢鈹€ sinks/             # Output implementations (Markdown, Feishu)
鈹?  鈹溾攢鈹€ prompting/         # Prompt rendering
鈹?  鈹溾攢鈹€ cli.py             # CLI entry point
鈹?  鈹溾攢鈹€ models.py          # Data models (NewsItem)
鈹?  鈹溾攢鈹€ scoring.py         # Content scoring logic
鈹?  鈹溾攢鈹€ settings.py        # Configuration models
鈹?  鈹斺攢鈹€ workflow_factory.py # Factory functions
鈹溾攢鈹€ configs/
鈹?  鈹溾攢鈹€ config.example.yaml
鈹?  鈹斺攢鈹€ config.yaml        # Runtime config (not in git)
鈹溾攢鈹€ prompts/               # Prompt templates
鈹溾攢鈹€ tests/                 # Test suite
鈹斺攢鈹€ README.md
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_engine_behavior.py -v
```

## 馃摑 State Files

InsightHub maintains state across runs:

- **`history.json`**: Unique IDs of all processed items (for deduplication)
- **`delivery_state.json`**: Metadata about distributions (timestamps, item counts)

These files enable InsightHub to avoid reprocessing and provide delivery tracking.

## 馃殌 Deployment

### Environment Setup

```bash
# Set required API keys
export ZHIPUAI_API_KEY="sk-..."
export FEISHU_APP_ID="cli_..."
export FEISHU_APP_SECRET="..."

# Or use .env file
pip install python-dotenv
# Create .env with above variables
```

### Running on Schedule

Use cron (Unix/macOS) or Task Scheduler (Windows):

```bash
# Crontab: Run daily at 8 AM
0 8 * * * /path/to/insighthub run

# With logging
0 8 * * * /path/to/insighthub run >> /var/log/insighthub.log 2>&1
```

### GitHub Pages Deployment (gh-pages)

This repository now supports a two-workflow static-site pipeline:

1. `.github/workflows/daily.yml`
- Runs tests and `insighthub run`
- Commits daily artifacts to `main`:
  - `output/posts/YYYY-MM-DD-<run_id>.md`
  - `output/manifest/index.json`
  - `history.json`
  - `delivery_state.json`

2. `.github/workflows/deploy-pages.yml`
- Triggers after daily workflow success (or manual dispatch)
- Pre-renders static HTML site from manifest + markdown
- Publishes `site/` to `gh-pages`

Site build command:

```bash
python scripts/build_site.py \
  --manifest output/manifest/index.json \
  --content-root output \
  --output-dir site
```

Timezone is configurable via `runtime.timezone` (default `Asia/Shanghai`).

### Docker

Create a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["insighthub", "run"]
```

## 馃搫 License

MIT License - See LICENSE file for details

## 馃 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 馃摟 Support

For issues, questions, or suggestions, please open an issue on the repository.

---

**Built with 鉂わ笍 for knowledge discovery and content curation**

