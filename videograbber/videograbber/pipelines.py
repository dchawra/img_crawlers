# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import signal

import scrapy.spiders
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
import sys
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from urllib.parse import urljoin
import urllib
from scrapy.exporters import CsvItemExporter


class videograbberPipeline:
    def __init__(self):
        self.exporter = None
        self.urls_seen = set()


        # Set up a signal handler for interrupt (Ctrl+C)
        signal.signal(signal.SIGINT, self.close_on_interrupt)

    def open_spider(self, spider: scrapy.spiders.CrawlSpider):
        # get base domain of the spider
        url = spider.allowed_domains[0]

        self.exporter = CsvItemExporter(open(f'videolinks_{url}.tsv', 'a+b'), delimiter='\t', include_headers_line=True)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter['video_url'] is not None:
            if adapter['video_url'].startswith('http'):
                pass
            else:
                adapter['video_url'] = urljoin(adapter['page_url'], adapter['video_url'])
        else:
            pass

        if adapter['video_url'] in self.urls_seen:
            raise DropItem(f"Duplicate item found: {item!r}")
        else:
            self.urls_seen.add(adapter['video_url'])

        print(f"Writing item to TSV: {item!r}")
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()

    def close_on_interrupt(self, signum, frame):
        # Handle interrupt signal (Ctrl+C)
        print("Received interrupt signal. Closing the TSV file gracefully.")
        self.exporter.finish_exporting()
