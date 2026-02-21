import argparse
import asyncio
import datetime
import logging
import os
import sys

from insighthub.core.engine import InsightEngine
from insighthub.errors import ConfigValidationError
from insighthub.observability import JsonLogFormatter, RunContextFilter, new_run_id, set_run_id
from insighthub.settings import settings
from insighthub.workflow_factory import build_llm_provider, build_sinks, build_sources


def setup_logging(run_id: str):
    """Set up structured logging to both console and file."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"insighthub_{today_str}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonLogFormatter())
    console_handler.addFilter(RunContextFilter())
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JsonLogFormatter())
    file_handler.addFilter(RunContextFilter())
    logger.addHandler(file_handler)

    set_run_id(run_id)
    return logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="InsightHub Workflow CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    p_fetch = subparsers.add_parser("fetch", help="Fetch data from sources")
    p_fetch.add_argument("--output", "-o", default="output/raw_data.json", help="Output JSON file for fetched items")
    p_fetch.add_argument("--ignore-history", action="store_true", help="Fetch all items ignoring history")

    p_summarize = subparsers.add_parser("summarize", help="Summarize items using AI")
    p_summarize.add_argument("--input", "-i", required=True, help="Input JSON file with items")
    p_summarize.add_argument("--output", "-o", default="output/summary.md", help="Output Markdown file")

    p_dist = subparsers.add_parser("distribute", help="Send content to sinks")
    p_dist.add_argument("--input", "-i", required=True, help="Input Markdown file content")
    p_dist.add_argument("--items", help="Input JSON file with items (optional, for metadata)")
    p_dist.add_argument("--no-history", action="store_true", help="Do not update history")

    subparsers.add_parser("run", help="Run the full workflow")
    return parser


async def run_cli():
    parser = build_parser()
    args = parser.parse_args()

    run_id = new_run_id()
    logger = setup_logging(run_id)
    logger.info("Starting InsightHub workflow.", extra={"event": "workflow.start", "command": args.command or "run"})

    try:
        settings.validate_runtime_requirements()
    except ConfigValidationError as e:
        logger.error("Runtime settings validation failed.", extra={"event": "workflow.validation_failed", "error": str(e)})
        return

    llm_provider = build_llm_provider(settings, logger=logger)
    if llm_provider is None:
        return

    sources = build_sources(settings, logger=logger)
    if not sources:
        logger.error("No sources are enabled in the configuration. Exiting.", extra={"event": "workflow.no_sources"})
        return

    sinks = build_sinks(settings, logger=logger)
    if not sinks:
        logger.warning("No sinks are enabled in the configuration.", extra={"event": "workflow.no_sinks"})

    engine = InsightEngine(
        sources=sources,
        llm_provider=llm_provider,
        sinks=sinks,
        prompts_dir="prompts",
        history_file="history.json",
        delivery_state_file="delivery_state.json",
        prompt_structure=settings.prompt.structure,
        prompt_style=settings.prompt.style,
        prompt_variables=settings.prompt.variables,
        max_history_records=settings.state.max_history_records,
        max_delivery_item_records=settings.state.max_delivery_item_records,
        max_delivery_runs=settings.state.max_delivery_runs,
    )

    if args.command == "fetch":
        logger.info("Executing subcommand: fetch")
        items = await engine.fetch(ignore_history=args.ignore_history)
        if items:
            output_path = args.output
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            engine.save_items(items, output_path)
            logger.info(f"Saved {len(items)} items to {output_path}")
        else:
            logger.info("No new items fetched.")

    elif args.command == "summarize":
        logger.info("Executing subcommand: summarize")
        items = engine.load_items(args.input)
        if items:
            content = await engine.summarize(items)
            output_path = args.output
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            engine.save_content(content, output_path)
            logger.info(f"Summary saved to {output_path}")
        else:
            logger.warning("No items loaded to summarize.")

    elif args.command == "distribute":
        logger.info("Executing subcommand: distribute")
        content = engine.load_content(args.input)
        if content:
            items = engine.load_items(args.items) if args.items else []
            await engine.distribute(content, items, update_history=not args.no_history)
            logger.info("Distribution completed.")
        else:
            logger.warning("No content loaded to distribute.")

    else:
        logger.info("Executing full workflow (run)")
        await engine.run()

    logger.info("Workflow/Command completed.", extra={"event": "workflow.completed"})


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_cli())
