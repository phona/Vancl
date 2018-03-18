# -*- coding: utf-8 -*-
import scrapy

from scrapy.http.request import Request
from vancl.items import ImageItem
from vancl.pipelines import Saving, DB

class ImagesSpider(scrapy.Spider):
    name = 'images'
    allowed_domains = ['*']
    # start_urls = ['http://0.0.0.0:8000']

    def __init__(self, *args, **kwargs):
        super(ImagesSpider, self).__init__(*args, **kwargs)
        self.conn = Saving(host=DB['host'],
                           port=DB['port'],
                           user=DB['user'],
                           passwd=DB['passwd'],
                           autocommit=DB['autocommit'],
                           charset="utf8",
                           db=DB['name'])

    def get_images_url(self, table):
        with self.conn:
            return self.conn.get_url(table, "original")

    def get_requests(self, item, urls):
        for url in urls:
            yield Request(url[0])

    def start_requests(self):
        urls = self.get_images_url("items_items")
        if urls:
            item = ImageItem()
        yield item

    def close(self, reason):
        self.conn.close()

    def parse(self, response):
        pass
