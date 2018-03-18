# -*- coding: utf-8 -*-
import re
import logging

import scrapy
from scrapy.http.request import Request
from vancl.items import VanclItem, ColorItem
from scrapy.utils.log import configure_logging
from collections import defaultdict


class CoatsSpider(scrapy.Spider):
    name = 'coats'
    allowed_domains = ['vancl.com']
    start_urls = ['http://coats.vancl.com/']

    # self defined parameters
    pattern = re.compile(r"\d+")
    color_url = "http://item.vancl.com/styles/AjaxChangeProduct.aspx?productcode={0}&point=0&ref=item_color_{1}&source=&fresh=0.806010595391426"

    def parse(self, response):
        """
        List page collected
        :param response:
        :return:
        """
        item_list = response.xpath("//ul[@class='shirts-product-list']/li")
        for each in item_list:
            item = VanclItem()
            item['title'] = self.get_title(each)
            item['old_price'] = self.get_old_price(each)
            item['new_price'] = self.get_new_price(each)
            item['original'] = self.get_image_url(each)
            item['productcode'] = self.get_product_code(each)
            yield item
            yield Request(url=self.get_url(each),
                          callback=self.sec_parse,
                          meta={'item':item})

    def sec_parse(self, response):
        """
        collecting all images for a item
        :param response:
        :return:
        """
        item = response.meta['item']
        item["menu_image_url"] = self.get_menu_url(response)
        item["display_image_url"] = self.get_display_url(response)
        yield item

        color_name_code = self.get_color_name_code(response)
        for name, code in color_name_code:
            color_item = ColorItem()
            color_item["productcode"] = item["productcode"]
            color_item["color_name"] = name
            color_item["color_code"] = code
            yield Request(url=self.color_url.format(item['productcode'],
                                                    code),
                          callback=self.thd_parse,
                          meta={'color_item':color_item})

    def thd_parse(self, response):
        """
        collecting each color images
        :param response:
        :return:
        """
        color_item = response.meta['color_item']
        color_item['color_image_url'] = defaultdict(list)
        for i in self.get_color_small(response):
            color_item['color_image_url']['small'].append(i)
        color_item['color_image_url']['mid'].append(self.get_color_big(response))

        yield color_item

    def get_color_big(self, response):
        return response.xpath("//img[@id='midimg']/@src").extract()[0]

    def get_color_small(self, response):
        return response.xpath("//span[@class='SpriteSmallImgs']/@name").extract()

    def get_display_url(self, response):
        display_list = response.xpath("//tr[@class='firstRow']")
        display_vessel = []
        for each in display_list:
            display_vessel.append(
                each.xpath("td/img/@src").extract()[0],
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

    def get_product_code(self, response):
        result = response.xpath("a[@class='tit']/@href").extract()[0]
        result = re.search(self.pattern, result).group(0)
        return int(result)


    def get_color_name_code(self, response):
        color_list = response.xpath("//div[@class='selColor']/ul/li")
        color_vessel = []
        for each in color_list:
            color_vessel.append([each.xpath("@title").extract()[0],
                                 int(each.xpath("@name").extract()[0])],)
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
            return float(0)

    def get_image_url(self, response):
        return response.xpath("a[@class='product-img']/img/@src").extract()[0]


configure_logging(install_root_handler=False)
logging.basicConfig(
    filename='log.txt',
    format='%(levelname)s: %(message)s',
    level=logging.INFO
)