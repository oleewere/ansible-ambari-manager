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

import datetime
import threading
import time
import random
from audit_logger import AuditLogger
from config import Config
from optparse import OptionParser
from system_requests import SystemRequests

def main():

  parser = OptionParser(usage="Usage: %prog [options]")
  parser.add_option("-d", "--days", dest="no_of_days", type="int", help="[REQUIRED] Number of days to run this script")
  parser.add_option("-t", "--threads", dest="no_of_threads", default=1, type="int", help="Number of thread count")
  parser.add_option("-e", "--execution", dest="no_of_execution", default=1000, type="int", help="Number of execution count")
  (options, args) = parser.parse_args()

  if options.no_of_days is None:
    options.no_of_days = int(raw_input('Enter number of days to run this script:'))

  if options.no_of_threads is None:
    options.no_of_threads = int(raw_input('Enter number of of thread count:'))

  if options.no_of_execution is None:
    options.no_of_execution = int(raw_input('Enter number of execution count:'))

  current_time = datetime.datetime.now()
  end_time = current_time + datetime.timedelta(days=options.no_of_days)

  system_requests = SystemRequests('fill')
  machine_config = Config()

  while datetime.datetime.now() < end_time:

    thread_list = []
    for i in range(0, options.no_of_threads):
      t = threading.Thread(target=execute, args=(system_requests, machine_config, options.no_of_execution,))
      thread_list.append(t)

    for thread in thread_list:
      thread.start()

    for thread in thread_list:
      thread.join()

def execute(system_requests, machine_config, no_of_execution):
  user = machine_config.get('ambari-infra', 'user', 'infra-solr')
  security_enabled = machine_config.get('cluster', 'security', False)
  principal = machine_config.get('ambari-infra', 'principal', None)
  keytab = machine_config.get('ambari-infra', 'keytab', None)
  
  solr_server_address = machine_config.get('ambari-infra', 'solr_server_address', None)
  solr_ranger_collection = machine_config.get('ambari-infra', 'solr_ranger_collection', None)
  
  document_number = int(machine_config.get('ambari-infra', 'document_number', '100'))
  ip_address = machine_config.get('host', 'ip_address', None)
  cluster = machine_config.get('cluster', 'cluster_name', None)
  
  sleep_time = int(machine_config.get('ambari-infra', 'sleep_time', '10'))
  
  for i in range(0, no_of_execution):

    curl_prefix = 'curl -k'

    if security_enabled == 'True':
      kinit_command = "/usr/bin/kinit -kt {0} {1}".format(keytab, principal)
      code, stdout = system_requests.execute_command(kinit_command, user)
      AuditLogger.info("KINIT COMMAND RESULT : " + str(stdout))
      curl_prefix = 'curl -k --negotiate -u :'
    
    curl = '{0} -X POST -H \'Content-Type: application/json\''.format(curl_prefix)
    
    url = '{0}/solr/{1}/update'.format(solr_server_address, solr_ranger_collection)
    
    data = '['
    for i in range(0, document_number):
      if i > 0:
        data += ','
      
      random_numbers = random.randint(100000000000,999999999999)
      now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
      data += '{{ "id": "{0}", "access": "WRITE", "enforcer": "ranger-acl", "repo": "{3}_fill", "reqUser": "ambari-qa", "resource": "resource {0}", "cliIP": "{1}", "logType": "RangerAudit", "result": 1, "policy": 2, "repoType": 1, "resType": "path", "reason": "reason {0}", "action": "write", "evtTime": "{2}", "seq_num": 0, "event_count": 1, "event_dur_ms": 0, "cluster": "{3}" }}'.format(random_numbers, ip_address, now, cluster)
    
    data += ']'
    
    curl_command = '{0} \'{1}\' --data-binary \'{2}\''.format(curl, url, data)
    code, stdout = system_requests.execute_command(curl_command, user, 200)
    AuditLogger.info("FILL COMMAND RESULT : " + str(stdout))
    
    time.sleep(sleep_time)

if __name__ == '__main__':
  main()
