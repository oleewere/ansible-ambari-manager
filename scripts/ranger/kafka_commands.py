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

  user = machine_config.get('kafka', 'user', 'kafka')

  while datetime.datetime.now() < end_time:

    thread_list = []
    for i in range(0, options.no_of_threads):
      for j in range(0, 2):
        t = threading.Thread(target=execute, args=(system_requests, machine_config, user, options.no_of_execution,))
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
    kafka_home = machine_config.get('kafka', 'kafka_home', '/usr/hdp/current/kafka-broker')
    zookeeper_quorum = machine_config.get('zookeeper', 'zookeeper_quorum', 'localhost:2181')
    kafka_create_topic = "{0}/bin/kafka-topics.sh --create --zookeeper {1} --replication-factor 1 --partitions 1 --topic".format(kafka_home, zookeeper_quorum)
    kafka_list_topic = "{0}/bin/kafka-topics.sh --list --zookeeper {1}".format(kafka_home, zookeeper_quorum)
    kafka_delete_topic = "{0}/bin/kafka-topics.sh --delete --zookeeper {1} --topic".format(kafka_home, zookeeper_quorum)

    random_numbers = random.randint(100000000000,999999999999)
    sleep_time = machine_config.get('kafka', 'sleep_time', '10')

    kinit_command = ""
    if security_enabled == 'True':
      kinit_command = "/usr/bin/kinit -kt {0} {1};".format(keytab, principal)

    kafka_create_command = '{0} {1} test_topic_{2}'.format(kinit_command, kafka_create_topic, random_numbers)
    code, stdout = system_requests.execute_command(kafka_create_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("KAFKA COMMAND RESULT FOR CREATE TOPIC test_topic_" + str(random_numbers) + " : " + str(stdout))

    kafka_list_command = '{0} {1}'.format(kinit_command, kafka_list_topic)
    code, stdout = system_requests.execute_command(kafka_list_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("KAFKA COMMAND RESULT FOR LIST TOPIC test_topic_" + str(random_numbers) + " : " + str(stdout))

    kafka_delete_command = '{0} {1} test_topic_{2}'.format(kinit_command, kafka_delete_topic, random_numbers)
    code, stdout = system_requests.execute_command(kafka_delete_command, user)
    time.sleep(int(sleep_time))
    AuditLogger.info("KAFKA COMMAND RESULT FOR DELETE TOPIC test_topic_" + str(random_numbers) + " : " + str(stdout))

if __name__ == '__main__':
  main()