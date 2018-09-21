# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst


class RetiredPlayersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    BasicInfo= scrapy.Field(output_processor=TakeFirst())
    AverageStats=scrapy.Field(output_processor=TakeFirst())
    FullStats=scrapy.Field(output_processor=TakeFirst())
    Stats=scrapy.Field(output_processor=TakeFirst())
