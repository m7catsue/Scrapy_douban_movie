# -*- coding: utf-8 -*-
# Item pipeline作用: 清洗数据;保存到数据库;
# Item pipelines range: 0-1000. Items go through from lower valued to higher valued classes.
# 如果scrapy需要运行多个间断的session，则需要自定义CustomRequestFilter和FilterDuplicatePipeline从数据库中获得已保存的item(url)

import logging
import pymongo
from scrapy.utils.project import get_project_settings     # To get settings from settings.py
from scrapy.exceptions import DropItem                    # 通过抛出DropItem exception来扔掉item,后续pipeline将不会收到被扔掉的item
from twisted.enterprise import adbapi


class DropEmptyItemPipeline(object):
    """
    drop掉primary fields为空的item；'页面不存在'导致primary fields为空(title, year...)
    response.xpath("somexpath").extract() 若是xpath路径取不到，则返回为[]，不会有exception
    影视剧(非电影)、短片、极冷僻影片等 取到的length会为空(抓取的item没有length属性)；
    极冷僻的影片actors、genre或language也可能为空(抓取的item没有actors/genre/language属性)
    """
    # 若是只写入MongoDB，可放宽 或 不用DropEmptyItemPipeline；MongoDB collection没有固定structure
    def process_item(self, item, spider):
        # scrapy.Item._values是一个底层的dict，用来实现item[key]=value
        if not 'title' in item._values:
            raise DropItem("Item with empty field [Title] from url: %s\n" % item['url'])
        elif not 'actors' in item._values:
            raise DropItem("Item with empty field [Actors] from url: %s\n" % item['url'])
        elif not 'length' in item._values:
            raise DropItem("Item with empty field [Length] from url: %s\n" % item['url'])
        elif not 'genre' in item._values:
            raise DropItem("Item with empty field [Genre] from url: %s\n" % item['url'])
        elif not 'language' in item._values:
            raise DropItem("Item with empty field [Language] from url: %s\n" % item['url'])
        else:
            return item


class FilterDuplicatePipeline(object):
    """
    通过标准化的url(当作id)来filer duplicate items
    """
    def __init__(self):
        self.items_seen = set()

    def process_item(self, item, spider):
        if item['url'] in self.items_seen:
            raise DropItem("Duplicate item with url: %s\n" % item['url'])
        else:
            self.items_seen.add(item['url'])
            return item


class MysqlPipeline(object):
    """
    用twisted.enterprise.adbapi 将items存入mysql数据库
    Use the adbapi.ConnectionPool class to manage connections;
    Allows adbapi to use multiple connections, one per thread
    """
    def __init__(self):
        settings = get_project_settings()
        self.mysql_host = settings.get('MYSQL_HOST')
        self.mysql_user = settings.get('MYSQL_USER')
        self.mysql_pass = settings.get('MYSQL_PASS')
        self.mysql_db = settings.get('MYSQL_DB')

    def open_spider(self, spider):
        """This method is called when the spider is opened"""
        # twisted.enterprise.adbapi不需import相关mysql模组，只需列出 模组名称 和 该模组connect(...)中的args
        self.dbpool = adbapi.ConnectionPool('pymysql', host=self.mysql_host, user=self.mysql_user,
                                            password=self.mysql_pass, db=self.mysql_db, charset='utf8')

    def close_spider(self, spider):
        """This method is called when the spider is closed"""
        self.dbpool.close()

    def process_item(self, item, spider):
        """Run db query in thread pool"""
        query = self.dbpool.runInteraction(self._conditional_insert, item)
        query.addErrback(self._handle_error, item)                    # _handle_error called if any exception is raised
        return item

    def _conditional_insert(self, txn, item):
        """Create record if doesn't exist"""
        # FilterDuplicatePipeline已经对duplicate items做排重处理
        txn.execute("SELECT * FROM douban_movie_scrapy WHERE title=%s AND myear=%s", (item['title'], item['year']))
        if txn.rowcount == 0:
            txn.execute("INSERT INTO douban_movie_scrapy (title, myear, country, genre, mlanguage, length, "
                        "director, actors, score, image_url, url) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (item['title'], item['year'], item['country'], item['genre'], item['language'], item['length'],
                         item['director'], item['actors'], item['score'], item['image_url'], item['url']))
            # txn对象执行INSERT语句之后 无需 普通数据库连接的conn.commit()语句
            logging.info('Item stored to MySQL with url %s.' % item['url'])
        else:
            logging.info('Item already in MySQL with url %s.' % item['url'])

    def _handle_error(self, error, item):
        """do nothing, just log"""
        logging.error(error)
        logging.info('*** Insert operation (MySQL) failed: %s ***\n' % item['url'])


class MongodbPipeline(object):
    """
    将抓取的数据存入MongoDB
    """
    def __init__(self):
        settings = get_project_settings()
        self.mongo_host = settings.get('MONGODB_HOST')
        self.mongo_port = settings.get('MONGODB_PORT')
        self.mongo_db_name = settings.get('MONGODB_DB')
        self.mongo_collection_name = settings.get('MONGODB_COLLECTION')

    def open_spider(self, spider):
        """This method is called when the spider is opened"""
        self.connection = pymongo.MongoClient(self.mongo_host, self.mongo_port)
        self.db = self.connection[self.mongo_db_name]

    def close_spider(self, spider):
        """This method is called when the spider is closed"""
        self.connection.close()

    def process_item(self, item, spider):
        """Insert data into MongoDB collection"""
        # FYI.使用class attribute, 在__init__时 connection需为self.connection,
        # 若在__init__中没有加self，则在process_item()的scope中取不到connection
        # FilterDuplicatePipeline已经对duplicate items做排重处理
        try:
            self.db[self.mongo_collection_name].insert(dict(item))
            logging.info('Item stored to MongoDB with url %s.' % item['url'])
            return item
        except Exception:
            logging.info('*** Insert operation (MongoDB) failed: %s ***\n' % item['url'])
            return item

