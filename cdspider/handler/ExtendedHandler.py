#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019-1-14 9:57:13
"""
import copy
import time
from . import BaseHandler
from cdspider.database.base import *
from cdspider.libs.constants import *
from cdspider.libs import utils
from cdspider.parser import CustomParser
from cdspider.parser.lib import TimeParser

class ExtendedHandler(BaseHandler):
    """
    extended handler
    :property task 爬虫任务信息 {"mode": "extend", "uuid": SpiderTask.extend uuid}
                   当测试该handler，数据应为 {"mode": "comment", "url": url, "extendRule": 评论规则，参考评论规则}
    """

    def get_scripts(self):
        """
        获取自定义脚本
        """
        try:
            if "uuid" in self.task and self.task['uuid']:
                task = self.db['SpiderTaskDB'].get_detail(self.task['uuid'], self.task['mode'])
                if not task:
                    raise CDSpiderDBDataNotFound("SpiderTask: %s not exists" % self.task['uuid'])
                self.task.update(task)
            rule = self.match_rule() or {}
            return rule.get("scripts", None)
        except:
            return None

    def init_process(self, save):
        """
        初始化爬虫流程
        :output self.process {"request": 请求设置, "parse": 解析规则, "paging": 分页规则, "unique": 唯一索引规则}
        """
        if "extendRule" in self.task:
            self.task['parent_url'] = self.task['url']
            self.task['acid'] = "testing_mode"
            typeinfo = utils.typeinfo(self.task['parent_url'])
            if typeinfo['domain'] != self.task['extendRule']['domain'] or typeinfo['subdomain'] != self.task['extendRule']['subdomain']:
                raise CDSpiderNotUrlMatched()
            crawler = self.get_crawler(self.task.get('extendRule', {}).get('request'))
            crawler.crawl(url=self.task['parent_url'])
            data = utils.get_attach_data(CustomParser, crawler.page_source, self.task['parent_url'], self.task['extendRule'], self.log_level)
            if data == False:
                return None
            url, params = utils.build_attach_url(data, self.task['extendRule'], self.task['parent_url'])
            del crawler
            if not url:
                raise CDSpiderNotUrlMatched()
            self.task['url'] = url
            save['base_url'] = url
            save["hard_code"] = params
            self.task['extendRule']['request']['hard_code'] = params
        else:
            mediaType = self.task.get('mediaType', MEDIA_TYPE_OTHER)
            if mediaType == MEDIA_TYPE_WEIBO:
                article = self.db['WeiboInfoDB'].get_detail(self.task.get('parentid', '0'), select=['url', 'acid'])
            else:
                article = self.db['ArticlesDB'].get_detail(self.task.get('parentid', '0'), select=['url', 'acid'])
            if not article:
                raise CDSpiderHandlerError("aritcle: %s not exists" % self.task['parentid'])
            self.task['parent_url'] = article['url']
            self.task['acid'] = article['acid']
        self.process = self.match_rule()  or {"unique": {"data": None}}
        if not 'data' in self.process['unique'] or not self.process['unique']['data']:
            self.process['unique']['data'] = ','. join(self.process['parse']['item'].keys())
        save['paging'] = True

    def match_rule(self):
        """
        获取匹配的规则
        """
        parse_rule = self.task.get("extendRule", {})
        if not parse_rule:
            '''
            如果task中包含列表规则，则读取相应的规则，否则在数据库中查询
            '''
            ruleId = self.task.get('rid', 0)
            parse_rule = self.db['ExtendRuleDB'].get_detail(ruleId)
            if not parse_rule:
                raise CDSpiderDBDataNotFound("ExtendRule: %s not exists" % ruleId)
            if parse_rule['status'] != ExtendRuleDB.STATUS_ACTIVE:
                raise CDSpiderHandlerError("comment rule not active")
        return parse_rule

    def route(self, mode, save):
        """
        schedule 分发
        :param mode  project|site 分发模����: 按项目|按站点
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
        for item in self.db['SpiderTaskDB'].get_plan_list(mode, save['id'], plantime=save['now'], where={"tid": task['uuid']}, select=['uuid', 'url', 'rid']):
            if not self.testing_mode:
                '''
                testing_mode打开时，数据不入库
                '''
                ruleId = item.get('rid', 0)
                if str(ruleId) in rules:
                    rule = rules[str(ruleId)]
                else:
                    rule = self.db['ExtendRuleDB'].get_detail(ruleId)
                    if rule:
                        rules[str(ruleId)] = rule
                if not rule:
                    continue
                frequency = str(rule.get('frequency', self.DEFAULT_RATE))
                plantime = int(save['now']) + int(self.ratemap[frequency][0])
                self.db['SpiderTaskDB'].update(item['uuid'], mode, {"plantime": plantime, "frequency": frequency})
            if item['uuid'] > save['id']:
                save['id'] = item['uuid']
            yield item

    def run_parse(self, rule):
        """
        根据解析规则解析源码，获取相应数据
        :param rule 解析规则
        :input self.response 爬虫结果 {"last_source": 最后一次抓取到的源码, "final_url": 最后一次请求的url}
        :output self.response {"parsed": 解析结果}
        """
        parser = CustomParser(source=self.response['last_source'], ruleset=copy.deepcopy(rule), log_level=self.log_level, url=self.response['final_url'])
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
            result = copy.deepcopy(self.response['parsed'])
            self.debug("%s result: %s" % (self.__class__.__name__, result))
            if not self.testing_mode:
                '''
                testing_mode打开时，数据不入库
                '''
                result['utime'] = self.crawl_id
                mediaType = self.task.get('mediaType', MEDIA_TYPE_OTHER)
                if mediaType == MEDIA_TYPE_WEIBO:
                    self.db['WeiboInfoDB'].update(self.task.get('parentid', '0'), result)
                else:
                    self.db['ArticlesDB'].update(self.task.get('parentid', '0'), result)
                self.crawl_info['crawl_count']['new_count'] += 1

    def finish(self, save):
        """
        记录抓取日志
        """
        super(ExtendedHandler, self).finish(save)
        if 'uuid' in self.task and self.task['uuid']:
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