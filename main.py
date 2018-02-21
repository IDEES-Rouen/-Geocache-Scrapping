from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner

from scrapy import cmdline
import subprocess
import pandas as pd
from pathlib import Path

# from scrapy.utils.log import configure_logging
#
# configure_logging()
# runner = CrawlerRunner(get_project_settings())
#
# @defer.inlineCallbacks
# def crawl():
#     yield runner.crawl('geocaching')
#     yield getUrl()
#
# @defer.inlineCallbacks
# def crawl_two(urls):
#     return runner.crawl('geocachingExtractor',urls = urls)
#
# def getUrl():
#     p = Path('.').resolve()
#     geocacheFile = p / 'data' / 'geocaches.json'
#
#     pd.set_option('display.width', 1000)
#
#     df = pd.read_json(geocacheFile.as_uri(), orient='index', lines=True).stack().reset_index(level=1, drop=True)
#     df = df.apply(pd.Series, index=df[0].keys())
#
#     yield df["url"].tolist()
#
# data = crawl()
#
# crawl_two(data)
#
# reactor.run() # the script will block here until the last crawl call is finished

# process = CrawlerProcess(get_project_settings())
#
# process.crawl('geocaching')
#
# process.start()


p = Path('.').resolve()
geocacheFile = p / 'data' / 'geocaches.json'

allowed_domains = ['geocaching.com']

df = pd.read_json(geocacheFile.as_uri(), orient='index', lines=True).stack().reset_index(level=1, drop=True)
df = df.apply(pd.Series, index=df[0].keys())

urls = df["url"].tolist()

process = CrawlerProcess(get_project_settings())
process.crawl('geocachingExtractor',urls = urls)

process.start()

