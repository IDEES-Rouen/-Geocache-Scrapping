from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner

from scrapy.utils.project import get_project_settings

import logging
from scrapy.utils.log import configure_logging

from geoscrap_project.spiders import GeocachingSpider
from geoscrap_project.spiders import GeocachingExtractorSpider

import pandas as pd
from pathlib import Path
from twisted.internet import task

configure_logging(install_root_handler=True)
logging.basicConfig(filename='geocache.log',level=logging.DEBUG)
logger = logging.getLogger()

def getUrl():
    p = Path('.').resolve()
    geocacheFile = p / 'data' / 'geocaches.json'

    def resolve_problem_panda(jsonFile):
        with jsonFile.open() as json_file:
            json_list = list(json_file)

        import json
        for json_str in json_list:
            result = json.loads(json_str)
        return json.dumps(result)

    result = resolve_problem_panda(geocacheFile)
    json = pd.read_json(result, orient='index')
    logger.debug(json)
    df = list(json['url'])

    return df


# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)
# logging.basicConfig(
#     filename='log.txt',
#     format='%(levelname)s: %(message)s',
#     level=logging.DEBUG
# )

# s = get_project_settings()
#
# s.update({
#     "LOG_ENABLED": "True",
#     "LOG_LEVEL": "DEBUG"
# })

def crawl(reactor):
    runner = CrawlerRunner()
    d = runner.crawl(GeocachingSpider.GeocachingSpider)
    d.addCallback(getResult)
    d.addCallback(crawl2, runner)
    return d

def getResult(result):
    return getUrl()

def crawl2( result, runner):
    return runner.crawl(GeocachingExtractorSpider.GeocachingExtractorSpider, urls = result)

task.react(crawl)