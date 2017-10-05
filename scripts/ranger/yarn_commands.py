#/usr/bin/env python

import datetime
import os
import random
import threading
import time
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

  user_list = machine_config.get('yarn', 'user_list', 'ambari-qa,yarn')
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
    yarn_jar = machine_config.get('yarn', 'yarn_jar', '/usr/hdp/current/hadoop-mapreduce-client/hadoop-mapreduce-examples.jar')
    queue_name = machine_config.get('yarn', 'queue_name', 'default')

    user = machine_config.get(user, 'user', user)
    principal = machine_config.get(user, 'principal', None)
    keytab = machine_config.get(user, 'keytab', None)

    sleep_time = machine_config.get('yarn', 'sleep_time', '3')

    kinit_command = ""
    if security_enabled == 'True':
      kinit_command = "/usr/bin/kinit -kt {0} {1};".format(keytab, principal)

    yarn_command = "{0} yarn jar {1} pi -Dmapred.job.queue.name={2} 2 2".format(kinit_command, yarn_jar, queue_name)
    code, stdout = system_requests.execute_command(yarn_command, user)
    AuditLogger.info("YARN COMMAND RESULT FOR USER - "+ str(user) + " : " + str(stdout))
    time.sleep(int(sleep_time))

if __name__ == '__main__':
  main()