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

    start_urls = ['https://www.geocaching.com/account/signin']

    custom_settings = {
        'CONCURRENT_REQUESTS': '1',
        'DOWNLOAD_DELAY': '2',
        'COOKIES_ENABLED': True,
        'ITEM_PIPELINES': {
            'geoscrap_project.pipelines.JsonPipeline': 200,
        },
        'HTTPERROR_ALLOWED_CODES': [301,302,404],
        'HTTPPROXY_ENABLED': False,
        'REDIRECT_ENABLED': True
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
            meta = meta,
            formxpath="//form[@action='/account/signin']",
            formdata={'__RequestVerificationToken':token,'UsernameOrEmail': 'reyman64', 'Password': 'H67y9!CSJw'},
            callback=self.after_login
        )

    def after_login(self, response):

        print(response)
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
        print("TYPE OF SEARCH")
        return scrapy.FormRequest.from_response(
            response,
            #meta={'proxy': 'http://localhost:8888'},
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies':'9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType':'SC'},
            callback=self.parse_cacheCountry

        )

    ## STEP 2 : SELECT COUNTRY
    def parse_cacheCountry(self, response):
        print("COUNTRY SELECT")
        return scrapy.FormRequest.from_response(
            response,
            #meta={'proxy': 'http://localhost:8888'},
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
        print ("SELECT STATE NORMANDY")
        return scrapy.FormRequest.from_response(
            response,
            #meta={'proxy': 'http://localhost:8888'},
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies': '9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType': 'SC',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectCountry': '73',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectState': '487',
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

        geocaches = {}

        #response.meta['viewstate'] = self.get_viewstate(response)

        tdList = response.xpath('(//td[@class="Merge"][2])')

        for td in tdList:
            geocache={}
            link = td.xpath('a//@href')
            name = td.xpath('a/span/text()')
            print("links = ", link.extract())
            # print("name = ", name.extract())

            geocache["url"] = link.extract_first()
            geocache["name"] = name.extract_first()

            p = urlparse(geocache["url"])
            code = p.path.split("/")[2].split("_")[0]

            if "page" not in response.meta.keys():
                print("PAGE NOT IN RESPONSE")
                geocache["page"] = 1
            else:
                print("PAGE IN RESPONSE")
                geocache["page"] = response.meta['page'][0]

            geocaches[code] = geocache

        return geocaches

    def get_viewstate(self,response):

        state = response.xpath('//input[@id="__VIEWSTATE"]/@value').extract()
        state1 = response.xpath('//input[@id="__VIEWSTATE1"]/@value').extract()

        print('xxx STATE = ', state)
        print('xxx STATE1 = ', state1)

        return [state, state1]


    def parse_pages(self,response):

        print("META KEY = ", response.meta.keys())
        viewstate = self.get_viewstate(response)

        geocaches = self.parse_cachesList(response)

        if 'page' not in response.meta.keys():
            infoPage = response.xpath('//td[@class="PageBuilderWidget"]/span/b[3]//text()')
            print("PAGE NOT IN RESPONSE META KEY")
            numberOfPage = int(infoPage.extract_first())
            response.meta['page'] = [1, 3]#numberOfPage

            yield scrapy.FormRequest.from_response(
                response,
                #meta={'proxy': 'http://localhost:8888', 'page': response.meta['page'], 'geocaches': geocaches},
                meta={ 'page': response.meta['page']},
                formname="aspnetForm",
                formxpath="//form[@id='aspnetForm']",
                formdata={'recaptcha_challenge_field': None,
                          'recaptcha_response_field': None,
                          'ctl00$ContentBody$chkHighlightBeginnerCaches': None,
                          'ctl00$ContentBody$chkAll': None,
                          '__EVENTTARGET': None,
                          '__EVENTARGUMENT': None},
                dont_click=True,
                callback=self.parse_pages,
                dont_filter=True
            )

        else:

            if response.meta['page'][0] > response.meta['page'][1]:
                return

            print("NEXT Page : ", response.meta['page'])
            response.meta['page'][0] += 1

            if (response.meta['page'][0] - 1) % 10 == 0:

                yield scrapy.FormRequest.from_response(
                    response,
                    meta={ 'page': response.meta['page']},
                    #meta={'proxy': 'http://localhost:8888', 'page': response.meta['page'], 'geocaches': geocaches},
                    formname="aspnetForm",
                    # meta={'page': page},
                    formxpath="//form[@id='aspnetForm']",
                    formdata={'recaptcha_challenge_field': None,
                              'recaptcha_response_field': None,
                              'ctl00$ContentBody$chkHighlightBeginnerCaches': None,
                              'ctl00$ContentBody$chkAll': None,
                              '__EVENTTARGET': 'ctl00$ContentBody$pgrBottom$ctl06', },
                    dont_click=True,
                    callback=self.parse_pages,
                    dont_filter=True
                    #priority=(21 - response.meta['page'][0])
                )

            else:
                print("ctl00$ContentBody$pgrTop$lbGoToPage_"+ str(response.meta['page'][0]))

                yield scrapy.FormRequest.from_response(
                    response,
                    meta={'page': response.meta['page']},
                    #meta={'proxy': 'http://localhost:8888', 'page': response.meta['page'], 'geocaches':geocaches},
                    formname="aspnetForm",
                    # meta={'page': page},
                    formxpath="//form[@id='aspnetForm']",
                    formdata={'recaptcha_challenge_field': None,
                              'recaptcha_response_field': None,
                              'ctl00$ContentBody$chkHighlightBeginnerCaches': None,
                              'ctl00$ContentBody$chkAll': None,
                              '__EVENTTARGET': 'ctl00$ContentBody$pgrTop$lbGoToPage_' + str(response.meta['page'][0]), },
                    dont_click=True,
                    callback=self.parse_pages,
                    dont_filter=True
                    #priority=(21 - response.meta['page'][0])
                )

        print("GEOCACHES = ", geocaches)
        yield geocaches
        #print ("RUN > ", 'ctl00$ContentBody$pgrTop$lbGoToPage_'+str(response.meta['page'][0]))
        #yield result


    def __init__(self, aDate = pendulum.today()):
        super(GeocachingSpider, self).__init__()
        self.aDate = aDate
        self.timestamp = self.aDate.timestamp()
        print("PENDULUM UTC TODAY ", self.aDate.isoformat())
        print("PENDULUM TO TIMESTAMP ", self.timestamp)
