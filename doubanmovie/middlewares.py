# -*- coding: utf-8 -*-

import logging
import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.utils.project import get_project_settings                               # To get settings from settings.py


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """
    从user_agent_list中随机抽取一个 作为request的user_agent
    """
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        settings = get_project_settings()
        self.user_agent_list = settings.get('USER_AGENT_LIST')

    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        if ua:
            request.headers.setdefault('User-Agent', ua)
            #logging.info('***[User Agent] %s ***' % ua)

