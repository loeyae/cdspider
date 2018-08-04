#-*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-1-9 17:43:17
:version: SVN: $Id: Urlsdb.py 2119 2018-07-04 03:56:41Z zhangyi $
"""

{
    "urls": {
        'uid': int,           # url id
        'title': str,         # title
        'siteid': int,        # site id
        'url': str,           # url
        'rate': int,          # int
        'status': int,        # status
        'base_request': str,  # 基础请求配置
        'main_process': str,  # 主流程配置
        'sub_process': str,   # 子流程配置
        'identify': str,      # 生成unique id的配置
        'createtime': int,    # create time
        'updatetime': int,    # last update time
        'creator': str,       # creator
        'updator': str,       # updator
    }
}

class UrlsDB(object):

    URLS_STATUS_INIT = 0
    URLS_STATUS_ACTIVE = 1
    URLS_STATUS_DISABLE = 2
    URLS_STATUS_DELETED = 3

    def insert(self, obj = {}):
        raise NotImplementedError

    def update(self, id, obj = {}):
        raise NotImplementedError

    def enable(self, id, where):
        raise NotImplementedError

    def enable_by_site(self, sid, where):
        raise NotImplementedError

    def enable_by_project(self, pid, where):
        raise NotImplementedError

    def delete(self, id, where):
        raise NotImplementedError

    def delete_by_site(self, sid, where):
        raise NotImplementedError

    def delete_by_project(self, pid, where):
        raise NotImplementedError

    def active(self, id, where):
        raise NotImplementedError

    def disable(self, id, where):
        raise NotImplementedError

    def disable_by_site(self, sid, where):
        raise NotImplementedError

    def disable_by_project(self, pid, where):
        raise NotImplementedError

    def get_detail(self, id):
        raise NotImplementedError

    def get_list(self, where = {}, select=None, **kwargs):
        raise NotImplementedError

    def get_new_list(self, id, site, select=None, **kwargs):
        raise NotImplementedError

    def get_max_id(self, siteid):
        raise NotImplementedError
