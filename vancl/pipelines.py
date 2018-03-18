# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os.path
import hashlib
import types

from MySQLdb.connections import Connection

from scrapy.http.request import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.utils.python import to_bytes
from vancl.items import VanclItem

DB = {
    'host': 'localhost',
    'port': 3306,
    'user': 'tao',
    'passwd': 'tao',
    'autocommit': True,
    'name': 'mysite',
}

class Saving(Connection):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.cur = self.cursor()

    def get_id(self, productcode):
        query = "SELECT ID FROM items_items WHERE productcode={0};".format(productcode)
        # print(query)
        self.cur.execute(query)
        return self.cur.fetchone()[0]

    def get_url(self, table):
        query = "SELECT original FROM {0} where path is null;".format(table)
        # print(query)
        self.cur.execute(query)
        return self.cur.fetchall()

    def insert(self, table, data):
        stance = len(data) * ['%s']
        query = "INSERT INTO {0} ({1}) VALUES ({2});".format(table,
                                                             ','.join(data.keys()),
                                                             ','.join(stance))
        # print(query, data.values())
        self.cur.execute(query, data.values())

    def update(self, table, data):
        query = "UPDATE {0} SET {1}='{2}' where {3}='{4}';".format(table,
                                                                   data["set"],
                                                                   data["set_val"],
                                                                   data["where"],
                                                                   data["where_val"])
        # print(query)
        self.cur.execute(query)


class MainPipeline(object):

    def __init__(self):
        self.conn = Saving(host=DB['host'],
                           port=DB['port'],
                           user=DB['user'],
                           passwd=DB['passwd'],
                           autocommit=DB['autocommit'],
                           charset="utf8",
                           db=DB['name'])

    def process_item(self, item, spider):
        if isinstance(item, VanclItem):
            return self.main_process(item, spider)
        else:
            return self.color_process(item, spider)

    def color_process(self, item, spider):
        fk = self.conn.get_id(item['productcode'])
        for size in item['color_image_url']:
            for url in item['color_image_url'][size]:
                self.insert_item("items_itemcolor", self.sub_color(fk,
                                                                   item['color_name'],
                                                                   item['color_code'],
                                                                   size,
                                                                   url))
        return item

    def main_process(self, item, spider):
        item['item_type'] = spider.name
        self.insert_item("items_items", self.list_page(item))

        fk = self.conn.get_id(item['productcode'])
        for url in item['menu_image_url']:
            self.insert_item("items_itemmenuimage",
                              self.sub_menu(fk, url))
        for url in item['display_image_url']:
            self.insert_item("items_itemdisplayimage",
                              self.sub_display(fk, url))
        return item

    def list_page(self, item):
        data = {
            'title': item['title'],
            'new_price': item['new_price'],
            'old_price': item['old_price'],
            'item_type': item['item_type'],
            'original': item['original'],
            'productcode': item['productcode'],
        }
        return data

    def sub_color(self, fk, name, code, size, url):
        data = {
            'item_id_id': fk,
            'name': name,
            'size': size,
            'original': url,
        }
        return data

    def sub_menu(self, fk, url):
        data = {
            'item_id_id': fk,
            'original': url
        }
        return data

    def sub_display(self, fk, url):
        data = {
            'item_id_id': fk,
            'original': url
        }
        return data

    def insert_item(self, table, data):
        with self.conn:
            self.conn.insert(table, data)

    def close_spider(self, spider):
        self.conn.close()
        self.conn.cur.close()


class MotherImagesPipeline(ImagesPipeline):

    table = ""
    middle_file = ""
    def open_spider(self, spider):
        self.spiderinfo = self.SpiderInfo(spider)
        self.conn = Saving(host=DB['host'],
                           port=DB['port'],
                           user=DB['user'],
                           passwd=DB['passwd'],
                           autocommit=DB['autocommit'],
                           charset="utf8",
                           db=DB['name'])

    def get_images_url(self):
        with self.conn:
            return self.conn.get_url(self.table)

    def get_media_requests(self, item, info):
        urls = self.get_images_url()
        if urls:
            for request in self.get_requests(item, urls):
                yield request
        # print(self.get_requests(item, info, urls))

    def get_requests(self, item, urls):
        for url in urls:
            yield Request(url[0])

    def item_completed(self, results, item, info):
        image_paths = [x for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contain no images")
        for path in image_paths:
            data = {
                "set": "path",
                "set_val": path["path"],
                "where": "original",
                "where_val": path['url'],
            }
            with self.conn:
                self.conn.update(self.table, data)
            # print(item)
        # return item

    def file_path(self, request, response=None, info=None):
        ## start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('FilesPipeline.file_key(url) method is deprecated, please use '
                          'file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        ## end of deprecation warning block

        media_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
        media_ext = os.path.splitext(url)[1]  # change to request.url after deprecation

        if self.middle_file:
            return 'full/%s/%s/%s/%s%s' % (self.spiderinfo.spider.name,
                                           self.middle_file,
                                           self.spiderinfo.spider.name,
                                           media_guid,
                                           media_ext)
        else:
            return 'full/%s/%s%s' % (self.spiderinfo.spider.name, media_guid, media_ext)


class ListImagesPipeline(MotherImagesPipeline):

    table = "items_items"


class ColorImagesPipeline(MotherImagesPipeline):

    table = "items_itemcolor"
    middle_file = "color"

class MenuImagesPipeline(MotherImagesPipeline):

    table = "items_itemmenuimage"
    middle_file = "menu"

class DisplayImagesPipeline(MotherImagesPipeline):

    table = "items_itemdisplayimage"
    middle_file = "display"


if __name__ == "__main__":
    # a = Saving(DB)
    conn = Saving(host=DB['host'],
                  port=DB['port'],
                  user=DB['user'],
                  passwd=DB['passwd'],
                  autocommit=DB['autocommit'])
    cur = conn.cursor()
    with conn:
        cur.execute("USE mysite;")
        cur.execute("SELECT ID FROM items_items WHERE productcode=6378499;")
        print(cur.fetchone()[0])
    cur.close()
    conn.close()
