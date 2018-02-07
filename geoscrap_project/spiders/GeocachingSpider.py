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


class GeocachingSpider(scrapy.Spider):
    name = "geocaching"

    p = Path('.').resolve()
    dataFolder = p.parent.joinpath("/data")

    start_urls = ['http://www.geocaching.com/account/login']

    custom_settings = {
        'HTTPPROXY_ENABLED': True
    }

    allowed_domains = ['geocaching.com']
    ua = UserAgent()

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
        return scrapy.Request(url="https://www.geocaching.com/seek/nearest.aspx",
                              meta=meta,
                              callback=self.parse_cacheSearch,
                              dont_filter=True)

    ## SIMULATE THE THREE STEP TO POPULATE THE FORM : search type, country, state
    ## NEEDED TO POPULATE ASP __VIEWSTATE hidden value

    ## STEP 1 : SEARCH TYPE = SC
    def parse_cacheSearch(self,response):

        return scrapy.FormRequest.from_response(
            response,
            meta={'proxy': 'http://localhost:8888'},
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies':'9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType':'SC'},
            callback=self.parse_cacheCountry

        )

    ## STEP 2 : SELECT COUNTRY
    def parse_cacheCountry(self, response):

        return scrapy.FormRequest.from_response(
            response,
            meta={'proxy': 'http://localhost:8888'},
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies': '9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType': 'SC',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectCountry': '73'},
            callback=self.parse_cacheState
        )

    ## STEP 3 : SELECT STATE AND SENT FINAL QUERY by submit
    ## 421 haute normandie
    ## 414 basse normandie
    def parse_cacheState(self, response):

        return scrapy.FormRequest.from_response(
            response,
            meta={'proxy': 'http://localhost:8888'},
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies': '9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType': 'SC',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectCountry': '73',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectState': '421',
                'ctl00$ContentBody$LocationPanel1$btnLocale': 'Recherche+de+géocaches'},
            callback=self.parse_pages
        )

    def display_hidden_tag(self,response):
        soup = BeautifulSoup(response.body)
        hidden_tags = soup.find_all("input", type="hidden")
        for tag in hidden_tags:
            print(tag)

    def parse_cachesList(self, response):

        # print("PAGE >> ", response.meta['page'] ," <<<<<<<<<<<<<")
        # self.display_hidden_tag(response)

        # Update Meta

        geocaches = []

        response.meta['viewstate'] = self.get_viewstate(response)

        tdList = response.xpath('(//td[@class="Merge"][2])')

        for td in tdList:

            link = td.xpath('a//@href')
            name = td.xpath('a/span/text()')
            # print("links = ", link.extract())
            # print("name = ", name.extract())

            geocache = GeoCacheItem()
            geocache["url"] = link.extract_first()
            geocache["name"] = name.extract_first()

            p = urlparse(geocache["url"])
            geocache["code"] = p.path.split("/")[2].split("_")[0]
            geocache["page"] = response.meta['page']
            geocaches.append(geocache)

        return geocaches

    def get_viewstate(self,response):

        state = response.xpath('//input[@id="__VIEWSTATE"]/@value').extract()
        state1 = response.xpath('//input[@id="__VIEWSTATE1"]/@value').extract()

        print('xxx STATE = ', state)
        print('xxx STATE1 = ', state1)

        return [state, state1]


    def parse_pages(self,response):

        if "page" not in response.meta.keys():
            ## EXTRACT NUMBER OF PAGES
            links = response.xpath('//td[@class="PageBuilderWidget"]/span/b[3]//text()')

            numberOfPage = int(links.extract_first())
            #pages = list(range(1, (numberOfPage + 1)))
            #pages = list(range(10, 15))
            #random.shuffle(pages)
            response.meta['page'] = 2
            viewstate = self.get_viewstate(response)

        if page == 1:

            result = scrapy.FormRequest.from_response(
                response,
                meta={'proxy': 'http://localhost:8888', 'page': page,'viewstate':viewstate},
                formname="aspnetForm",
                #meta={'page':page},
                formxpath="//form[@id='aspnetForm']",
                formdata={'recaptcha_challenge_field':None,
                          'recaptcha_response_field': None,
                          'ctl00$ContentBody$chkHighlightBeginnerCaches':None,
                          'ctl00$ContentBody$chkAll':None,
                          '__EVENTTARGET':None,
                          '__EVENTARGUMENT': None},
                dont_click=True,
                callback=self.parse_cachesList,
                dont_filter=True
                )
        elif page == 11:
            result = scrapy.FormRequest.from_response(
                response,
                meta={'proxy': 'http://localhost:8888','page': page},
                formname="aspnetForm",
                #meta={'page': page},
                formxpath="//form[@id='aspnetForm']",
                formdata={'recaptcha_challenge_field':None,
                          'recaptcha_response_field': None,
                          'ctl00$ContentBody$chkHighlightBeginnerCaches':None,
                          'ctl00$ContentBody$chkAll': None,
                          '__EVENTTARGET': 'ctl00$ContentBody$pgrTop$ctl06', },
                dont_click=True,
                callback=self.parse_cachesList,
                dont_filter=True,
                priority=(21 - page)
            )

        else :
            result = scrapy.FormRequest.from_response(
                response,
                meta={'proxy': 'http://localhost:8888', 'page': page},
                formname="aspnetForm",
                #meta={'page': page},
                formxpath="//form[@id='aspnetForm']",
                formdata={'recaptcha_challenge_field':None,
                          'recaptcha_response_field': None,
                          'ctl00$ContentBody$chkHighlightBeginnerCaches':None,
                          'ctl00$ContentBody$chkAll':None,
                          '__EVENTTARGET':'ctl00$ContentBody$pgrTop$lbGoToPage_'+str(page),},
                dont_click=True,
                callback=self.parse_cachesList,
                dont_filter=True,
                priority=(21-page)
                )

        print ("RUN > ", 'ctl00$ContentBody$pgrTop$lbGoToPage_'+str(page))
        yield result

    def __init__(self, aDate = pendulum.today()):
        super(GeocachingSpider, self).__init__()
        self.aDate = aDate
        self.timestamp = self.aDate.timestamp()
        print("PENDULUM UTC TODAY ", self.aDate.isoformat())
        print("PENDULUM TO TIMESTAMP ", self.timestamp)
