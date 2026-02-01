# InsightHub

InsightHub is an intelligent information aggregation and analysis system designed to automate the collection, filtering, summarization, and distribution of technical trends. It fetches data from sources like GitHub Trending and Zhihu Hot, leverages Large Language Models (LLMs) for content processing, and outputs the results to local Markdown files or synchronizes them with Feishu (Lark) Cloud Docs.

## Project Structure

```text
D:\Development\workspace\InsightHub\
├───.github\workflows\  # CI/CD workflows (e.g., daily runs)
├───configs\            # Configuration files (config.yaml)
├───docs\               # Documentation (Architecture, API guides)
├───output\             # Generated Markdown reports
├───prompts\            # LLM prompt templates
├───scripts\            # Entry point scripts (run_workflow.py)
├───src\                # Source code
│   └───insighthub\
│       ├───core\       # Core engine logic
│       ├───llm_providers\ # LLM integration (OpenRouter, ZhipuAI)
│       ├───sinks\      # Output handlers (Markdown, Feishu)
│       └───sources\    # Data fetchers (GitHub, Zhihu)
├───tests\              # Unit tests
├───requirements.txt    # Python dependencies
└───GEMINI.md           # This file
```

## Key Features

*   **Multi-Source Aggregation:** Fetches trending content from GitHub and Zhihu.
*   **AI-Powered Analysis:** Uses LLMs (OpenRouter, ZhipuAI) to summarize content and filter out noise.
*   **Smart Deduplication:** Checks against existing Feishu Docs to prevent duplicate posts.
*   **Flexible Output:** Supports generating local Markdown reports and pushing directly to Feishu Cloud Docs.
*   **Configurable:** All settings (sources, LLM providers, sinks) are managed via `configs/config.yaml`.

## Getting Started

### Prerequisites

*   Python 3.10 or higher.

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Edit `configs/config.yaml` to configure:
*   **LLM Provider:** Choose between `openrouter` or `zhipuai` and set your API key.
*   **Sources:** Enable/disable sources like `github_trending` or `zhihu_hot`.
*   **Sinks:** Configure output destinations (`markdown_file`, `feishu_doc`).

**Note:** It is recommended to set sensitive API keys as environment variables:
*   `OPENROUTER_API_KEY`
*   `ZHIPUAI_API_KEY`
*   `FEISHU_APP_ID`
*   `FEISHU_APP_SECRET`

### Usage

Run the main workflow script:

```bash
python scripts/run_workflow.py
```

This will:
1.  Fetch data from enabled sources.
2.  Process and summarize the data using the configured LLM.
3.  Generate reports in the `output/` directory (if `markdown_file` sink is enabled).
4.  Push content to Feishu (if `feishu_doc` sink is enabled).

## Development Conventions

*   **Code Style:** Follows standard Python PEP 8 guidelines.
*   **Async I/O:** Uses `asyncio` and `httpx` for network operations.
*   **Type Hinting:** Codebase uses strict type hinting.
*   **Architecture:** Follows a modular design with `Sources`, `LLMProviders`, and `Sinks` decoupled from the core `InsightEngine`.
