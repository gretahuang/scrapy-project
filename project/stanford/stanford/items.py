# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class StanfordItem(scrapy.Item):

    # -- Name Information -- #
    PREFIX = scrapy.Field()
    FIRST_NAME = scrapy.Field()
    LAST_NAME = scrapy.Field()
    SUFFIX = scrapy.Field()

    # -- Home Information -- #

    # Home address
    HOME_STREET = scrapy.Field()
    HOME_CITY = scrapy.Field()
    HOME_STATE = scrapy.Field()
    HOME_ZIPCODE = scrapy.Field()
    # Home phone
    HOME_PHONE = scrapy.Field()

    # -- Work Information -- #

    # Work address
    WORK_STREET = scrapy.Field()
    WORK_CITY = scrapy.Field()
    WORK_STATE = scrapy.Field()
    WORK_ZIPCODE = scrapy.Field()
    # Work phone
    WORK_PHONE = scrapy.Field()
    # Job information
    INDUSTRY = scrapy.Field()
    COMPANY = scrapy.Field()
    JOB_TITLE = scrapy.Field()
    
    # -- Other Information -- #
    
    # Email(s)
    EMAILS = scrapy.Field()

    # Date of last update for work information
    WORK_LAST_UPDATED = scrapy.Field()
