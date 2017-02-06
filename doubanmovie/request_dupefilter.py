# -*- coding: utf-8 -*-
# scrapy默认设置：DUPEFILTER_CLASS = 'scrapy.dupefilter.RFPDupeFilter'
# 测试 customised request filter
# 如果scrapy需要运行多个间断的session，则需要自定义CustomRequestFilter和FilterDuplicatePipeline从数据库中获得已保存的item(url)

from scrapy.dupefilters import RFPDupeFilter


class CustomRequestFilter(RFPDupeFilter):
    """
    通过url中 https://movie.douban.com/subject/...(id).../ 来去重的custom request filter
    """
    def request_fingerprint(self, request):
        """取得request_fingerprint (subject id)"""
        subject_id_index = request.url.split('/').index('subject') + 1
        request_fingerprint = request.url.split('/')[subject_id_index]
        return request_fingerprint



