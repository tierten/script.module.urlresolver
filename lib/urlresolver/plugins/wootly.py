"""
    Copyright (C) 2017 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import re
import urllib
import os
import random
from lib import helpers
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class WootlyResolver(UrlResolver):
    name = "wootly"
    domains = ["www.wootly.ch"]
    pattern = '(?://|\.)(wootly\.ch)/\?v=([0-9a-zA-Z]+)'

    profile_path = common.profile_path
    cookie_file = os.path.join(profile_path, '%s.cookies' % name)

    def __init__(self):
        self.net = common.Net(cookie_file=self.cookie_file)
        self.headers = {'User-Agent': common.RAND_UA}

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        html = self.net.http_GET(web_url, headers=self.headers).content

        data = self.__get_hidden(html)
        data = self.__apply_disabled(html, data)
        data.update({'x': random.randint(0, 100), 'y': random.randint(0, 100)})
            
        self.headers.update({'Referer': web_url})
        html = self.net.http_POST(web_url, form_data=data, headers=self.headers).content
        sources = helpers.scrape_sources(html)
        source = helpers.pick_source(sources)
        self.headers.update({'Cookie': self._get_stream_cookies(self.net.get_cookies(as_dict=True))})
        return source + helpers.append_headers(self.headers)

    def _get_stream_cookies(self, cookies):
        cookies = ['%s=%s' % (key, value) for key, value in cookies.items()]
        return urllib.quote('; '.join(cookies))

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='http://www.wootly.ch/?v={media_id}')

    def __apply_disabled(self, html, data):
        dis_by_var = {}
        var_names = {}
        for match in re.finditer('([A-Za-z0-9_]+)=document\.getElementById\("([^"]+)', html):
            var_names[match.group(1)] = match.group(2)
        
        for match in re.finditer('([A-Za-z0-9_]+)\.disabled=(true|false)', html):
            dis_by_var[match.group(1)] = match.group(2)
        
        dis_by_id = dict((var_names[key], value) for key, value in dis_by_var.iteritems())
        for key, value in data.items():
            if dis_by_id.get(key) == 'true':
                del data[key]
            elif dis_by_id.get(key) == 'false':
                pass
            elif value['disabled'] == 'disabled':
                del data[key]

        data = dict((value['name'], value['value']) for key, value in data.items())
        return data
    
    def __get_hidden(self, html, form_id=None, index=None, include_submit=True):
        hidden = {}
        if form_id:
            pattern = '''<form [^>]*(?:id|name)\s*=\s*['"]?%s['"]?[^>]*>(.*?)</form>''' % (form_id)
        else:
            pattern = '''<form[^>]*>(.*?)</form>'''
        
        html = helpers.cleanse_html(html)
            
        for i, form in enumerate(re.finditer(pattern, html, re.DOTALL | re.I)):
            if index is None or i == index:
                for field in re.finditer('''<input [^>]*type=['"]?hidden['"]?[^>]*>''', form.group(1)):
                    match = re.search('''name\s*=\s*['"]([^'"]+)''', field.group(0))
                    match1 = re.search('''value\s*=\s*['"]([^'"]*)''', field.group(0))
                    match2 = re.search('''disabled\s*=\s*['"]([^'"]+)''', field.group(0))
                    match3 = re.search('''id\s*=\s*['"]([^'"])''', field.group(0))
                    if match and match1:
                        disabled = match2.group(1) if match2 else None
                        key = match3.group(1) if match3 else match.group(1)
                        hidden[key] = {'name': match.group(1), 'value': match1.group(1), 'disabled': disabled}
                
                if include_submit:
                    match = re.search('''<input [^>]*type=['"]?submit['"]?[^>]*>''', form.group(1))
                    if match:
                        name = re.search('''name\s*=\s*['"]([^'"]+)''', match.group(0))
                        value = re.search('''value\s*=\s*['"]([^'"]*)''', match.group(0))
                        disabled = re.search('''disabled\s*=\s*['"]([^'"]+)''', match.group(0))
                        html_id = re.search('''id\s*=\s*['"]([^'"])''', field.group(0))
                        if name and value:
                            disabled = match2.group(1) if match2 else None
                            key = html_id.group(1) if match3 else name.group(1)
                            hidden[key] = {'name': name.group(1), 'value': value.group(1), 'disabled': disabled}
                
        common.log_utils.log_debug('Hidden fields are: %s' % (hidden))
        return hidden

