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

import urllib2, ssl
import json
import base64
import optparse
import ConfigParser

HTTP_PROTOCOL = 'http'
HTTPS_PROTOCOL = 'https'

CLUSTERS_URL = '/api/v1/clusters/{0}'
SERVICE_URL = '/services/{0}'
COMPONENT_URL = '/services/{0}/components/{1}'
HOST_COMPONENT_URL = '/hosts/{0}/host_components/{1}'
GET_HOST_COMPONENTS_URL = '/services/{0}/components/{1}?fields=host_components'
STACK_CONFIG_DEFAULTS_URL = '/api/v1/stacks/{0}/versions/{1}/services/{2}/configurations?fields=StackConfigurations/type,StackConfigurations/property_value'
CREATE_CONFIGURATIONS_URL = '/configurations'

GET_ALL_HOST_COMPONENTS_URL = '/host_components'

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
      response = None
      if protocol == 'https':
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib2.urlopen(request, context=ctx)
      else:
        response = urllib2.urlopen(request)
      response_body = response.read()
    except Exception as exc:
      raise Exception('Problem with accessing api. Reason: {0}'.format(exc))
    return response_body
  return do_request

def get_json(accessor, url):
  response = accessor(url, 'GET')
  json_resp = json.loads(response)
  return json_resp

def apply_configs(options, accessor, configs):
  for config in configs:
    configs[config].pop("properties", None)
    post_configs = {}
    post_configs[config] = configs[config]
    desired_configs_post_body = {}
    desired_configs_post_body["Clusters"] = {}
    desired_configs_post_body["Clusters"]["desired_configs"] = post_configs
    accessor(CLUSTERS_URL.format(options.cluster), 'PUT', json.dumps(desired_configs_post_body))

def create_configs(options, accessor, merged_properties, tag):
  configs_for_posts = {}
  for config_type in merged_properties:
    config = {}
    config['type'] = config_type
    config['tag'] = tag
    config['properties'] = merged_properties[config_type]
    configs_for_posts[config_type] = config
    accessor(CLUSTERS_URL.format(options.cluster) + CREATE_CONFIGURATIONS_URL, 'POST', json.dumps(config))
  return configs_for_posts

def generate_component_hosts_ini(options, accessor):
  component_hosts_result={}
  supported_components = options.component_list.split(',')
  hosts_components_response = get_json(accessor, CLUSTERS_URL.format(options.cluster) + GET_ALL_HOST_COMPONENTS_URL)
  if 'items' in hosts_components_response and len(hosts_components_response['items']) > 0:
    for host_role_data in hosts_components_response['items']:
      host_roles = host_role_data['HostRoles']
      component_name = host_roles['component_name']
      if component_name in supported_components:
        host_name = host_roles['host_name']
        if component_name not in component_hosts_result:
          component_hosts_result[component_name]=[]
        if host_name not in component_hosts_result[component_name]:
          component_hosts_result[component_name].append(host_name)

  config = ConfigParser.RawConfigParser()
  for component in component_hosts_result:
    config.add_section(component)
    config.set(component, 'hosts', ",".join(component_hosts_result[component]))

  with open(options.ini_file, 'w') as f:
    config.write(f)


def get_stack_default_properties(stack_default_properties_json):
  stack_default_properties = {}
  if 'items' in stack_default_properties_json and len(stack_default_properties_json['items']) > 0:
    for stack_properties in stack_default_properties_json['items']:
      if 'StackConfigurations' in stack_properties:
        first_stack_props = stack_properties['StackConfigurations']
        config_type = first_stack_props['type'].replace('.xml','')
        if config_type not in stack_default_properties:
          stack_default_properties[config_type] = {}

        stack_default_properties[config_type][first_stack_props['property_name']] = first_stack_props['property_value']

  return stack_default_properties

def create_host_components(options, accessor, components_hosts, component_name):
  for component_host in components_hosts:
    accessor(CLUSTERS_URL.format(options.cluster) + HOST_COMPONENT_URL.format(component_host, component_name), 'POST')

def get_component_hosts(component_host_object_list):
  host_names = []
  if "host_components" in component_host_object_list and len(component_host_object_list['host_components']) > 0:
    for host_component in component_host_object_list['host_components']:
      if 'HostRoles' in host_component:
        host_names.append(host_component['HostRoles']['host_name'])
  return host_names

def merge_properties(properties, stack_default_properties):
  new_properties = {}
  print 'Processing new properties...'
  for new_properties_config_type in stack_default_properties:
    if new_properties_config_type in properties:
      for old_config in properties[new_properties_config_type]:
        if old_config in stack_default_properties[new_properties_config_type] \
          and stack_default_properties[new_properties_config_type][old_config] != \
            properties[new_properties_config_type][old_config]:
          print 'Override {0}/{1} property from the backup.'.format(new_properties_config_type, old_config)
          stack_default_properties[new_properties_config_type][old_config] = properties[new_properties_config_type][old_config]
    new_properties[new_properties_config_type] = stack_default_properties[new_properties_config_type]
  return new_properties

def start_service(options, accessor, parser):
  '''
    Start service
    '''

  start_body = '{"RequestInfo": {"context" :"Start ' + options.service + '"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}'
  accessor(CLUSTERS_URL.format(options.cluster) + SERVICE_URL.format(options.service), 'PUT', start_body)

def stop_service(options, accessor, parser):
  '''
  Stop service
  '''

  stop_body = '{"RequestInfo": {"context" :"Stop ' + options.service + '"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'
  accessor(CLUSTERS_URL.format(options.cluster) + SERVICE_URL.format(options.service), 'PUT', stop_body)

def install_service(options, accessor, parser):
  '''
    Install service
    '''
  install_body = '{"RequestInfo": {"context" :"Install ' + options.service + '"}, "Body": {"ServiceInfo": {"state": "INSTALLED"}}}'
  accessor(CLUSTERS_URL.format(options.cluster) + SERVICE_URL.format(options.service), 'PUT', install_body)

def remove_service(options, accessor, parser):
  '''
    Remove Solr service
    '''

  accessor(CLUSTERS_URL.format(options.cluster) + SERVICE_URL.format(options.service), 'DELETE')

def configure(options, accessor, parser):
  '''
  Configure service - put next to another components or provide the host list
  '''
  accessor(CLUSTERS_URL.format(options.cluster) + SERVICE_URL.format(options.service), 'POST')
  accessor(CLUSTERS_URL.format(options.cluster) + COMPONENT_URL.format(options.service, options.component), 'POST')
  stack_default_properties = get_stack_default_properties(get_json(accessor, STACK_CONFIG_DEFAULTS_URL.format(options.stack_name, options.stack_version, options.service)))
  hosts = None
  if options.hosts_list:
    hosts = options.hosts_list.split(",")
  else:
    hosts = get_component_hosts(get_json(accessor, CLUSTERS_URL.format(options.cluster) + GET_HOST_COMPONENTS_URL.format(options.next_to_service, options.next_to_component)))
  configs = create_configs(options, accessor, stack_default_properties, "tag123456")
  apply_configs(options, accessor, configs)
  create_host_components(options, accessor, hosts, options.component)


if __name__=="__main__":
  parser = optparse.OptionParser("usage: %prog [options]")
  parser.add_option("--action", dest="action", type="string", help="configure | install  | start | stop | remove")
  parser.add_option("--component", dest="component", type="string", help="component name")
  parser.add_option("--service", dest="service", type="string", help="service name")
  parser.add_option("--next-to-component", dest="next_to_component", type="string", help="install component where this component installed")
  parser.add_option("--next-to-service", dest="next_to_service", type="string", help="install component where this service installed")
  parser.add_option("--host", dest="host", default="localhost", type="string", help="hostname for ambari server")
  parser.add_option("--hosts-list", dest="hosts_list", type="string", help="comma separated hosts (to install components)")
  parser.add_option("--port", dest="port", default=8080, type="int", help="port number for ambari server")
  parser.add_option("--cluster", dest="cluster", type="string", help="cluster name")
  parser.add_option("--protocol", dest="protocol", default=HTTP_PROTOCOL, help="ambari protocol (http | https)")
  parser.add_option("--username", dest="username", default="admin", type="string", help="username for accessing ambari server")
  parser.add_option("--password", dest="password", default="admin", type="string", help="password for accessing ambari server")
  parser.add_option("--extra-configs", dest="extra_config", type="string", help="configurations to apply with stack defaults")
  parser.add_option("--stack-name", dest="stack_name", default="HDP", type="string", help="name of the stack")
  parser.add_option("--stack-version", dest="stack_version", default="2.6", type="string", help="version of the stack")
  parser.add_option("--ini-file", dest="ini_file", default="ambari_components.ini", type="string", help="Filename of the generated ini file for host components (default: ambari_components.ini)")
  parser.add_option("--component-list", dest="component_list", default="INFRA_SOLR,RANGER_ADMIN,ATLAS_SERVER,LOGSEARCH_SERVER", type="string", help="comma separated components")
  (options, args) = parser.parse_args()

  accessor = api_accessor(options.host, options.username, options.password, options.protocol, options.port)

  print 'Inputs: ' + str(options)

  if options.action == 'configure':
    configure(options, accessor, parser)
  elif options.action == 'install':
    install_service(options, accessor, parser)
  elif options.action == 'start':
    start_service(options, accessor, parser)
  elif options.action == 'stop':
    stop_service(options, accessor, parser)
  elif options.action == 'remove':
    remove_service(options, accessor, parser)
  elif options.action == 'generate-component-hosts':
    generate_component_hosts_ini(options, accessor)
  else:
    parser.print_help()
    print 'action option is wrong or missing'


