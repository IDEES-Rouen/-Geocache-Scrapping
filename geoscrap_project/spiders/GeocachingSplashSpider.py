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
from selenium import webdriver
from scrapy_splash import *

class GeocachingSplashSpider(scrapy.Spider):
    name = "geocachingSplash"

    p = Path('.').resolve()
    dataFolder = p.parent.joinpath("/data")

    start_urls = ['https://www.geocaching.com/account/login']

    allowed_domains = ['geocaching.com']
    ua = UserAgent()



    def parse(self, response):
        self.logger.debug('Parse function called on %s', response.url)

        # https://stackoverflow.com/questions/34076989/python-scrapy-login-authentication-spider-issue
        token = response.css('input[name=__RequestVerificationToken]::attr(value)').extract()[0]

        return SplashFormRequest.from_response(
            response,
            args={'wait': 1.0},
            formxpath="//form[@action='/account/login']",
            formdata={'__RequestVerificationToken':token,'Username': 'dumbuser', 'Password': 'stackoverflow'},
            callback=self.after_login
        )

    def after_login(self, response):
        print("AFTER LOGIN BODY ", response.body)

        # go to nearest page
        return SplashRequest(url="https://www.geocaching.com/seek/nearest.aspx",
                       callback=self.parse_cacheSearch,
                       dont_filter=True)

    ## SIMULATE THE THREE STEP TO POPULATE THE FORM : search type, country, state
    ## NEEDED TO POPULATE ASP __VIEWSTATE hidden value

    ## STEP 1 : SEARCH TYPE = SC
    def parse_cacheSearch(self,response):

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.body)
        hidden_tags = soup.find_all("input", type="hidden")
        for tag in hidden_tags:
            print(tag)

        return SplashFormRequest.from_response(
            response,
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies':'9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType':'SC'},
            callback=self.parse_cacheCountry
        )

    ## STEP 2 : SELECT COUNTRY
    def parse_cacheCountry(self, response):

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.body)
        hidden_tags = soup.find_all("input", type="hidden")
        for tag in hidden_tags:
            print(tag)

        return SplashFormRequest.from_response(
            response,
            formxpath="//form[@id='aspnetForm']",
            formdata={
                'ctl00$ContentBody$uxTaxonomies': '9a79e6ce-3344-409c-bbe9-496530baf758',
                'ctl00$ContentBody$LocationPanel1$ddSearchType': 'SC',
                'ctl00$ContentBody$LocationPanel1$CountryStateSelector1$selectCountry': '73'},
            args={'wait': 0.5},
            callback=self.parse_cacheState
        )

    ## STEP 3 : SELECT STATE AND SENT FINAL QUERY by submit
    def parse_cacheState(self, response):

        return SplashFormRequest.from_response(
            response,
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

        self.display_hidden_tag(response)

        links = response.xpath('//td[@class="Merge"]//a[@class="lnk"]')
        for link in links:
            print(link.extract())

    def parse_pages(self,response):

        self.parse_cachesList(response)

        ## EXTRACT NUMBER OF PAGES
        links = response.xpath('//td[@class="PageBuilderWidget"]/span/b[3]')
        print(links.extract_first())

        ## SEARCH 5 first pages
        ##for page in range(1,5):
        ##print ("RUN > ", 'ctl00$ContentBody$pgrTop$lbGoToPage_'+str(page))
        return SplashFormRequest.from_response(
            response,
            formxpath="//form[@id='aspnetForm']",
            formdata={'__EVENTARGUMENT':'',
                          '__EVENTTARGET':'ctl00$ContentBody$pgrTop$lbGoToPage_2' #+str(page),
                          },
            dont_click=True,
            callback=self.parse_cachesList,
            dont_filter=True
            )

    def __init__(self, aDate = pendulum.today()):
        super(GeocachingSplashSpider, self).__init__()
        self.aDate = aDate
        self.timestamp = self.aDate.timestamp()
        print("PENDULUM UTC TODAY ", self.aDate.isoformat())
        print("PENDULUM TO TIMESTAMP ", self.timestamp)

    # def clean_html(self, html_text):
    #     soup = BeautifulSoup(html_text, 'html.parser')
    #     return soup.get_text()
    #
    # rules = [
    # # Extract links matching 'item.php' and parse them with the spider's method parse_item
    # #    Rule(LxmlLinkExtractor(allow=('data/airports/',)), callback='parse')
    # ]
    #
    # def generateCentroidUrls(self,centroidFile):
    #     listOfUrls =[]
    #     with open(centroidFile, newline='') as csvfile:
    #         centroidReader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    #         for row in centroidReader:
    #             print(', '.join(row))
    #             listOfUrls.append("'https://www.geocaching.com/play/search/")
    #     return listOfUrls
    #
    # def build_search_call(self,lat,lon,radius):
    #     return 'https://www.geocaching.com/play/search/@{lat},@{lon}?origin=@{lat},@{lon}&g=-1&radius={radius}km'.format(
    #         lat=lat, lon=lon, radius=radius)
