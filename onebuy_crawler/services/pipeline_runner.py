from __future__ import annotations

import os

from onebuy_crawler.pipelines.cleaning import CleaningPipeline
from onebuy_crawler.pipelines.dedup import DedupPipeline
from onebuy_crawler.pipelines.mysql import MySqlPipeline
from onebuy_crawler.pipelines.raw_log import RawLogPipeline


class PipelineRunner:
    """Run Scrapy-style item pipelines from non-Scrapy entrypoints."""

    def __init__(self, settings):
        self.pipelines = [CleaningPipeline(), DedupPipeline(), RawLogPipeline()]
        if os.getenv("CRAWLER_ENABLE_MYSQL", "0") == "1":
            self.pipelines.append(MySqlPipeline(settings))

    def process(self, item):
        current = item
        for pipeline in self.pipelines:
            current = pipeline.process_item(current)
        return current
