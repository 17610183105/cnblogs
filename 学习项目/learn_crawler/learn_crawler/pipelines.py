# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import codecs
import json
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
import MySQLdb


def get_insert_sql(self):
    insert_sql ="insert into cnblogs VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(title)"

    params = (
        self.get("title", ""),
        self.get("image_url", ""),
        self.get("image_path", ""),
        self.get("read_num", 0),
    )

    return insert_sql, params


class LearnCrawlerPipeline:
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'a', encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False,) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "image_url" in item:
            for ok,value in results:
                image_path = value['path']
                item['image_path'] = image_path
        return item


class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常
        return item

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql = "insert into cnblogs VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE title=VALUES(title)"
        params = []
        params.append(item.get("title", ""))
        image_url_str = ",".join(item.get("image_url",[]))
        params.append(image_url_str)
        params.append(item.get("image_path", ""))
        params.append(item.get("read_num", 0))

        cursor.execute(insert_sql, params)