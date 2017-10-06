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
import logging
import logging.handlers

class AuditLogger:
  logger = None

  @staticmethod
  def initialize_logger(type, name = 'RangerAuditTest', logging_level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s'):

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)

    handler = logging.handlers.RotatingFileHandler('ranger_audits_' + type + '.log', maxBytes = 268435456, backupCount = 5)
    handler.setLevel(logging_level)

    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    AuditLogger.logger = logger

  @staticmethod
  def info(msg):
    AuditLogger.logger.info(msg)

  @staticmethod
  def error(msg):
    AuditLogger.logger.error(msg)

  @staticmethod
  def warning(msg):
    AuditLogger.logger.warning(msg)

  @staticmethod
  def debug(msg):
    AuditLogger.logger.debug(msg)

  @staticmethod
  def critical(msg):
    AuditLogger.logger.critical(msg)