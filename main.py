from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scrapy import cmdline
import subprocess

#cmdline.execute("scrapy crawl airports".split())

#https://doc.scrapy.org/en/latest/topics/practices.html
process = CrawlerProcess(get_project_settings())
process.crawl('geocachingExtractor')

process.start()

## PYMONGO DUMP

#from pymongo import MongoClient
#client = MongoClient('mongodb://mongodb_service:27017/')


