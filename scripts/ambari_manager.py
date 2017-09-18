#!/usr/bin/env python

'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import sys
import urllib2
import json
import base64
import optparse

HTTP_PROTOCOL = 'http'
HTTPS_PROTOCOL = 'https'

CLUSTERS_URL = '/api/v1/clusters/{0}'
SERVICE_URL = '/services/{0}'
COMPONENT_URL = '/services/{0}/components/{1}'
HOST_COMPONENT_URL = '/hosts/{0}/host_components/{1}'
STACK_CONFIG_DEFAULTS_URL = '/api/v1/stacks/{0}/versions/{1}/services/{2}/configurations?fields=StackConfigurations/type,StackConfigurations/property_value'
CREATE_CONFIGURATIONS_URL = '/configurations'

def api_accessor(host, username, password, protocol, port):
  def do_request(api_url, request_type, request_body=''):
    try:
      url = '{0}://{1}:{2}{3}'.format(protocol, host, port, api_url)
      print 'Execute {0} {1}'.format(request_type, url)
      if request_body:
        print 'Request body: {0}'.format(request_body)
      admin_auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
      request = urllib2.Request(url)
      request.add_header('Authorization', 'Basic %s' % admin_auth)
      request.add_header('X-Requested-By', 'ambari')
      request.add_data(request_body)
      request.get_method = lambda: request_type
      response = urllib2.urlopen(request)
      response_body = response.read()
    except Exception as exc:
      raise Exception('Problem with accessing api. Reason: {0}'.format(exc))
    return response_body
  return do_request

if __name__=="__main__":
  parser = optparse.OptionParser("usage: %prog [options]")
  parser.add_option("-a", "--action", dest="action", type="string", help="configure | install | start | stop | remove")
  parser.add_option("-C", "--component", dest="component", type="string", help="component name")
  parser.add_option("-S", "--service", dest="service", type="string", help="service name")
  parser.add_option("-H", "--host", dest="host", default="localhost", type="string", help="hostname for ambari server")
  parser.add_option("-P", "--port", dest="port", default=8080, type="int", help="port number for ambari server")
  parser.add_option("-c", "--cluster", dest="cluster", type="string", help="cluster name")
  parser.add_option("-s", "--ssl", dest="ssl", action="store_true", help="use if ambari server using https")
  parser.add_option("-u", "--username", dest="username", default="admin", type="string", help="username for accessing ambari server")
  parser.add_option("-p", "--password", dest="password", default="admin", type="string", help="password for accessing ambari server")
  (options, args) = parser.parse_args()

  protocol = 'https' if options.ssl else 'http'

  accessor = api_accessor(options.host, options.username, options.password, protocol, options.port)

  print 'Inputs: ' + str(options)

