from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

from geoscrap_project.spiders import GeocachingSpider
from geoscrap_project.spiders import GeocachingExtractorSpider

import pandas as pd
from pathlib import Path

def getUrl():
    p = Path('.').resolve()
    geocacheFile = p / 'data' / 'geocaches.json'

    pd.set_option('display.width', 1000)

    df = pd.read_json(geocacheFile.as_uri(), orient='index', lines=True).stack().reset_index(level=1, drop=True)
    df = df.apply(pd.Series, index=df[0].keys())

    return df["url"].tolist()

configure_logging()
runner = CrawlerRunner()

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(GeocachingSpider.GeocachingSpider)
    urls = getUrl()
    yield runner.crawl(GeocachingExtractorSpider.GeocachingExtractorSpider, urls = urls)
    reactor.stop()

crawl()
reactor.run()
