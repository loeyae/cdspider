#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-12-2 15:16:45
"""
import copy
import time
from . import BaseHandler
from cdspider.database.base import *
from cdspider.libs.constants import *
from cdspider.libs import utils
from cdspider.parser import CustomParser

class InteractHandler(BaseHandler):
    """
    interact handler
    :property task 爬虫任务信息 {"mode": "interact", "uuid": SpiderTask.interact uuid}
                   当测试该handler，数据应为 {"mode": "interact", "url": url, "interactionNumRule": 互动数规则，参考互动数规则}
    """
    def get_scripts(self):
        """
        获取自定义脚本
        """
        try:
            rule = self.match_rule()
            return rule.get("scripts", None)
        except:
            return None

    def init_process(self, save):
        """
        初始化爬虫流程
        :output self.process {"request": 请求设置, "parse": 解析规则, "paging": 分页规则, "unique": 唯一索引规则}
        """
        if "interactionNumRule" in self.task:
            self.task['parent_url'] = self.task['url']
            self.task['acid'] = "testing_mode"
            typeinfo = utils.typeinfo(self.task['parent_url'])
            if typeinfo['domain'] != self.task['interactionNumRule']['domain'] or typeinfo['subdomain'] != self.task['interactionNumRule']['subdomain']:
                raise CDSpiderNotUrlMatched()
            crawler = self.get_crawler(self.task.get('interactionNumRule', {}).get('request'))
            crawler.crawl(url=self.task['parent_url'])
            data = utils.get_attach_data(CustomParser, crawler.page_source, self.task['parent_url'], self.task['interactionNumRule'], self.log_level)
            if data == False:
                return None
            url, params = utils.build_attach_url(data, self.task['interactionNumRule'], self.task['parent_url'])
            del crawler
            if not url:
                raise CDSpiderNotUrlMatched()
            self.task['url'] = url
            save['base_url'] = url
            save["hard_code"] = params
            self.task['interactionNumRule']['request']['hard_code'] = data
        else:
            article = self.db['ArticlesDB'].get_detail(self.task['parentid'], select=['url', 'acid'])
            if not article:
                raise CDSpiderHandlerError("aritcle: %s not exists" % self.task['parentid'])
            self.task['acid'] = article['acid']
        self.process = self.match_rule()

    def match_rule(self):
        """
        获取匹配的规则
        """
        parse_rule = self.task.get("interactionNumRule", {})
        if not parse_rule:
            '''
            如果task中包含列表规则，则读取相应的规则，否则在数据库中查询
            '''
            ruleId = self.task.get('kid', 0)
            parse_rule = self.db['AttachmentDB'].get_detail(ruleId)
            if not parse_rule:
                raise CDSpiderDBDataNotFound("interactionNumRule: %s not exists" % self.task['kid'])
            if parse_rule['status'] != AttachmentDB.STATUS_ACTIVE:
                raise CDSpiderHandlerError("interaction num rule not active")
        return parse_rule

    def route(self, mode, save):
        """
        schedule 分发
        :param mode  project|site 分发模式: 按项目|按站点
        :param save 传递的上下文
        :return 包含uuid的迭代器，项目模式为项目的uuid，站点模式为站点的uuid
        :notice 该方法返回的迭代器用于router生成queue消息，以便plantask听取，消息格式为:
        {"mode": route mode, "h-mode": handler mode, "uuid": uuid}
        """
        if not "id" in save:
            save["id"] = 0
        if mode == ROUTER_MODE_PROJECT:
            for item in self.db['ProjectsDB'].get_new_list(save['id'], select=["uuid"]):
                if item['uuid'] > save['id']:
                    save['id'] = item["uuid"]
                yield item['uuid']
        elif mode == ROUTER_MODE_SITE:
            if not "pid" in save:
                save["pid"] = 0
            for item in self.db['ProjectsDB'].get_new_list(save['pid'], select=["uuid"]):
                while True:
                    has_item = False
                    for each in self.db['SitesDB'].get_new_list(save['id'], item['uuid'], select=["uuid"]):
                        has_item = True
                        if each['uuid'] > save['id']:
                            save['id'] = each['uuid']
                        yield each['uuid']
                    if not has_item:
                        break
                if item['uuid'] > save['pid']:
                    save['pid'] = item['uuid']
        elif mode == ROUTER_MODE_TASK:
            '''
            按任务分发
            '''
            if not "pid" in save:
                '''
                初始化上下文中的pid参数,该参数用于项目数据查询
                '''
                save["pid"] = 0
            for item in self.db['ProjectsDB'].get_new_list(save['pid'], select=["uuid"]):
                while True:
                    has_item = False
                    for each in self.db['TaskDB'].get_new_list(save['id'], where={"pid": item['uuid']}, select=["uuid"]):
                        has_item = True
                        if each['uuid'] > save['id']:
                            save['id'] = each['uuid']
                        yield each['uuid']
                    if not has_item:
                        break
                if item['uuid'] > save['pid']:
                    save['pid'] = item['uuid']

    def schedule(self, message, save):
        """
        根据router的queue消息，计划爬虫任务
        :param message route传递过来的消息
        :param save 传递的上下文
        :return 包含uuid, url的字典迭代器，为SpiderTaskDB中数据
        :notice 该方法返回的迭代器用于plantask生成queue消息，以便fetch听取，消息格式为
        {"mode": handler mode, "uuid": SpiderTask uuid, "url": SpiderTask url}
        """
        mode = message['mode']
        if not 'id' in save:
            save['id'] = 0
        if mode == ROUTER_MODE_PROJECT:
            if not 'tid' in save:
                save['tid'] = 0
            for item in self.db['TaskDB'].get_new_list(save['tid'], where={"pid": message['item']}):
                self.debug("%s schedule task: %s" % (self.__class__.__name__, str(item)))
                while True:
                    has_item = False
                    for each in self.schedule_by_task(item, message['h-mode'], save):
                        yield each
                        has_item = True
                    if not has_item:
                        self.debug("%s schedule task end" % (self.__class__.__name__))
                        break
                if item['uuid'] > save['tid']:
                    save['tid'] = item['uuid']
        elif mode == ROUTER_MODE_SITE:
            if not 'tid' in save:
                save['tid'] = 0
            for item in self.db['TaskDB'].get_new_list(save['tid'], where={"sid": message['item']}):
                self.debug("%s schedule task: %s" % (self.__class__.__name__, str(item)))
                while True:
                    has_item = False
                    for each in self.schedule_by_task(item, message['h-mode'], save):
                        yield each
                        has_item = True
                    if not has_item:
                        self.debug("%s schedule task end" % (self.__class__.__name__))
                        break
                if item['uuid'] > save['tid']:
                    save['tid'] = item['uuid']
        elif mode == ROUTER_MODE_TASK:
            task = self.db['TaskDB'].get_detail(message['item'])
            for each in self.schedule_by_task(task, message['h-mode'], save):
                yield each

    def schedule_by_task(self, task, mode, save):
        """
        获取站点下计划中的爬虫任务
        :param site 站点信息
        :param mode handler mode
        :param save 上下文参数
        :return 包含爬虫任务uuid, url的字典迭代器
        """
        rules = {}
        for item in self.db['SpiderTaskDB'].get_plan_list(mode, save['id'], plantime=save['now'], where={"tid": task['uuid']}, select=['uuid', 'url', 'kid']):
            if not self.testing_mode:
                '''
                testing_mode打开时，数据不入库
                '''
                ruleId = item.pop('kid', 0)
                if str(ruleId) in rules:
                    rule = rules[str(ruleId)]
                else:
                    rule = self.db['AttachmentDB'].get_detail(ruleId)
                    rules[str(ruleId)] = rule
                if not rule:
                    continue
                plantime = int(save['now']) + int(self.ratemap[str(rule.get('frequency', self.DEFAULT_RATE))][0])
                self.db['SpiderTaskDB'].update(item['uuid'], mode, {"plantime": plantime})
            yield item
            if item['uuid'] > save['id']:
                save['id'] = item['uuid']

    def run_parse(self, rule):
        """
        根据解析规则解析源码，获取相应数据
        :param rule 解析规则
        :input self.response 爬虫结果 {"last_source": 最后一次抓取到的源码, "final_url": 最后一次请求的url}
        :output self.response {"parsed": 解析结果}
        """
        def build_rule(item):
            key = item.pop('key')
            if key and item['filter']:
                return {key: item}
            return None
        r = {}
        for item in rule:
            _r = build_rule(item)
            if _r:
                r.update(_r)
        parser = CustomParser(source=self.response['last_source'], ruleset=r, log_level=self.log_level, url=self.response['final_url'])
        self.response['parsed'] = parser.parse()

    def run_result(self, save):
        """
        爬虫结果处理
        :param save 保存的上下文信息
        :input self.response {"parsed": 解析结果, "final_url": 请求的url}
        """
        self.crawl_info['crawl_urls'][str(self.page)] = self.response['final_url']
        self.crawl_info['crawl_count']['page'] += 1
        if self.response['parsed']:
            rid = self.task.get('parentid', None)
            result = copy.deepcopy(self.response['parsed'])
            attach_data = self.db['AttachDataDB'].get_detail(rid)
            if attach_data:
                if not "crawlinfo" in attach_data or not attach_data['crawlinfo']:
                    #爬虫信息记录
                    result['crawlinfo'] = {
                        'pid': self.task['pid'],                        # project id
                        'sid': self.task['sid'],                        # site id
                        'tid': self.task['tid'],                        # task id
                        'uid': self.task['uid'],                        # url id
                        'ruleId': self.task['kid'],                     # interactionNumRule id
                        'final_url': self.response['final_url'],        # 请求url
                    }
                elif not "ruleId" in attach_data['crawlinfo'] or not attach_data['crawlinfo']['ruleId']:
                    crawlinfo = attach_data['attach_data']
                    crawlinfo['ruleId'] = self.task['uid']
                    result['crawlinfo'] = crawlinfo
                result['utime'] = int(time.time())
                result['mediaType'] = self.task.get('mediaType', MEDIA_TYPE_OTHER)
                self.debug("%s result: %s" % (self.__class__.__name__, result))
                if not self.testing_mode:
                    '''
                    testing_mode打开时，数据不入库
                    '''
                    self.db['AttachDataDB'].update(rid, result)
                self.crawl_info['crawl_count']['repeat_count'] += 1
            else:
                #爬虫信息记录
                result['crawlinfo'] = {
                    'pid': self.task['pid'],                        # project id
                    'sid': self.task['sid'],                        # site id
                    'tid': self.task['tid'],                        # task id
                    'uid': self.task['uid'],                        # url id
                    'ruleId': self.task['kid'],                     # interactionNumRule id
                    'list_url': self.response['final_url'],         # 列表url
                }
                result['ctime'] = self.crawl_id
                result['acid'] = self.task['acid']
                result['utime'] = 0
                result['rid'] = rid
                self.debug("%s result: %s" % (self.__class__.__name__, result))
                if not self.testing_mode:
                    '''
                    testing_mode打开时，数据不入库
                    '''
                    self.db['AttachDataDB'].insert(result)

                self.crawl_info['crawl_count']['new_count'] += 1

    def finish(self, save):
        """
        记录抓取日志
        """
        super(InteractHandler, self).finish(save)
        crawlinfo = self.task.get('crawlinfo', {}) or {}
        self.crawl_info['crawl_end'] = int(time.time())
        crawlinfo[str(self.crawl_id)] = self.crawl_info
        crawlinfo_sorted = [(k, crawlinfo[k]) for k in sorted(crawlinfo.keys())]
        if len(crawlinfo_sorted) > self.CRAWL_INFO_LIMIT_COUNT:
            del crawlinfo_sorted[0]
        s = self.task.get("save")
        if not s:
            s = {}
        s.update(save)
        self.db['SpiderTaskDB'].update(self.task['uuid'], self.task['mode'], {"crawltime": self.crawl_id, "crawlinfo": dict(crawlinfo_sorted), "save": s})
