"""
Exashare.com urlresolver XBMC Addon
Copyright (C) 2014 JUL1EN094 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import urlparse,re
from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin

class ExashareResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "exashare"
    domains = [ "exashare.com" ]
    
    def __init__(self):
        p=self.get_setting('priority') or 100
        self.priority=int(p)
        self.net=Net()

    def get_media_url(self, host, media_id):

        web_url = self.get_url('exashare.com', media_id)

        html = self.net.http_GET(web_url).content

        try: r = re.search('src="([^"]+)', html).group(1)
        except: return

        web_url = urlparse.urlparse(r).netloc
        web_url = self.get_url(web_url, media_id)

        referer = '%s://%s/' % (urlparse.urlparse(r).scheme, urlparse.urlparse(r).netloc)

        headers = { 'Referer': referer }

        html = self.net.http_GET(web_url, headers=headers).content

        stream_url = re.search('file\s*:\s*"(http.+?)"', html)

        if stream_url:
            return stream_url.group(1)
        else:
            raise UrlResolver.ResolverError('Unable to locate link')

    def get_url(self,host,media_id):
        return 'http://%s/embed-%s.html' % (host,media_id)

    def get_host_and_id(self,url):
        r=re.search('//(?:www.)?(exashare.com)/(?:embed-)?([0-9a-zA-Z]+)',url)
        if r: return r.groups()
        else: return False

    def valid_url(self, url, host):
        return re.match('http://(www.)?exashare.com/(embed-)?[A-Za-z0-9]+', url) or "exashare.com" in host
