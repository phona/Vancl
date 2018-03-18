import re
import threading
import hashlib
import os.path
from queue import Queue

import requests
from pipelines import DB, Saving
from settings import DEFAULT_REQUEST_HEADERS, IMAGES_STORE
from scrapy.utils.python import to_bytes


__all__ = [
    'Thread', 'ThreadPool', 'Tasks'
]

# download picture for color


class ThreadPool(object):
    def __init__(self, threads):
        self.thread_count = threads
        self.thread_pool = []

    def ready(self, worker, tasks):
        """
        create thread_pool
        :param worker:
        :return: None
        """
        if self.thread_count > 0:
            self.thread_pool.append(worker(tasks))
            self.thread_count -= 1
        else:
            raise(Exception("The pool is aready full."))

    def start(self):
        for i in range(len(self.thread_pool)):
            self.thread_pool[i].setDaemon()
            self.thread_pool[i].start()
            self.thread_pool[i].join()


class Thread(threading.Thread):

    middle_file = "color"
    pattern = re.compile(r"product/.*?/.*?/.*?/(\d+)/")

    def __init__(self, tasks, name):
        super(Thread, self).__init__()
        self.tasks = tasks
        self.name = name

    def run(self):
        """
        Provide a thread object to do requests from thread_pool object

        :parm url: input each url as requests.
        :rtype: None
        :return: None
        """
        while True:
            request = self.tasks.get()
            response = requests.get(url=request[0], headers=DEFAULT_REQUEST_HEADERS)
            path = {
                "path": self.get_image_path(response.content),
                "url": request[0],
            }
            with open(os.path.join(IMAGES_STORE, path["path"]), "wb") as picture:
                picture.write(os.path.join(IMAGES_STORE,
                                           self.get_image_path(path["url"])))
            self.tasks.update(path)
            self.tasks.task_done()

    def color_url(self, request):
        item_color = request[0]
        productcode = re.search(self.pattern, self.tasks.get_product_code(request[1])).group(1)
        return "http://item.vancl.com/styles/AjaxChangeProduct.aspx?productcode=%s&point=0&ref=%s&source=&fresh=0.9281119133434976" % (productcode, item_color)


    def get_image_path(self, url):
        media_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
        media_ext = os.path.splitext(url)[1]  # change to request.url after deprecation

        return r'full\%s\%s\%s\%s%s' % (self.name,
                                        self.middle_file,
                                        self.name,
                                        media_guid,
                                        media_ext)

class Tasks(object):
    """
    Task object contain queue and database method.
    make convenience read and write data.
    """
    def __init__(self):
        self.tasks = Queue()
        self.conn = Saving(host=DB['host'],
                           port=DB['port'],
                           user=DB['user'],
                           passwd=DB['passwd'],
                           autocommit=DB['autocommit'],
                           charset="utf8",
                           db=DB['name'])

    def put(self):
        for i in self.get_urls():
            self._put(i[0])

    def _put(self, item):
        self.tasks.put(item)

    def taskdone(self):
        self.tasks.task_done()

    def get(self):
        return self.tasks.get()

    def get_urls(self):
        """
        get urls from table items_itemcolor
        :rtype : tuple
        :return: tuple of list
        """
        return self.conn.get_url("items_itemcolor", "original, item_id_id")

    def get_product_code(self, fk):
        query = "SELECT original FROM items_items WHERE id={0}".format(fk)
        self.conn.cur.execute(query)
        return self.conn.cur.fetchone()[0]

    def update(self, path):
        """
        inherit from Saving object
        :param table:
        :param data:
        :return:
        """
        data = {
            "set": "path",
            "set_val": path["path"],
            "where": "original",
            "where_val": path["url"],
        }
        self.conn.update("items_itemcolor", data)


if __name__ == "__main__":
    test_tasks = Tasks()
    test_thead = Thread(test_tasks, "test")
    url = test_tasks.get_urls()
    print(test_thead.color_url(url[0]))

