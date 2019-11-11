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
import random
from urllib.parse import urlparse
from urllib import parse
from pyproj import Proj

import re

# TODO : récupération de l'inventaire des travel bugs sur la droite

class GeocachingExtractorSpider(scrapy.Spider):
    name = "GeocachingExtractorSpider"

    start_urls = ['http://www.geocaching.com/account/signin']

    custom_settings = {
        'CONCURRENT_REQUESTS': '1',
        'DOWNLOAD_DELAY': '3',
        'COOKIES_ENABLED': True,
        'ITEM_PIPELINES': {
            'geoscrap_project.pipelines.FullInfoJsonPipeline': 200,
        },
        'HTTPERROR_ALLOWED_CODES': [301,302,404],
        'HTTPPROXY_ENABLED': False,
        'REDIRECT_ENABLED': True
    }

    def __init__(self, urls):
        super(GeocachingExtractorSpider, self).__init__()
        print(urls)
        self.urls = urls


    def parse(self, response):

        meta = response.meta

        self.logger.debug('Parse function called on %s', response.url)

        # https://stackoverflow.com/questions/34076989/python-scrapy-login-authentication-spider-issue
        token = response.css('input[name=__RequestVerificationToken]::attr(value)').extract()[0]

        return scrapy.FormRequest.from_response(
            response,
            meta=meta,
            formxpath="//form[@action='/account/signin']",
            formdata={'__RequestVerificationToken':token,'UsernameOrEmail': 'reyman64', 'Password': 'H67y9!CSJw'},
            callback=self.after_login
        )

    def after_login(self, response):

        meta = response.meta

        for url in self.urls:
            yield scrapy.Request(url=url,
                              meta=meta,
                              callback=self.parse_cacheInfo,
                              dont_filter=True)


    def parse_cacheInfo(self, response):

        cache = GeoCacheItem()

        cache["content"] = response.xpath('//div[@class="UserSuppliedContent"]').extract()
        cache["code"] = response.xpath('//span[@class="CoordInfoCode"]/text()').extract_first()
        cache["location"] = response.xpath('//span[@id="uxLatLon"]/text()').extract_first()

        cache["nom"] = response.xpath('//span[@id="ctl00_ContentBody_CacheName"]/text()').extract_first()
        cache["searchLocation"] = response.xpath('//span[@id="ctl00_ContentBody_Location"]/text()').extract_first()
        cache["auteur"] = response.xpath('//div[@id="ctl00_ContentBody_mcd1"]/a/text()').extract_first()

        auteurUID = response.xpath('//div[@id="ctl00_ContentBody_mcd1"]/a/@href').extract_first()

        UTMLocation = response.xpath('//span[@id="ctl00_ContentBody_LocationSubPanel"]/text()').extract_first()
        UTMLocation = " ".join(UTMLocation.split())

        UTMsplitted = UTMLocation.split(" ")

        zone = UTMsplitted[1][:-1]
        UTMx  =UTMsplitted[3]
        UTMy = UTMsplitted[5]

        myProj = Proj("+proj=utm +zone=" + \
                      zone + ", +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

        Lon, Lat = myProj(UTMx, UTMy, inverse=True)

        print("**********")
        print("ZONE = ",zone )
        print("UTMx = ",Lon )
        print("UTMy = ",Lat )
        print("**********")

        cache["locationWGSLon"] = Lon
        cache["locationWGSLat"] = Lat

        p = urlparse(auteurUID)
        cache["auteurUID"] = parse.parse_qs(p.query)['guid'][0]

        cache["type"] = response.xpath('//div[@id="cacheDetails"]/p/a/img/@title').extract_first()
        date = response.xpath('//div[@id="ctl00_ContentBody_mcd2"]/text()').extract_first()
        cache["cachedate"] = re.search("([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})", date).group(0)

        difficulte = response.xpath('//span[@id="ctl00_ContentBody_uxLegendScale"]/img/@alt').extract_first()
        cache["difficulte"] = re.search(r'\b\d+([\.,]\d+)?',difficulte).group(0)

        terrain = response.xpath('//span[@id="ctl00_ContentBody_Localize12"]/img/@alt').extract_first()
        cache["terrain"] = re.search(r'\b\d+([\.,]\d+)?',terrain).group(0)

        taille = response.xpath('//span[@class="minorCacheDetails"]/img/@alt').extract_first()
        cache["taille"] = taille.split(" ")[1]

        cache["urlGallerie"] = response.xpath('//*[contains(concat(" ", normalize-space(@class), " "), "CacheDetailNavigation NoPrint")]/ul/li/a/@href').extract_first()


        cacheAttributesList = response.xpath('//div[@class="WidgetBody"]/img/@src').extract()
        cacheAttribute = []
        for attributes in cacheAttributesList:
            p = urlparse(attributes)
            codeAttribute = p.path.split("/")[3].split(".")[0]
            cacheAttribute.append(codeAttribute)

        cache["cacheAttributs"] = cacheAttribute

        logsAttributesList = response.xpath('//span[@id="ctl00_ContentBody_lblFindCounts"]/p')
        logsList = []

        data = logsAttributesList.extract_first()
        logsNumber = re.sub("(</?p[^>]*>|<img.*?>)", "", str(data), 0, re.IGNORECASE | re.DOTALL | re.MULTILINE | re.UNICODE)
        logsNumber = " ".join(logsNumber.split()).split(" ")
        attributes = logsAttributesList.xpath("./img/@alt")

        for number,attribute in zip(logsNumber,attributes):
            logsList.append({attribute.extract().replace(" ","_"):number})

        cache["logsAttributs"] = logsList

        numberOfLogs = response.xpath('//*[contains(concat(" ", normalize-space(@class), " "), "InformationWidget Clear")]/h3').extract()
        cache["logsNombre"] = re.findall(r'\b\d+\b',str(numberOfLogs))[0]

        yield cache