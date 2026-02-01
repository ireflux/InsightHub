# Role: Senior Software Architect & Automation Expert

# Project: InsightHub
InsightHub 是一个智能化的信息聚合与深度分析系统。它的核心使命是：从 GitHub Trending、知乎热榜等源头自动抓取数据，利用 AI (LLM) 进行多维度的筛选、去重与总结，最终生成高质量的 Markdown 技术周刊并自动化同步至飞书。

# 🏗️ Core Architectural Design (Strict Constraints):
代码实现必须遵循高度抽象化和接口驱动的设计原则，确保系统可轻松横向扩展。

1. **Source Layer (数据源层 - 抽象抽象再抽象):**
   - 定义 `BaseSource` 抽象基类。所有平台（GitHub, Zhihu, RSS）必须继承自此类。
   - 核心方法：`fetch_raw_data()` (抓取), `parse_to_unified_format()` (解析为统一的 dict 结构)。
   - 去重将依赖飞书云文档的查询/检索接口（Feishu Docs API），在推送前检查文档中是否已存在相同来源链接，从而避免重复发布。

2. **AI Provider Layer (AI 能力抽象层):**
   - 采用 **Strategy Pattern (策略模式)**。定义 `BaseLLMProvider` 抽象类。
   - 需适配以下 Provider：
     - `OpenRouter` (模型: `xiaomi/mimo-v2-flash:free`)
     - `ZhipuAI` (模型: `glm-4.5-flash`)
   - 必须包含 `LLMFactory`，根据 `config.yaml` 动态切换不同的 LLM 供应商。
   - 统一接口：`summarize(content: str)` 和 `classify(content: str, categories: list)`。
   - 必须内置速率限制处理（Rate Limiting）和自动重试机制。

3. **Sink Layer (输出层):**
   - 定义 `BaseSink` 抽象基类。
   - `FeishuDocSink`: 负责通过 Feishu Docs API 写入飞书云文档/多维表格。
   - `MarkdownFileSink`: 在本地生成归档的 `.md` 文件。

4. **Workflow Orchestrator:**
   - 整个流程解耦为：Sources -> Deduplicator -> LLM Filter/Summarizer -> Sink Renderer。

# 🛠️ Technical Stack:
- Language: Python 3.10+ (Strict Type Hinting)
- Async: 使用 `httpx` 和 `asyncio` 进行全异步网络 IO。
- Data Model: 使用 `Pydantic v2` 定义数据协议。
- Persistence: 去重不再使用本地数据库；使用飞书 Docs API 进行云端查询以决定是否重复发布。
- Prompt Management: 所有 Prompt 模板必须存放在单独的 `prompts/` 目录下，支持变量注入。

# 🎯 Current Tasks:

1. **Project Scaffold:**
   - 生成符合最佳实践的目录结构（src/, configs/, tests/, prompts/, scripts/）。
   - 提供 `requirements.txt`。

2. **Core Implementation:**
   - 实现 `BaseLLMProvider` 及其针对 OpenRouter 和 ZhipuAI 的子类（适配最新的 API 规范）。
   - 实现 `GitHubTrendingSource` (使用 BeautifulSoup 或官方 API)。
   - 实现 `ZhihuHotSource` (包含简单的关键词正则过滤，减少无效 AI 调用)。

3. **The "Brain" Logic:**
   - 编写 `InsightEngine` 类，串联“抓取 -> 数据库查重 -> AI 智能总结 -> 飞书推送”的完整逻辑。

4. **Config System:**
   - 使用 `config.yaml` 管理所有的 API Key、运行频率、各源的过滤阈值等。

# 📋 Coding Style & Standards:
- 代码必须清晰易读，包含必要的 Docstrings。
- 遵循 DRY (Don't Repeat Yourself) 原则。
- 敏感信息（API Keys）必须从环境变量或加密的 `.env` 文件读取，禁止硬编码。
- 最终生成的 Markdown 必须针对飞书渲染引擎进行优化（多用引用块 `>` 和加粗 `**`）。

# 🚀 Let's Start:
请先展示项目的目录结构设计，并给出核心抽象类 `BaseSource` 和 `BaseLLMProvider` 的 Python 代码实现。

## CI / GitHub Actions

Add the following GitHub Actions workflow to run InsightHub daily and push results to Feishu Cloud Docs:

- Workflow file: `.github/workflows/daily.yml` (runs daily, installs requirements, runs `scripts/run_workflow.py`).
- Required repository secrets: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_DOC_ID` (optional if you want to update an existing doc), and `OPENROUTER_API_KEY`.

The workflow sets these secrets as environment variables so the runtime can pick them up. The run will create a new Feishu doc titled using the configured `default_title` template (supports `{date}` which will be replaced by `YYYYMMDD`).