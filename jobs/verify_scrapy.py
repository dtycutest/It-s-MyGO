from __future__ import annotations

from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings


def main() -> None:
    settings = get_project_settings()
    loader = SpiderLoader.from_settings(settings)

    print("Scrapy project: onebuy_crawler")
    print(f"Settings module: {settings.get('SETTINGS_MODULE')}")
    print("Spiders:")
    for name in sorted(loader.list()):
        spider_cls = loader.load(name)
        print(f"  - {name}: {spider_cls.__module__}.{spider_cls.__name__}")

    print("Item pipelines:")
    pipelines = settings.getdict("ITEM_PIPELINES")
    for pipeline, priority in sorted(pipelines.items(), key=lambda item: item[1]):
        print(f"  - {priority}: {pipeline}")


if __name__ == "__main__":
    main()
