# InsightHub

A production-ready, asynchronous Python workflow engine for aggregating technical signals, scoring and summarizing content with LLMs, and distributing insights across multiple platforms.

---

## Key Features

- **Multi-source Aggregation**: GitHub Trending, Hacker News, V2EX, and Slashdot.
- **AI Scoring & Summarization**: Prioritize and summarize content using LLMs (ZhipuAI, OpenRouter, NVIDIA, Custom OpenAI/Anthropic).
- **Flexible Distribution**: Output to Markdown files, Feishu documents, and static site manifests.
- **Robust State Management**: Built-in deduplication, history tracking, and automatic retry logic.
- **Asynchronous Design**: High-performance concurrent fetching and processing.

## Quick Start

### 1. Installation

Requires Python 3.10+.

```bash
git clone https://github.com/your-username/InsightHub.git
cd InsightHub

# Using UV (Recommended)
uv sync

# Using Pip
pip install -e .
```

### 2. Configuration

Copy the example configuration:
```bash
cp configs/config.example.yaml configs/config.yaml
```

Set your API keys as environment variables:
```bash
export ZHIPUAI_API_KEY="your_key"
export OPENROUTER_API_KEY="your_key"
```

### 3. Run the Workflow

```bash
# Execute the full pipeline (Fetch -> Score -> Summarize -> Distribute)
insighthub run
```

## Integrations

### Supported Sources
- **GitHub Trending** (`github_trending`)
- **Hacker News** (`hacker_news`)
- **V2EX** (`v2ex_hot`)
- **Slashdot** (`slashdot`)

### Supported LLM Providers
- **ZhipuAI** (`zhipuai`)
- **OpenRouter** (`openrouter`)
- **NVIDIA NIM** (`nvidia`)
- **Custom OpenAI/Anthropic** (`custom_openai`, `custom_anthropic`)

### Supported Sinks
- **Markdown File** (`markdown_file`)
- **Feishu Document** (`feishu_doc`)

## CLI Commands

InsightHub also supports running individual stages:

```bash
# Fetch data
insighthub fetch --output data.json

# Summarize data
insighthub summarize --input data.json --output summary.md

# Distribute content
insighthub distribute --input summary.md --items data.json
```

## Automation

InsightHub includes GitHub Action workflows (`.github/workflows/`) for:
- **Daily Runs**: Executes the workflow and saves artifacts.
- **Site Deployment**: Builds and publishes a static site to GitHub Pages from the run results.

## License

MIT License.
