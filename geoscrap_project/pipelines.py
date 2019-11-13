# -*- coding: utf-8 -*-

import pymongo

from scrapy.exceptions import DropItem
from scrapy.exporters import JsonLinesItemExporter
import os
from pathlib import Path
import logging

class MongoPipeline(object):

    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(dict(item))
        return item


class FullInfoJsonPipeline(object):
    def __init__(self):
        print("FullInfoJsonPipeline")
        p = Path('.') / 'data' / 'fullGeochache.json'

        self.file = p.open('wb')
        self.exporter = JsonLinesItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class JsonPipeline(object):

    logger = logging.getLogger()

    def __init__(self):
        print("JsonPipeline")
        p = Path('.') / 'data' / 'geocaches.json'
        self.file = p.open('wb')
        self.exporter = JsonLinesItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.logger.debug(" ** PROCESS ** ")
        if len(item) ==0:
            self.logger.debug("EMPTY")
            raise DropItem()
        else:
            self.logger.debug("NOT EMPTY")
            self.exporter.export_item(item)
            return item

