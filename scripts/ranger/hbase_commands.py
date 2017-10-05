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

  user_list = machine_config.get('hbase', 'user_list', 'hbase,ambari-qa,hdfs')
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
    hbase_cmd = machine_config.get('hbase', 'hbase_cmd', '/usr/hdp/current/hbase-client/bin/hbase')

    user = machine_config.get(user, 'user', user)
    principal = machine_config.get(user, 'principal', None)
    keytab = machine_config.get(user, 'keytab', None)

    random_numbers = random.randint(100000000000,999999999999)
    sleep_time = machine_config.get('hbase', 'sleep_time', '10')

    kinit_command = ""
    if security_enabled == 'True':
      kinit_command = "/usr/bin/kinit -kt {0} {1};".format(keytab, principal)

    hbase_create_command = "create 'test_table_{0}', 'col1', 'col2'".format(random_numbers)
    hbase_disable_command = "disable 'test_table_{0}'".format(random_numbers)
    hbase_drop_command = "drop 'test_table_{0}'".format(random_numbers)

    temp_file_path = "/tmp/test_tmp_{0}".format(random_numbers)
    temp_file = open(temp_file_path, 'w')
    temp_file.write(hbase_create_command + "\n" + hbase_disable_command + "\n" + hbase_drop_command + "\nexit\n")
    temp_file.close()

    hbase_command = "{0} {1} shell {2}".format(kinit_command, hbase_cmd, temp_file_path)
    code, stdout = system_requests.execute_command(hbase_command, user)
    AuditLogger.info("HBASE COMMAND RESULT : " + str(stdout))
    time.sleep(int(sleep_time))
    os.remove(temp_file_path)

if __name__ == '__main__':
  main()