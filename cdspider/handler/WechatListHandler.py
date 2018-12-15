#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-12-13 20:37:03
"""
import copy
import time
import traceback
import html
from . import BaseHandler, Loader
from urllib.parse import urljoin, unquote_plus
from cdspider.database.base import *
from cdspider.libs import utils
from cdspider.libs.constants import *
from cdspider.parser import ListParser, CustomParser
from cdspider.parser.lib import TimeParser

class WechatListHandler(BaseHandler):
    """
    wechat list handler
    :property task 爬虫任务信息 {"mode": "wechat-list", "uuid": SpiderTask.author uuid}
                   当测试该handler，数据应为 {"mode": "wechat-list", "wxauthorRule": 公众号搜索解析, "author": 自媒体号设置，参考自媒体号, "authorListRule": 自媒体列表规则，参考自媒体列表规则}
    """

    EXPIRE = 7200

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
            '''
            初始化上下文中的id参数,该参数用于数据查询
            '''
            save["id"] = 0
        if mode == ROUTER_MODE_PROJECT:
            '''
            按项目分发
            '''
            for item in self.db['ProjectsDB'].get_new_list(save['id'], select=["uuid"]):
                if item['uuid'] > save['id']:
                    save['id'] = item["uuid"]
                yield item['uuid']
        elif mode == ROUTER_MODE_SITE:
            '''
            按站点分发
            '''
            if not "pid" in save:
                '''
                初始化上下文中的pid参数,该参数用于项目数据查询
                '''
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
                    for each in self.db['TaskDB'].get_new_list(save['id'], where={"pid": item['uuid'], "type": {"$in": [TASK_TYPE_AUTHOR]}, "mediaType": MEDIA_TYPE_WEWCHAT}, select=["uuid"]):
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
            '''
            初始化上下文中的id参数,该参数用于数据查询
            '''
            save['id'] = 0
        if mode == ROUTER_MODE_PROJECT:
            '''
            按项目分发的计划任务
            '''
            if not 'tid' in save:
                '''
                初始化上下文中的tid参数,该参数用于站点数据查询
                '''
                save['tid'] = 0
            for item in self.db['TaskDB'].get_new_list(save['tid'], where={"pid": message['item'], "type": {"$in": [TASK_TYPE_AUTHOR]}, "mediaType": MEDIA_TYPE_WEWCHAT}):
                self.debug("%s schedule task: %s" % (self.__class__.__name__, str(item)))
                while True:
                    has_item = False
                    #以站点为单位获取计划中的爬虫任务
                    for each in self.schedule_by_task(item, message['h-mode'], save):
                        yield each
                        has_item = True
                    if not has_item:
                        self.debug("%s schedule task end" % (self.__class__.__name__))
                        break
                if item['uuid'] > save['tid']:
                    save['tid'] = item['uuid']
        elif mode == ROUTER_MODE_SITE:
            '''
            按站点分发的计划任务
            '''
            if not 'tid' in save:
                '''
                初始化上下文中的tid参数,该参数用于站点数据查询
                '''
                save['tid'] = 0
            for item in self.db['TaskDB'].get_new_list(save['tid'], where={"pid": message['item'], "type": {"$in": [TASK_TYPE_AUTHOR]}, "mediaType": MEDIA_TYPE_WEWCHAT}):
                self.debug("%s schedule task: %s" % (self.__class__.__name__, str(item)))
                #获取该站点计划中的爬虫任务
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
            '''
            按站点分发的计划任务
            '''
            task = self.db['TaskDB'].get_detail(message['item'])
            #获取该站点计划中的爬虫任务
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
        for item in self.db['SpiderTaskDB'].get_plan_list(mode, save['id'], plantime=save['now'], where={"tid": task['uuid']}, select=['uuid', 'url']):
            if not self.testing_mode:
                '''
                testing_mode打开时，数据不入库
                '''
                author = self.db['WechatDB'].get_detail(item['uid'])
                if not author:
                    self.db['SpiderTaskDB'].delete(item['uuid'], mode)
                plantime = int(save['now']) + int(self.ratemap[str(author.get('frequency', self.DEFAULT_RATE))][0])
                self.db['SpiderTaskDB'].update(item['uuid'], mode, {"plantime": plantime})
            if item['uuid'] > save['id']:
                save['id'] = item['uuid']
            yield item

    def newtask(self, message):
        """
        新建爬虫任务
        :param message [{"uid": url uuid, "mode": handler mode}]
        """
        uid = message['uid']
        if not isinstance(uid, (list, tuple)):
            uid = [uid]
        for each in uid:
            spiderTasks = self.db['SpiderTaskDB'].get_list(message['mode'], {"uid": each})
            if len(list(spiderTasks)) > 0:
                continue
            author = self.db['WechatDB'].get_detail(each)
            if not author:
                raise CDSpiderDBDataNotFound("wechat: %s not found" % each)
            task = {
                'mode': message['mode'],     # handler mode
                'pid': author['pid'],        # project uuid
                'sid': author['sid'],        # site uuid
                'tid': author['tid'],        # task uuid
                'uid': each,                 # url uuid
                'kid': 0,                    # keyword id
                'url': "base_url",           # url
                'status': self.db['SpiderTaskDB'].STATUS_ACTIVE,
            }
            self.debug("%s newtask: %s" % (self.__class__.__name__, str(task)))
            if not self.testing_mode:
                '''
                testing_mode打开时，数据不入库
                '''
                self.db['SpiderTaskDB'].insert(task)

    def get_scripts(self):
        """
        获取列表规则中的自定义脚本
        :return 自定义脚本
        """
        save = {}
        try:
            if "uuid" in self.task and self.task['uuid']:
                task = self.db['SpiderTaskDB'].get_detail(self.task['uuid'], self.task['mode'])
                if not task:
                    raise CDSpiderDBDataNotFound("SpiderTask: %s not exists" % self.task['uuid'])
                self.task.update(task)
            rule = self.match_rule(save) or {}
            return rule.get("scripts", None)
        except:
            return None

    def init_process(self, save):
        """
        初始化爬虫流程
        :output self.process {"request": 请求设置, "parse": 解析规则, "paging": 分页规则, "unique": 唯一索引规则}
        """
        rule = self.match_rule(save)
        self.process = rule

    def match_rule(self, save):
        """
        获取匹配的规则
        """
        if "authorListRule" in self.task:
            '''
            如果task中包含列表规则，则读取相应的规则，否则在数据库中查询
            '''
            wechatRule = copy.deepcopy(self.task['wxauthorRule'])
            if not wechatRule:
                raise CDSpiderDBDataNotFound("wechat rule not exists")
            rule = copy.deepcopy(self.task['authorListRule'])
            author = copy.deepcopy(self.task['author'])
            if not author:
                raise CDSpiderError("author not exists")
        else:
            author = self.db['WechatDB'].get_detail(self.task['uid'])
            if not author:
                self.db['SpiderTaskDB'].delete(self.task['uuid'], self.task['mode'])
                raise CDSpiderDBDataNotFound("author: %s not exists" % self.task['uid'])
            if author['status'] != WechatDB.STATUS_ACTIVE:
                self.db['SpiderTaskDB'].disable(self.task['uuid'], self.task['mode'])
                raise CDSpiderHandlerError("url not active")
            wechatRule = self.db['WechatRuleDB'].get_detail_by_tid(author['tid'])
            if not wechatRule:
                self.db['SpiderTaskDB'].disable(self.task['uuid'], self.task['mode'])
                raise CDSpiderDBDataNotFound("wechat rule by tid: %s not exists" % author['tid'])
            if wechatRule['status'] != WechatRuleDB.STATUS_ACTIVE:
                raise CDSpiderHandlerError("wechat rule: %s not active" % wechatRule['uuid'])
            rule = self.db['AuthorListRuleDB'].get_detail_by_tid(author['tid'])
            if not rule:
                self.db['SpiderTaskDB'].disable(self.task['uuid'], self.task['mode'])
                raise CDSpiderDBDataNotFound("author rule by tid: %s not exists" % author['tid'])
            if rule['status'] != AuthorListRuleDB.STATUS_ACTIVE:
                raise CDSpiderHandlerError("author rule: %s not active" % rule['uuid'])
        account = author.get('account')
        if account:
            save['request'] = {
                "hard_code": [{
                    "mode": "format",
                    "name": "account",
                    "value": account,
                }],
            }
        self.task['prepare_rule'] = wechatRule
        self.task['url'] = wechatRule['baseUrl']
        return rule

    def prepare(self, save):
        super(WechatListHandler, self).prepare(save)
        if not 'save' in self.task or not self.task['save']:
            self.task['save'] = {}
        ctime = self.task['save'].get('timestamp')
        if not self.task['save'].get('base_url') or self.crawl_id - int(ctime) > self.EXPIRE:
            params = copy.deepcopy(self.request_params)
            self.crawler.crawl(**params)
            parser = CustomParser(source=self.crawler.page_source, ruleset=copy.deepcopy(self.task['prepare_rule']['parse']))
            accountInfo = parser.parse()
            if not accountInfo or not accountInfo[0]['url']:
                raise CDSpiderParserNoContent("Wechat account not found")
            print(accountInfo)
            save['base_url'] = html.unescape(accountInfo[0]['url'])
            save['timestamp'] = self.crawl_id
            self.request_params['url'] = html.unescape(accountInfo[0]['url'])
        else:
            self.request_params['url'] = self.task['save'].get('base_url')

    def run_parse(self, rule):
        """
        根据解析规则解析源码，获取相应数据
        :param rule 解析规则
        :input self.response 爬虫结果 {"last_source": 最后一次抓取到的源码, "final_url": 最后一次请求的url}
        :output self.response {"parsed": 解析结果}
        """
        parser = ListParser(source=self.response['last_source'], ruleset=copy.deepcopy(rule), log_level=self.log_level, url=self.response['final_url'])
        self.response['parsed'] = parser.parse()

    def update_crawl_info(self):
        """
        构造文章数据的爬虫信息
        """
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
        self.db['SpiderTaskDB'].update(self.task['uuid'], self.task['mode'], {"crawltime": self.crawl_id, "crawlinfo": dict(crawlinfo_sorted), "save": save})


    def run_result(self, save):
        """
        爬虫结果处理
        :param save 保存的上下文信息
        :input self.response {"parsed": 解析结果, "final_url": 请求的url}
        """
        self.crawl_info['crawl_urls'][str(self.page)] = self.response['last_url']
        self.crawl_info['crawl_count']['page'] += 1
        self.crawl_info['crawl_count']['total'] = len(self.response['parsed'])
        self.update_crawl_info()
        if self.response['parsed']:
            #格式化url
            formated = self.build_url_by_rule(self.response['parsed'], self.response['final_url'])
            item_handler = None
            item_save = {"base_url": task.get('url')}
            for item in formated:
                try:
                    item_task = self.build_item_task(url)
                    if item_handler == None:
                        item_handler = Loader(self.ctx, task = item_task, spider = self.spider, no_sync = self.no_sync).load()
                        item_handler.init(item_save)
                    else:
                        item_handler.run_next(item_task)
                    item_save['retry'] = 0
                    while True:
                        self.info('Item Spider crawl start')
                        item_handler.crawl(item_save)
                        if isinstance(item_handler.response['broken_exc'], CONTINUE_EXCEPTIONS):
                            item_handler.on_continue(item_handler.response['broken_exc'], item_save)
                            continue
                        elif item_handler.response['broken_exc']:
                            raise handler.response['broken_exc']
                        if not item_handler.response['last_source']:
                            raise CDSpiderCrawlerError('Item Spider crawl failed')
                        self.info("Spider crawl end, source: %s" % str(handler.response["last_source"]))
                        self.info("Spider parse start")
                        handler.parse()
                        self.info("Spider parse end, result: %s" % str(handler.response["parsed"]))
                        self.info("Spider result start")
                        handler.on_result(save)
                        self.info("Spider result end")
                except Exception as e:
                    self.on_error(e, save)
            if item_handler:
                item_handler.finish(item_save)

    def url_prepare(self, url):
        return html.unescape(url)

    def build_url_by_rule(self, data, base_url = None):
        """
        根据url规则格式化url
        :param data 解析到的数据
        :param base_url 基本url
        """
        if not base_url:
            base_url = self.task.get('url')
        urlrule = self.process.get("url")
        formated = []
        for item in data:
            if not 'url' in item or not item['url']:
                raise CDSpiderError("url no exists: %s @ %s" % (str(item), str(task)))
            if item['url'].startswith('javascript') or item['url'] == '/':
                continue
            try:
                item['url'] = self.url_prepare(item['url'])
            except:
                self.error(traceback.format_exc())
                continue
            if urlrule and 'name' in urlrule and urlrule['name']:
                parsed = {urlrule['name']: item['url']}
                item['url'] = utils.build_url_by_rule(urlrule, parsed)
            else:
                item['url'] = urljoin(base_url, item['url'])
            formated.append(item)
        return formated


    def build_item_task(self, url):
        """
        生成详情抓取任务并入队
        """
        message = {
            'mode': HANDLER_MODE_WECHAT_ITEM,
            'url': url,
            'crawlid': self.crawl_id,
            'stid': self.task['uuid'],
        }
        return message
#        self.queue['scheduler2spider'].put_nowait(message)