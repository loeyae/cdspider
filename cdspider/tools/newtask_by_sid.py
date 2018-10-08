#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-8-14 14:56:32
"""
from cdspider.tools import Base

class newtask_by_sid(Base):
    """
    newtask by site
    """
    def process(self, *args):
        sid = int(self.get_arg(args, 0, 'Pleas input sid'))
        uid = int(self.get_arg(args, 1, 'Pleas input start uid'))
        maxuid = 0
        if len(args) > 2:
            maxuid = int(args[2])
        self.broken('Site not exists', sid)
        site = self.g['db']['SitesDB'].get_detail(sid)
        self.broken('Site: %s not exists' % sid, site)
        self.notice('Selected Site Info:', site)
        UrlsDB = self.g['db']['UrlsDB']
        while True:
            i = 0
            for item in UrlsDB.get_new_list(uid, sid, where={'status': {"$in": [UrlsDB.STATUS_INIT, UrlsDB.STATUS_ACTIVE]}}):
                task = self.g['db']['TaskDB'].get_list(int(item['pid']) or 1, {"uid": item['uid'], "aid": 0})
                if len(list(task)) > 0:
                    continue
                d={}
                d['uid'] = item['uid']
                self.info("push newtask_queue data: %s" %  str(d))
                self.g['queue']['newtask_queue'].put_nowait(d)
                i += 1
                if item['uid'] > uid:
                    uid = item['uid']
                if maxuid > 0 and maxuid <= uid:
                    return
            if i < 1:
                return
