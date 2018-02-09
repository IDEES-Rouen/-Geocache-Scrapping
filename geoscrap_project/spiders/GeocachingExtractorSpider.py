import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import Rule
from geoscrap_project.items.Items import *
from bs4 import BeautifulSoup
import cfscrape
import json
import jmespath
from fake_useragent import UserAgent
import pendulum
from pathlib import Path
import random
from urllib.parse import urlparse
import pandas as pd
import re

class GeocachingSpider(scrapy.Spider):
    name = "geocachingExtractor"

    p = Path('.').resolve()
    geocacheFile = p / 'data' / 'geocaches.json'

    allowed_domains = ['geocaching.com']

    pd.set_option('display.width', 1000)

    df = pd.read_json(geocacheFile.as_uri(), orient='index', lines=True).stack().reset_index(level=1, drop=True)
    df = df.apply(pd.Series, index=df[0].keys())

        #start_urls = [url.strip() for url in f.readlines()]
        #f.close()
    print(df["url"].tolist())

    start_urls = ['http://www.geocaching.com/account/login']

    def parse(self, response):

        meta = response.meta

        self.logger.debug('Parse function called on %s', response.url)

        # https://stackoverflow.com/questions/34076989/python-scrapy-login-authentication-spider-issue
        token = response.css('input[name=__RequestVerificationToken]::attr(value)').extract()[0]

        return scrapy.FormRequest.from_response(
            response,
            meta=meta,
            formxpath="//form[@action='/account/login']",
            formdata={'__RequestVerificationToken':token,'Username': 'dumbuser', 'Password': 'stackoverflow'},
            callback=self.after_login
        )

    def after_login(self, response):

        meta = response.meta

        # go to nearest page
        return scrapy.Request(url="https://www.geocaching.com/geocache/GC7AE50_mont-gargan",
                              meta=meta,
                              callback=self.parse_cacheInfo,
                              dont_filter=True)


    def parse_cacheInfo(self, response):
        texte = response.xpath('//div[@class="UserSuppliedContent"]').extract()
        print(texte)
        code = response.xpath('//span[@class="CoordInfoCode"]/text()').extract_first()
        print(code)

        location = response.xpath('//span[@id="uxLatLon"]/text()').extract_first()
        print(location)

        cacheby = response.xpath('//div[@id="ctl00_ContentBody_mcd1"]/a/text()').extract_first()
        print(cacheby)

        cachetype = response.xpath('//div[@id="cacheDetails"]/p/a/img/@title').extract_first()
        print(cachetype)

        cachedate = response.xpath('//div[@id="ctl00_ContentBody_mcd2"]/text()').extract_first()
        cachedate = re.search("([0-9]{2}\/[0-9]{2}\/[0-9]{4})", cachedate).group(0)
        print(cachedate)

        cacheDifficultyStar = response.xpath('//span[@id="ctl00_ContentBody_uxLegendScale"]/img/@alt').extract_first()

        cacheTerrainStar = response.xpath('//span[@id="ctl00_ContentBody_Localize12"]/img/@alt').extract_first()

        print(cacheDifficultyStar)
        print(cacheTerrainStar)

        cachesize = response.xpath('//span[@class="minorCacheDetails"]/img/@alt').extract_first()
        print(cachesize)

        galleryURL = response.xpath('//*[contains(concat(" ", normalize-space(@class), " "), "CacheDetailNavigation NoPrint")]/ul/li/a/@href').extract_first()
        print(galleryURL)

        cacheAttributesList = response.xpath('//div[@class="WidgetBody"]/img/@src').extract()
        cacheAttribute = []
        for attributes in cacheAttributesList:
            p = urlparse(attributes)
            codeAttribute = p.path.split("/")[3].split(".")[0]
            cacheAttribute.append(codeAttribute)

        print(cacheAttribute)

        logsAttributesList = response.xpath('//span[@id="ctl00_ContentBody_lblFindCounts"]/p')
        logsList = []

        data = logsAttributesList.extract_first()
        logsNumber = re.sub("(</?p[^>]*>|<img.*?>)", "", str(data), 0, re.IGNORECASE | re.DOTALL | re.MULTILINE | re.UNICODE)
        logsNumber = " ".join(logsNumber.split()).split(" ")
        attributes = logsAttributesList.xpath("./img/@alt")

        for number,attribute in zip(logsNumber,attributes):
            logsList.append({attribute.extract().replace(" ","_"):number})

        print(logsList)

        numberOfLogs = response.xpath('//*[contains(concat(" ", normalize-space(@class), " "), "InformationWidget Clear")]/h3').extract()
        numberOfLogs = re.findall(r'\b\d+\b',str(numberOfLogs))
        print(numberOfLogs)