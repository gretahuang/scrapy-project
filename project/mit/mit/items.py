# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MitItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    PREFIX = scrapy.Field()
    FIRST_NAME = scrapy.Field()
    LAST_NAME = scrapy.Field()
    SUFFIX = scrapy.Field()

    INDUSTRY = scrapy.Field()
    COMPANY = scrapy.Field()
    JOB_TITLE = scrapy.Field()

    HOME_STREET = scrapy.Field()
    HOME_CITY = scrapy.Field()
    HOME_STATE = scrapy.Field()
    HOME_ZIPCODE = scrapy.Field()

    WORK_STREET = scrapy.Field()
    WORK_CITY = scrapy.Field()
    WORK_STATE = scrapy.Field()
    WORK_ZIPCODE = scrapy.Field()

    HOME_PHONE = scrapy.Field()
    MOBILE_PHONE = scrapy.Field()
    WORK_PHONE = scrapy.Field()
    
    EMAILS = scrapy.Field()
    SPOUSE = scrapy.Field()

    WORK_LAST_UPDATED = scrapy.Field()
    HOME_LAST_UPDATED = scrapy.Field()
