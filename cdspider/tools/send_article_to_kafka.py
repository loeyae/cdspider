#-*- coding: utf-8 -*-

'''
Created on 2018年8月9日

@author: Wang Fengwei
'''
import json
import traceback
from cdspider.tools import Base
import time

class send_article_to_kafka(Base):

    def process(self, *args, **kwargs):
        where = json.loads(self.get_arg(args, 0, 'Pleas input where'))
        created = int(time.time())
        if len(args) > 1:
            created = int(args[1])
        sum=0
        acid = '0'
        if len(args) > 2:
            acid = args[2]
        checked = True
        if len(args) > 3:
            checked = bool(int(args[3]))
        where['status'] = 1
        self.notice('Where Info:', where, checked = checked)
        while True:
            try:
                n=0
                where['acid'] = {"$gt": acid}
                for item in self.g['db']['ArticlesDB'].get_list(created, where=where, sort=[('acid', 1)], hits = 200):
                    n=n+1
                    sum=sum+1
                    d={}
                    d['rid']=item['rid']
                    d['on_sync']='publicOpinionCustomeNS:publicOpinionCustomeTB001'
                    self.info("import status_queue data: %s, last acid: %s" %  (str(d), item['acid']))
                    acid=item['acid']
                    self.g['queue']['result2kafka'].put_nowait(d)
                if n==0:
                    break
                time.sleep(0.2)
            except:
                self.error(traceback.format_exc())
                if not checked:
                    continue
                else:
                    break
        print(str(sum))
