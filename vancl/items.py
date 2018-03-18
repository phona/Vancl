# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class VanclItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    fk = scrapy.Field()
    images = scrapy.Field()
    image_url = scrapy.Field()

    # list page
    title = scrapy.Field()
    old_price = scrapy.Field()
    new_price = scrapy.Field()
    item_type = scrapy.Field()
    productcode = scrapy.Field()
    original = scrapy.Field()

    # sub page
    menu_image_url = scrapy.Field()
    display_image_url = scrapy.Field()

class ColorItem(scrapy.Item):

    productcode = scrapy.Field()
    color_name = scrapy.Field()
    color_code = scrapy.Field()
    color_image_url = scrapy.Field()

class ImageItem(scrapy.Item):

    fk = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
