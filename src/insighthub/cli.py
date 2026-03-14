import argparse
import asyncio
import datetime
import logging
import os
import sys

from insighthub.core.engine import InsightEngine
from insighthub.errors import ConfigValidationError
from insighthub.observability import JsonLogFormatter, RunContextFilter, new_run_id, set_run_id
from insighthub.publishing import TitlePolicy
from insighthub.settings import get_settings
from insighthub.workflow_factory import build_llm_provider, build_sinks, build_sources


def setup_logging(run_id: str, settings):
    """Set up structured logging to both console and file."""
    obs = settings.runtime.observability
    log_dir = settings.runtime.paths.logs_dir
    if obs.file_enabled and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{obs.file_name_prefix}_{today_str}.log")

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, obs.level.upper(), logging.INFO))

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter: logging.Formatter
    if obs.format == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s [run_id=%(run_id)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

    if obs.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(RunContextFilter())
        logger.addHandler(console_handler)

    if obs.file_enabled:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
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
    p_summarize.add_argument(
        "--items-output",
        help="Output JSON file for items that actually entered final summary (default: <output>.items.json)",
    )

    p_debug_input = subparsers.add_parser(
        "debug-summary-input",
        help="Build and export the exact text payload that would be sent to LLM summarization",
    )
    p_debug_input.add_argument("--input", "-i", required=True, help="Input JSON file with items")
    p_debug_input.add_argument(
        "--output",
        "-o",
        default="output/summary_input.txt",
        help="Output text file containing the composed summarize input",
    )
    p_debug_input.add_argument(
        "--no-scoring",
        action="store_true",
        help="Skip scoring/order step and keep input order when exporting summarize input",
    )

    p_dist = subparsers.add_parser("distribute", help="Send content to sinks")
    p_dist.add_argument("--input", "-i", required=True, help="Input Markdown file content")
    p_dist.add_argument(
        "--items",
        help="Input JSON file with summarized items metadata (default: auto-detect <input>.items.json if exists)",
    )
    p_dist.add_argument("--no-history", action="store_true", help="Do not update history")

    subparsers.add_parser("run", help="Run the full workflow")
    return parser


async def _close_llm_provider(provider):
    if provider is None:
        return
    close_fn = getattr(provider, "aclose", None)
    if callable(close_fn):
        await close_fn()


def _requires_sources(command: str | None) -> bool:
    return command in (None, "run", "fetch")


async def run_cli():
    parser = build_parser()
    args = parser.parse_args()

    run_id = new_run_id()
    settings = get_settings()
    logger = setup_logging(run_id, settings)
    logger.info("Starting InsightHub workflow.", extra={"event": "workflow.start", "command": args.command or "run"})

    requires_llm = args.command in (None, "run", "summarize")
    requires_sources = _requires_sources(args.command)
    llm_provider = None
    try:
        if requires_llm:
            try:
                settings.validate_runtime_requirements()
            except ConfigValidationError as e:
                logger.error("Runtime settings validation failed.", extra={"event": "workflow.validation_failed", "error": str(e)})
                return

            llm_provider = build_llm_provider(settings, logger=logger)
            if llm_provider is None:
                return

        sources = build_sources(settings, logger=logger) if requires_sources else []
        if requires_sources and not sources:
            logger.error("No sources are enabled in the configuration. Exiting.", extra={"event": "workflow.no_sources"})
            return

        sinks = build_sinks(settings, logger=logger)
        if not sinks:
            logger.warning("No sinks are enabled in the configuration.", extra={"event": "workflow.no_sinks"})

    title_policy = TitlePolicy(
        template=settings.publishing.title.template,
        date_format=settings.publishing.title.date_format,
        timezone_name=settings.publishing.title.timezone or settings.runtime.timezone,
        strip_leading_h1=settings.publishing.title.strip_leading_h1,
    )

        engine = InsightEngine(
            sources=sources,
            llm_provider=llm_provider,
            sinks=sinks,
            prompts_dir=settings.runtime.paths.prompts_dir,
            history_file=settings.runtime.paths.history_file,
            delivery_state_file=settings.runtime.paths.delivery_state_file,
            prompt_structure=settings.prompt.structure,
            prompt_style=settings.prompt.style,
            prompt_variables=settings.prompt.variables,
            max_history_records=settings.state.max_history_records,
            max_delivery_item_records=settings.state.max_delivery_item_records,
            max_delivery_runs=settings.state.max_delivery_runs,
            scoring_config=settings.scoring,
            source_retry_policy=settings.runtime.retry.source_fetch,
            llm_retry_policy=settings.runtime.retry.llm_summarize,
            sink_retry_policy=settings.runtime.retry.sink_render,
            dedup_config=settings.runtime.dedup,
            timezone_name=settings.runtime.timezone,
            title_policy=title_policy,
            stage_runs_dir=settings.runtime.paths.stage_runs_dir,
        )

        if requires_llm and llm_provider is None:
            logger.error(
                "LLM provider is required for this command but was not initialized.",
                extra={"event": "workflow.llm_required_missing", "command": args.command or "run"},
            )
            return

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
                if settings.scoring.enabled:
                    items = await engine.score_items(items)
                content = await engine.summarize(items)
                output_path = args.output
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                engine.save_content(content, output_path)
                logger.info(f"Summary saved to {output_path}")
                items_output_path = args.items_output or f"{os.path.splitext(output_path)[0]}.items.json"
                os.makedirs(os.path.dirname(os.path.abspath(items_output_path)), exist_ok=True)
                engine.save_items(items, items_output_path)
                logger.info(f"Summarized items saved to {items_output_path}")
            else:
                logger.warning("No items loaded to summarize.")

        elif args.command == "debug-summary-input":
            logger.info("Executing subcommand: debug-summary-input")
            items = engine.load_items(args.input)
            if items:
                if settings.scoring.enabled and not args.no_scoring:
                    items = await engine.score_items(items)
                combined_input = engine.build_summarize_input(items)
                output_path = args.output
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                engine.save_content(combined_input, output_path)
                logger.info(f"Summarize input payload saved to {output_path}")
            else:
                logger.warning("No items loaded to build summarize input.")

        elif args.command == "distribute":
            logger.info("Executing subcommand: distribute")
            content = engine.load_content(args.input)
            if content:
                items_path = args.items
                if not items_path:
                    default_items_path = f"{os.path.splitext(args.input)[0]}.items.json"
                    if os.path.exists(default_items_path):
                        items_path = default_items_path
                        logger.info(f"Auto-detected summarized items file: {items_path}")
                items = engine.load_items(items_path) if items_path else []
                await engine.distribute(content, items, update_history=not args.no_history)
                logger.info("Distribution completed.")
            else:
                logger.warning("No content loaded to distribute.")

        else:
            logger.info("Executing full workflow (run)")
            await engine.run()

        logger.info("Workflow/Command completed.", extra={"event": "workflow.completed"})
    finally:
        await _close_llm_provider(llm_provider)


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
