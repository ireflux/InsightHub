import asyncio
import re
import os
import datetime
import logging
import sys

# Adjust the path to include the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from insighthub.settings import settings
from insighthub.sources import GitHubTrendingSource, ZhihuHotSource, HackerNewsSource
from insighthub.llm_providers import LLMFactory
from insighthub.core.engine import InsightEngine
from insighthub.sinks import MarkdownFileSink, FeishuDocSink

def setup_logging():
    """Sets up logging to both console and file."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "insighthub.log")
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)

async def main():
    """
    The main entry point for the InsightHub workflow.
    """
    logger = setup_logging()
    logger.info("Starting InsightHub workflow with optimized configuration and data models...")

    # 1. Initialize LLM Provider
    llm_provider_name = settings.llm_provider.name
    llm_api_key = settings.llm_provider.api_key
    llm_model = settings.llm_provider.model
    
    try:
        llm_provider = LLMFactory.create_provider(
            llm_provider_name, 
            api_key=llm_api_key,
            model=llm_model,
        )
    except (ValueError, ImportError) as e:
        logger.error(f"Error initializing LLM provider: {e}")
        return

    # 2. Initialize Sources
    sources = []
    for src_config in settings.sources:
        source_name = src_config.name
        if source_name == "github_trending":
            sources.append(GitHubTrendingSource())
        elif source_name == "zhihu_hot":
            keyword_pattern = src_config.keyword_filter
            pattern = re.compile(keyword_pattern) if keyword_pattern else None
            sources.append(ZhihuHotSource(keyword_filter=pattern))
        elif source_name == "hacker_news":
            sources.append(HackerNewsSource())
        else:
            logger.warning(f"Unknown source '{source_name}' in config. Skipping.")

    if not sources:
        logger.error("No sources are enabled in the configuration. Exiting.")
        return
        
    # 3. Initialize Sinks
    sinks = []
    for sink_config in settings.sinks:
        sink_name = sink_config.name
        if sink_name == "markdown_file":
            output_dir = sink_config.output_dir or "output"
            sinks.append(MarkdownFileSink(output_dir=output_dir))
        elif sink_name == "feishu_doc":
            app_id = sink_config.app_id
            app_secret = sink_config.app_secret
            space_id = sink_config.space_id
            default_title = sink_config.default_title or "InsightHub"
            
            # Format title with date if placeholder exists
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            try:
                formatted_title = default_title.format(date=date_str)
            except Exception:
                formatted_title = default_title.replace("{date}", date_str)

            if app_id and app_secret:
                try:
                    sinks.append(FeishuDocSink(
                        app_id=app_id, 
                        app_secret=app_secret, 
                        default_title=formatted_title,
                        space_id=space_id
                    ))
                except ValueError as e:
                    logger.error(f"Error initializing FeishuDocSink: {e}")
            else:
                logger.warning("feishu_doc sink enabled but 'app_id'/'app_secret' not provided. Skipping.")
        else:
            logger.warning(f"Unknown sink '{sink_name}' in config. Skipping.")

    if not sinks:
        logger.warning("No sinks are enabled in the configuration. Output will only be printed to the console.")

    # 4. Initialize InsightEngine and run
    engine = InsightEngine(
        sources=sources,
        llm_provider=llm_provider,
        sinks=sinks,
        prompts_dir="prompts",
        history_file="history.json"
    )
    await engine.run()
    logger.info("Workflow completed.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())