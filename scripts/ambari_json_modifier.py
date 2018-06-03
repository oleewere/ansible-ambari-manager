#!/usr/bin/env python

import json
import optparse

def update_json(options):
  input_data = None
  with open(options.input) as f:
    input_data = json.load(f)
  update_data = None
  with open(options.update_input) as f:
    update_data = json.load(f)
  service_config_map = {}
  with open(options.service_config_map_input) as f:
    service_config_map = json.load(f)

  service_filter = options.service_filter.split(",") if options.service_filter else []

  config_type_supported = False
  for service in service_config_map:
    if service in service_filter and options.config_type in service_config_map[service]:
      config_type_supported = True

  update_props = {}
  if config_type_supported:
    update_props = update_data[options.config_type]
    props = input_data['properties']
    for prop in props:
      if prop in update_props:
        props[prop] = update_props[prop]

    for new_update_prop in update_props:
      if new_update_prop not in props:
        props[new_update_prop] = update_props[new_update_prop]

    new_input_data = {}
    new_input_data['properties'] = props
    with open(options.output, 'w') as outfile:
      json.dump(new_input_data, outfile)
  else:
    print "Config types are filtered out (checkout service filter)"


if __name__=="__main__":
  parser = optparse.OptionParser("usage: %prog [options]")
  parser.add_option("--input", dest="input", type="string", help="input json")
  parser.add_option("--update-input", dest="update_input", type="string", help="inputs with updated proeprties")
  parser.add_option("--config-type", dest="config_type", type="string", help="config type")
  parser.add_option("--output", dest="output", type="string", help="merged json output")
  parser.add_option("--service-filter", dest="service_filter", type="string", help="comma separated services to filter configs")
  parser.add_option("--service-config-map-input", dest="service_config_map_input", type="string", help="file that contains service - config type mapping ")

  (options, args) = parser.parse_args()

  update_json(options)
