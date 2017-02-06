# -*- coding: utf-8 -*-

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst


class DoubanmovieItem(scrapy.Item):
    """
    每个豆瓣电影页面所要抓取的item；
    input_processor: processing extracted data as soon as it’s received (through methods like (add_xpath)...)
    output_processr: processing data when ItemLoader.load_item() is called, thus producing the final value assigned to item
    在output_processor之前是['myvalue']或['a', 'b', 'c']的形式，需要以string的形式写入database
    """
    # Primary fields
    title = scrapy.Field(
        output_processor=TakeFirst()
    )
    year = scrapy.Field(                                             # MapCompose对list中的每一个元素x操作
        input_processor=MapCompose(lambda x: x[1:-1]),               # 去除电影年份(list中只有1个str)前后的括号
        output_processor=TakeFirst()
    )
    country = scrapy.Field(
        input_processor=MapCompose(lambda x: x.replace('/', ',')),   # 将'国家'(list中只有1个str)中的'/'替换为','
        output_processor=lambda x: ','.join(x)                       # x是整个list
    )
    genre = scrapy.Field(
        output_processor=lambda x: ','.join(x)
    )
    language = scrapy.Field(
        input_processor=MapCompose(lambda x: x.replace('/', ',')),   # 将'语言'(list中只有1个str)中的'/'替换为','
        output_processor=lambda x: ','.join(x)
    )
    length = scrapy.Field(
        output_processor=TakeFirst()
    )
    director = scrapy.Field(
        output_processor=lambda x: ','.join(x)
    )
    actors = scrapy.Field(                                           # 这里x指整个list
        input_processor=lambda x: x[:5] if len(x) > 5 else x,        # actors是一个有多个元素的list，取其前5位元素(actor)
        output_processor=lambda x: ','.join(x)
    )
    score = scrapy.Field(
        output_processor=TakeFirst()
    )

    image_url = scrapy.Field(
        output_processor=TakeFirst()
    )

    # Housekeeping fields
    url = scrapy.Field(
        input_processor=MapCompose(
            # 将url的格式标准化，统一形式为'https://movie.douban.com/subject/2129039/'
            lambda x: '/'.join(x.split('/')[:-1]) + '/' if not x.endswith('/') else x),
        output_processor=TakeFirst()
    )
    project = scrapy.Field(
        output_processor=TakeFirst()
    )
    spider = scrapy.Field(
        output_processor=TakeFirst()
    )
    server = scrapy.Field(
        output_processor=TakeFirst()
    )
    datetime = scrapy.Field(
        output_processor=TakeFirst()
    )


