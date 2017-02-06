# -*- coding: utf-8 -*-

import scrapy
from scrapy.loader import ItemLoader
from doubanmovie.items import DoubanmovieItem
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import time
import socket


class DoubanMovieSpider(scrapy.Spider):
    """
    DoubanMovieSpider 抓取豆瓣电影页面信息
    """
    name = "montion2"                                                        # scrapy shell命令使用的是spider name 'basic'
    allowed_domains = ["movie.douban.com"]                                  # allowed_domains加‘https://’和'/'等字符会被offsite filter过滤掉
    phantomJS_executable_path = \
        r'C:\Users\m7catsue\Desktop\phantomjs-2.1.1-windows\bin\phantomjs.exe'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.63 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8'}

    def start_requests(self):
        """从豆瓣电影首页 和 豆瓣电影top250 获取首批url"""
        yield scrapy.Request('https://movie.douban.com/', callback=self.parse_front_page)

        for x in xrange(0, 250, 25):                                        # 豆瓣top250的10个index页面(0，25，50...225)
            yield scrapy.Request(
                ('https://movie.douban.com/top250?start=%s&filter=' % x), callback=self.parse_top250_index_page)

    def parse_front_page(self, response):
        """豆瓣电影首页'正在上映' 和 '热门推荐'影片的页面url"""
        # '正在上映'影片
        page_urls = response.xpath(
            "//*[@id='screening']/div[@class='screening-bd']/ul/li/ul/li[@class='title']/a/@href").extract()
        for page_url in page_urls:
            yield scrapy.Request(page_url, callback=self.parse)

        # '热门推荐'影片(需执行Javascript)
        for key in self.headers:                                            # set custom headers for selenium PhantomJS
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = self.headers[key]

        driver = webdriver.PhantomJS(executable_path=self.phantomJS_executable_path)
        driver.get(response.url)
        WebDriverWait(driver, 4).until(
            expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'list-wp')))

        link_elements = driver.find_elements_by_xpath("//*[@id='gaia']/div[@class='list-wp']/div/a")
        for link_element in link_elements:
            page_url = link_element.get_attribute('href')
            yield scrapy.Request(page_url, callback=self.parse)

        driver.close()                                                       # 关闭web driver

    def parse_top250_index_page(self, response):
        """从豆瓣电影top250 index页面获取 top250电影页面url"""
        page_urls = response.xpath(
            "//*[@id='content']/div[@class='grid-16-8 clearfix']/div[@class='article']/ol/li/div[@class='item']/div[@class='pic']/a/@href"
        ).extract()
        for page_url in page_urls:
            yield scrapy.Request(page_url, callback=self.parse)

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
            yield scrapy.Request(next_page_url, callback=self.parse)                   # yield response with callback

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

