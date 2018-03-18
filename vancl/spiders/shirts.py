# -*- coding: utf-8 -*-
import re

import scrapy
from vancl.items import VanclItem
from scrapy.http.request import Request


class CoatsSpider(scrapy.Spider):
    name = 'shirts'
    allowed_domains = ['vancl.com']
    start_urls = ['http://shirts.vancl.com/']
    pattern = re.compile(r"\d+")

    def parse(self, response):
        item_list = response.xpath("//ul[@class='shirts-product-list']/li")
        for each in item_list:
            item = VanclItem()
            item['title'] = self.get_title(each)
            item['old_price'] = self.get_old_price(each)
            item['new_price'] = self.get_new_price(each)
            item['image_url'] = self.get_image_url(each)
            # yield item
            yield Request(url=self.get_url(each),
                          callback=self.sec_parse,
                          meta={'item':item})

    def sec_parse(self, response):
        # collecting all images url
        item = response.meta['item']
        item["color_image_url"] = self.get_color_url(response)
        item["menu_image_url"] = self.get_menu_url(response)
        item["display_image_url"] = self.get_display_url(response)

        yield item

    def get_display_url(self, response):
        display_list = response.xpath("//table")
        display_vessel = []
        for each in display_list:
            result = each.xpath("tbody/tr/td/img/@src").extract()
            if result:
                display_vessel.append(
                    result[0],
                )
        return display_vessel

    def get_menu_url(self, response):
        menu_list = response.xpath("//span[@class='SpriteSmallImgs']")
        menu_vessel = []
        for each in menu_list:
            menu_vessel.append(
                each.xpath("@name").extract()[0],
            )
        return menu_vessel

    def get_color_url(self, response):
        color_list = response.xpath("//div[@class='selColor']/ul/li")
        color_vessel = []
        for each in color_list:
            color_vessel.append(
                each.xpath("div/a/@href").extract()[0],
            )
        return color_vessel

    def get_url(self, response):
        return response.xpath("a[2]/@href").extract()[0]

    def get_title(self, response):
        return response.xpath("a[@class='tit']/@title").extract()[0]

    def get_old_price(self, response):
        result = response.xpath("span/text()").extract()[0]
        result = re.search(self.pattern, result).group(0)
        return float(result)

    def get_new_price(self, response):
        result = response.xpath("a[@class='product-img']/h3/span[@class='sprice']/text()").extract()
        if result:
            result = re.search(self.pattern, result[0]).group(0)
            return float(result)
        else:
            return ''

    def get_image_url(self, response):
        return response.xpath("a[@class='product-img']/img/@src").extract()[0]

