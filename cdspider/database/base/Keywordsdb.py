#-*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-1-9 17:32:52
:version: SVN: $Id: Keywordsdb.py 2119 2018-07-04 03:56:41Z zhangyi $
"""
{
    'keywords': {
        'kwid': int,        # keywords id
        'word': str,        # keyword
        'status': int,      # status
        'rate': str,        # 关键词来源
        'src': str,         # 来源
        'ctime': int,       # 创建时间
        'utime': int,       # 最后一次更新时间
        'creator': str,     # 创建人
        'updator': str,     # 最后一次更新的人
    }
}

from . import Base

class KeywordsDB(Base):

    KEYWORDS_STATUS_INIT = 0
    KEYWORDS_STATUS_ACTIVE = 1
    KEYWORDS_STATUS_DISABLE = 2
    KEYWORDS_STATUS_DELETED = 3


    def insert(self, obj={}):
        raise NotImplementedError

    def update(self, id, obj={}):
        raise NotImplementedError

    def active(self, id, where = {}):
        raise NotImplementedError

    def disable(self, id, where = {}):
        raise NotImplementedError

    def delete(self, id, where = {}):
        raise NotImplementedError

    def get_detail(self, id):
        raise NotImplementedError

    def get_list(self, where = {}, select=None, **kwargs):
        raise NotImplementedError
