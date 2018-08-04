# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import copy
import tempfile
import logging

from cdspider.libs.goose3.text import StopWords
from cdspider.libs.goose3.parsers import Parser, ParserSoup
from cdspider.libs.goose3.version import __version__

AVAILABLE_PARSERS = {
    'lxml': Parser,
    'soup': ParserSoup,
}

KNOWN_ARTICLE_CONTENT_PATTERNS = [
    {'attr': 'class', 'value': 'short-story'},
    {'attr': 'itemprop', 'value': 'articleBody'},
    {'attr': 'class', 'value': 'post-content'},
    {'attr': 'class', 'value': 'g-content'},
    {'tag': 'article'},
]
KNOWN_ARTICLE_CONTENT_PATTERNS_BY_DOMAIN = {
    'qq.com': [
        {'attr': 'class', 'value': 'content-article'},
    ],
    'sina.com.cn': [
        {'attr': 'id', 'value': 'article'},
    ],
    'ifeng.com': [
        {'attr': 'id', 'value': 'yc_con_txt'},
    ],
    '163.com': [
        {'attr': 'class', 'value': 'post_text'},
    ]
}


class Configuration(object):

    def __init__(self):
        # logger
        self._logger = logging.getLogger('goose')

        # parser information
        self._available_parsers = list(AVAILABLE_PARSERS.keys())
        self._parser_class = 'lxml'

        # URL extraction parameters
        self._browser_user_agent = 'Goose/%s' % __version__
        self._http_timeout = 30.0
        self._http_auth = None
        self._http_proxies = None
        self._http_headers = None
        self._final_url = None

        # extraction information
        self._local_storage_path = os.path.join(tempfile.gettempdir(), 'goose')
        self._known_context_patterns = KNOWN_ARTICLE_CONTENT_PATTERNS
        self._target_language = 'en'
        self._use_meta_language = True

        # general configuration
        self._strict = True
        self._debug = False
        self._stopwords_class = StopWords
        self._enable_fewwords_paragraphs = False

        # imagemagick executable paths
        self._imagemagick_convert_path = "/opt/local/bin/convert"  # Not used
        self._imagemagick_identify_path = "/opt/local/bin/identify"  # not used

        # image extraction
        self._enable_image_fetching = False
        self._images_min_bytes = 4500
        # Do we need to allow setting one's own ImageExtractor class?

        self._domain = None
        self._subdomain = None

        self._custom_rule = {}

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, val):
        self._domain = val

    @property
    def subdomain(self):
        return self._subdomain

    @subdomain.setter
    def subdomain(self, val):
        self._subdomain = val

    @property
    def custom_rule(self):
        return self._custom_rule

    @custom_rule.setter
    def custom_rule(self, val):
        self._custom_rule = val

    @property
    def final_url(self):
        return self._final_url

    @final_url.setter
    def final_url(self, val):
        self._final_url = val

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, val):
        self._logger = val

    @property
    def known_context_patterns(self):
        ''' list: The context patterns to search to find the likely article content

            Note:
                Each entry must be a dictionary with the following keys: `attr` and `value` \
                or just `tag`
        '''
        known_context_patterns = []
        fulldomain = "%s.%s" % (self.subdomain, self.domain)
        if fulldomain in KNOWN_ARTICLE_CONTENT_PATTERNS_BY_DOMAIN:
            known_context_patterns.extend(KNOWN_ARTICLE_CONTENT_PATTERNS_BY_DOMAIN[fulldomain])
        if self.domain in KNOWN_ARTICLE_CONTENT_PATTERNS_BY_DOMAIN:
            known_context_patterns.extend(KNOWN_ARTICLE_CONTENT_PATTERNS_BY_DOMAIN[self.domain])
        known_context_patterns.extend(self._known_context_patterns)
        return known_context_patterns

    @known_context_patterns.setter
    def known_context_patterns(self, val):
        ''' val must be a dictionary or list of dictionaries
            e.g., {'attr': 'class', 'value': 'my-article-class'}
                or [{'attr': 'class', 'value': 'my-article-class'},
                    {'attr': 'id', 'value': 'my-article-id'}]
        '''
        if isinstance(val, list):
            self._known_context_patterns = val + self.known_context_patterns
        else:
            self._known_context_patterns.insert(0, val)

    @property
    def strict(self):
        ''' bool: Enable `strict mode` and throw exceptions instead of
            swallowing them.

            Note:
                Defaults to `True` '''
        return self._strict

    @strict.setter
    def strict(self, val):
        ''' set the strict property '''
        self._strict = bool(val)

    @property
    def http_timeout(self):
        ''' float: The time delay to pass to `requests` to wait for the response
            in seconds

            Note:
                Defaults to 30.0 '''
        return self._http_timeout

    @http_timeout.setter
    def http_timeout(self, val):
        ''' set the http_timeout property '''
        self._http_timeout = float(val)

    @property
    def local_storage_path(self):
        ''' str: The local path to store temporary files

            Note:
                Defaults to the value of `os.path.join(tempfile.gettempdir(), 'goose')` '''
        return self._local_storage_path

    @local_storage_path.setter
    def local_storage_path(self, val):
        ''' set the local_storage_path property '''
        if val:
            self._local_storage_path = val

    @property
    def debug(self):
        ''' bool: Turn on or off debugging

            Note:
                Defaults to `False`
            Warning:
                Debugging is currently not implemented '''
        return self._debug

    @debug.setter
    def debug(self, val):
        ''' set the debug property '''
        self._debug = bool(val)

    @property
    def parser_class(self):
        ''' str: The key of the parser to use

            Note:
                Defaults to `lxml` '''
        return self._parser_class

    @parser_class.setter
    def parser_class(self, val):
        ''' set the parser_class property '''
        self._parser_class = val

    @property
    def available_parsers(self):
        ''' list(str): A list of all possible parser values for the parser_class

            Note:
                Not settable '''
        return self._available_parsers

    @property
    def http_auth(self):
        ''' tuple: Authentication class and information to pass to the requests
            library

            See Also:
                `Requests Authentication <http://docs.python-requests.org/en/master/user/authentication/>`__
        '''
        return self._http_auth

    @http_auth.setter
    def http_auth(self, val):
        ''' set the http_auth property '''
        self._http_auth = val

    @property
    def http_proxies(self):
        ''' dict: Proxy information to pass directly to the supporting `requests` object

            See Also:
                `Requests Proxy Support <http://docs.python-requests.org/en/master/user/advanced/#proxies>`__
        '''
        return self._http_proxies

    @http_proxies.setter
    def http_proxies(self, val):
        ''' set the http_proxies property '''
        self._http_proxies = val

    @property
    def http_headers(self):
        ''' dict: Custom headers to pass directly to the supporting `requests` object

            See Also:
                `Requests Custom Headers <http://docs.python-requests.org/en/master/user/quickstart/#custom-headers>`__
        '''
        return self._http_headers

    @http_headers.setter
    def http_headers(self, val):
        ''' set the http_headers property '''
        self._http_headers = val

    @property
    def browser_user_agent(self):
        ''' Browser user agent string to use when making URL requests

            Note:
                Defaults to `Goose/{goose3.__version__}`

            Examples:
                Using the non-standard browser agent string is advised when pulling
                frequently

                >>> config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2)'
                >>> config.browser_user_agent = 'AppleWebKit/534.52.7 (KHTML, like Gecko)'
                >>> config.browser_user_agent = 'Version/5.1.2 Safari/534.52.7'
        '''
        return self._browser_user_agent

    @browser_user_agent.setter
    def browser_user_agent(self, val):
        ''' set the browser user agent string '''
        self._browser_user_agent = val

    @property
    def imagemagick_identify_path(self):
        ''' str: Path to the identify program that is part of imagemagick

            Note:
                Defaults to `"/opt/local/bin/identify"`
            Warning:
                Currently not used / implemented '''
        return self._imagemagick_identify_path

    @imagemagick_identify_path.setter
    def imagemagick_identify_path(self, val):
        ''' set the imagemagick identify program path '''
        self._imagemagick_identify_path = val

    @property
    def imagemagick_convert_path(self):
        ''' str: Path to the convert program that is part of imagemagick

            Note:
                Defaults to `"/opt/local/bin/convert"`
            Warning:
                Currently not used / implemented '''
        return self._imagemagick_convert_path

    @imagemagick_convert_path.setter
    def imagemagick_convert_path(self, val):
        ''' set the imagemagick convert program path '''
        self._imagemagick_convert_path = val

    @property
    def stopwords_class(self):
        ''' StopWords: The StopWords class to use when analyzing article content

            Note:
                Defaults to the english stop words
            Note:
                Current stop words available in `goose3.text` include: \n
                `StopWords`, `StopWordsChinese`, `StopWordsArabic`, and `StopWordsKorean`
        '''
        return self._stopwords_class

    @property
    def enable_fewwords_paragraphs(self):
        return self._enable_fewwords_paragraphs

    @enable_fewwords_paragraphs.setter
    def enable_fewwords_paragraphs(self, val):
        self._enable_fewwords_paragraphs = val

    @stopwords_class.setter
    def stopwords_class(self, val):
        ''' set the stopwords class to use '''
        # TODO: add a check to see if a valid class is provided!
        self._stopwords_class = val

    @property
    def target_language(self):
        ''' str: The default target language if the language is not extractable
            or if use_meta_language is set to False

            Note:
                Default language is 'en'
        '''
        return self._target_language

    @target_language.setter
    def target_language(self, val):
        ''' set the target language property '''
        self._target_language = val

    @property
    def use_meta_language(self):
        ''' bool: Determine if language should be extracted from the meta tags
            or not. If this is set to `False` then the target_language will be
            used. Also, if extraction fails then the target_language will be
            utilized.

            Note:
                Defaults to `True` '''
        return self._use_meta_language

    @use_meta_language.setter
    def use_meta_language(self, val):
        ''' set the use_meta_language property '''
        self._use_meta_language = bool(val)

    @property
    def enable_image_fetching(self):
        ''' bool: Turn on or off image extraction

            Note:
                Defaults to `True` '''
        return self._enable_image_fetching

    @enable_image_fetching.setter
    def enable_image_fetching(self, val):
        ''' set the enable_image_fetching property '''
        self._enable_image_fetching = bool(val)

    @property
    def images_min_bytes(self):
        ''' int: Minimum number of bytes for an image to be evaluated to be the
            main image of the site

            Note:
                Defaults to 4500 bytes '''
        return self._images_min_bytes

    @images_min_bytes.setter
    def images_min_bytes(self, val):
        ''' set the images_min_bytes property '''
        self._images_min_bytes = int(val)

    def get_parser(self):
        ''' Retrieve the current parser class to use for extraction

            Returns:
                Parser: The parser to use '''
        return AVAILABLE_PARSERS[self.parser_class]
