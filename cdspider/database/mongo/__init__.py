# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.
#version: SVN: $Id: __init__.py 1388 2018-06-22 01:39:47Z zhangyi $

from .Mongo import Mongo as Base
from .Articlesdb import ArticlesDB
from .CrawlLogdb import CrawlLogDB
from .Keywordsdb import KeywordsDB
from .MediaTypesdb import MediaTypesDB
from .Projectsdb import ProjectsDB
from .Sitesdb import SitesDB
from .Taskdb import TaskDB
from .Uniquedb import UniqueDB
from .Urlsdb import UrlsDB
from .SpiderTaskdb import SpiderTaskDB
from .ListRuledb import ListRuleDB
from .ParseRuledb import ParseRuleDB
from .ErrorLogdb import ErrorLogDB
