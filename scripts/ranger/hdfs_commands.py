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

  system_requests = SystemRequests()
  machine_config = Config()

  user_list = machine_config.get('hdfs', 'user_list', 'ambari-qa,hive')
  user_list = user_list.split(",")

  while datetime.datetime.now() < end_time:

    thread_list = []
    for i in range(0, options.no_of_threads):
      for j in range(0, len(user_list)):
        t = threading.Thread(target=execute, args=(system_requests, machine_config, user_list[j], options.no_of_execution,))
        thread_list.append(t)

    for thread in thread_list:
      thread.start()

    for thread in thread_list:
      thread.join()

def execute(system_requests, machine_config, user, no_of_execution):
  for i in range(0, no_of_execution):
    security_enabled = machine_config.get('cluster', 'security', False)
    user = machine_config.get(user, 'user', user)
    principal = machine_config.get(user, 'principal', None)
    keytab = machine_config.get(user, 'keytab', None)

    random_numbers = random.randint(100000000000,999999999999)
    sleep_time = machine_config.get('hdfs', 'sleep_time', '10')

    kinit_command = ""
    if security_enabled == 'True':
      kinit_command = "/usr/bin/kinit -kt {0} {1};".format(keytab, principal)

    hdfs_ls_command = "{0} hdfs dfs -ls /tmp".format(kinit_command)
    code, stdout = system_requests.execute_command(hdfs_ls_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("HDFS COMMAND RESULT FOR LIST FILES : " + str(stdout))

    hdfs_mkdir_command = "{0} hdfs dfs -mkdir -p /tmp/test_dir_{1}".format(kinit_command, random_numbers)
    code, stdout = system_requests.execute_command(hdfs_mkdir_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("HDFS COMMAND RESULT FOR MAKE DIRECTORY : " + str(stdout))

    hdfs_ls_dir_command = "{0} hdfs dfs -ls /tmp/test_dir_{1}".format(kinit_command, random_numbers)
    code, stdout = system_requests.execute_command(hdfs_ls_dir_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("HDFS COMMAND RESULT FOR LIST DIRECTORY /tmp/test_dir_" + str(random_numbers) + " : " + str(stdout))

    hdfs_remove_command = "{0} hdfs dfs -rmr /tmp/test_dir_{1}".format(kinit_command, random_numbers)
    code, stdout = system_requests.execute_command(hdfs_remove_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("HDFS COMMAND RESULT FOR DELETE DIRECTORY /tmp/test_dir_" + str(random_numbers) + " : " + str(stdout))

if __name__ == '__main__':
  main()