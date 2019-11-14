# -*- coding: utf-8 -*-

import pymongo

from scrapy.exceptions import DropItem
from scrapy.exporters import JsonLinesItemExporter
import os
from pathlib import Path
import logging
import pendulum

def get_timestamp():
    aDate = pendulum.today()
    return aDate.timestamp()

class FullInfoJsonPipeline(object):
    def __init__(self):
        print("FullInfoJsonPipeline")
        name = 'fullgeocaches'+str(get_timestamp())+'.json'

        p = Path('.') / 'data' / name

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
        name = 'geocaches'+str(get_timestamp())+'.json'
        p = Path('.') / 'data' / name
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

