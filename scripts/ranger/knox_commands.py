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

  system_requests = SystemRequests()
  machine_config = Config()

  user_list = machine_config.get('knox', 'user_list', 'sam,tom,admin')
  user_list = user_list.split(",")

  knox_services = ['WEBHDFS', 'WEBHCAT']

  while datetime.datetime.now() < end_time:

    thread_list = []
    for i in range(0, options.no_of_threads):
      for j in range(0, len(user_list)):
        for service in range(0, len(knox_services)):
          t = threading.Thread(target=execute, args=(system_requests, machine_config, user_list[j], knox_services[service], options.no_of_execution,))
          thread_list.append(t)

    for thread in thread_list:
      thread.start()

    for thread in thread_list:
      thread.join()

def execute(system_requests, machine_config, user, service, no_of_execution):
  for i in range(0, no_of_execution):
    user = machine_config.get(user, 'user', user)
    password = machine_config.get(user, 'password', user + '-password')
    knox_host = machine_config.get('knox', 'knox_host', 'localhost')
    knox_port = machine_config.get('knox', 'knox_port', '8443')
    knox_topology = machine_config.get('knox', 'knox_topology', 'default')

    operation = "webhdfs/v1?op=LISTSTATUS"
    if service == "WEBHDFS":
      operation = "{0}/v1?op=LISTSTATUS".format(service.lower())
    if service == "WEBHCAT":
      operation = "templeton/v1/status"

    knox_command = 'curl -i -k -u {0}:{1} -X GET https://{2}:{3}/gateway/{4}/{5}'.format(user, password, knox_host, knox_port, knox_topology, operation)

    code, stdout = system_requests.execute_command(knox_command, 'root')
    AuditLogger.info("KNOX COMMAND RESULT : " + str(stdout))

if __name__ == '__main__':
  main()