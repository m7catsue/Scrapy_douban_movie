# -*- coding: utf-8 -*-
# [*]scrapy.http.Request: dont_filter (boolean) – indicates that this request should not be filtered by the scheduler.
# This is used when you want to perform an identical request multiple times, to ignore the duplicates filter.
# Use it with care, or you will get into crawling loops. Default to False.
# [*] 对于xpath表达式中有unicode字符：
# u'' string literals are Python syntax, not part of XPath. e.g. u"//*[contains(.,'café')]"

from scrapy.loader import ItemLoader
from doubanmovie.items import DoubanmovieItem
import scrapy
import time
import socket


class BasicSpider(scrapy.Spider):
    """
    For test purpose
    """
    name = "basic"                                                             # scrapy shell命令使用的是spider name 'basic'
    allowed_domains = ["movie.douban.com"]                                    # allowed_domains加‘https://’和'/'等字符会被offsite filter过滤掉
    start_urls = ('https://movie.douban.com/subject/4811813/',
                  'https://movie.douban.com/subject/7054604/',)

    def parse(self, response):
        """
        parse一个具体豆瓣电影的页面；
        response.xpath("somexpath").extract()若是xpath路径取不到，则返回为[]，不会有exception
        以下@开头的是scrapy的contract，在命令行输入scrapy check basic来检验spider的功能

        @url https://movie.douban.com/subject/4811813/
        @returns items 1
        @scrapes title year country genre language length director actors score image_url
        @scrapes url project spider server datetime
        """
        # 取得下一波需要跳转到的url的response(由request返回)
        for next_page_url in response.xpath(
                "//*[@id='recommendations']/div[@class='recommendations-bd']/dl/dd/a/@href").extract():
            yield scrapy.Request(next_page_url, callback=self.parse)                # yield response with callback

        l = ItemLoader(item=DoubanmovieItem(), response=response)

        # Load primary fields using XPath expressions
        l.add_xpath('title', "//div[@id='content']/h1/span[@property='v:itemreviewed']/text()")
        l.add_xpath('year', "//div[@id='content']/h1/span[@class='year']/text()")
        # '/following::text()[1]' 取得位于span之下的（同缩进的）单独一行string
        l.add_xpath('country', u"//*[@id='info']/span[@class='pl' and text()='制片国家/地区:']/following::text()[1]")
        l.add_xpath('genre', "//*[@id='info']//span[@property='v:genre']/text()")
        l.add_xpath('language', u"//*[@id='info']/span[@class='pl' and text()='语言:']/following::text()[1]")
        l.add_xpath('length', "//*[@id='info']/span[@property='v:runtime']/text()")
        l.add_xpath('director', "//*[@id='info']/span[1]/span[@class='attrs']//a/text()")
        l.add_xpath('actors', "//*[@id='info']/span[@class='actor']/span[@class='attrs']/a/text()")
        l.add_xpath('score', "//*[@id='interest_sectl']//strong[@property='v:average']/text()")
        l.add_xpath('image_url', "//*[@id='mainpic']/a/img/@src")               # 电影海报图片链接

        # Housekeeping fields
        l.add_value('url', response.url)                                            # 当前页面url(未标准化的)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', socket.gethostname())
        l.add_value('datetime', time.strftime("%Y-%m-%d %H:%M:%S"))              # 当前时间

        yield l.load_item()

