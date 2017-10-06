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

import os
import pwd
import subprocess
import sys
from audit_logger import AuditLogger

class SystemRequests:
  def __init__(self, type):
    AuditLogger.initialize_logger(type)
    AuditLogger.info("Initializing Logger for Ranger Audits [" + type + "]")

  def execute_command(self, command, user):
    env = os.environ.copy()

    subprocess_command = ["su", user, "-l", "-s", "/bin/bash", "-c", command]
    AuditLogger.info("RUNNING COMMAND: " + " ".join(subprocess_command))
    proc = subprocess.Popen(subprocess_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, cwd=None, env=env)
    result = proc.communicate()
    proc_stdout = result[0]
    proc_returncode = proc.returncode

    return proc_returncode, proc_stdout