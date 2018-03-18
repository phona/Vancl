# -*- coding: utf-8 -*-
import scrapy
from vancl.items import VanclItem


class CoatsSpider(scrapy.Spider):
    name = 'sweater'
    allowed_domains = ['vancl.com']
    start_urls = ['http://zhenzhishan.vancl.com/']

    def parse(self, response):
        item = VanclItem()
        item_list = response.xpath("//ul[@class='shirts-product-list']/li")
        for each in item_list:
            item['title'] = self.get_title(each)
            item['old_price'] = self.get_old_price(each)
            item['new_price'] = self.get_new_price(each)
            item['image_url'] = self.get_image_url(each)
            yield item

    def get_title(self, response):
        return response.xpath("a[@class='tit']/@title").extract()

    def get_old_price(self, response):
        return response.xpath("span/text()").extract()

    def get_new_price(self, response):
        return response.xpath("a[@class='product-img']/h3/span[@class='sprice']/text()").extract()

    def get_image_url(self, response):
        return response.xpath("a[@class='product-img']/img/@src").extract()

