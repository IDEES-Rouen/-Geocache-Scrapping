# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class GeoCacheItem(scrapy.Item):
    nom = scrapy.Field()
    content = scrapy.Field()
    location = scrapy.Field()
    locationWGSLon = scrapy.Field()
    locationWGSLat = scrapy.Field()
    searchLocation = scrapy.Field()
    auteur = scrapy.Field()
    auteurUID = scrapy.Field()
    code = scrapy.Field()
    type = scrapy.Field()
    cachedate = scrapy.Field()
    difficulte = scrapy.Field()
    terrain = scrapy.Field()
    taille = scrapy.Field()
    urlGallerie = scrapy.Field()
    cacheAttributs = scrapy.Field()
    logsAttributs = scrapy.Field()
    logsNombre = scrapy.Field()