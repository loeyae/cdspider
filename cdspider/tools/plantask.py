#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-8-20 15:47:13
"""
import time
import random
from cdspider.tools import Base

class plantask(Base):
    """
    put you comment
    """
    def process(self, *args):
        pid = int(self.get_arg(args, 0, 'Pleas input project sid'))
        sid = int(self.get_arg(args, 1, 'Pleas input site id'))
        maxn = int(self.get_arg(args, 2, 'Pleas input random max'))

        self.broken('Site not exists', sid)
        site = self.g['db']['SitesDB'].get_detail(sid)
        self.broken('Site: %s not exists' % sid, site)
        self.notice('Selected Site Info:', site)
        task_db = self.g['db']['TaskDB']
        id = 0
        while True:
            i = 0
            for item in task_db.get_list(pid, where={'sid': sid, 'tid': {"$gt": id}}):
                d={}
                d['plantime']=int(time.time())+random.randint(1, maxn)
                self.info("update plantime from %s to: %s" % (item['plantime'], d['plantime']))
                task_db.update(item['tid'], pid, d)
                i += 1
                if item['tid'] > id:
                    id = item['tid']
            if i < 1:
                return
