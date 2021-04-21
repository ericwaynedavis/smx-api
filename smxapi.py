#!/usr/bin/env python3.8
import argparse
import json
import requests
import urllib3
import re
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
s = requests.Session()

def pretty_print_POST(req):
    print('{}\n{}\r\n{}\r\nRequest Body: {}\r\n'.format(
        '-----------HTTP REQUEST-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body
    ))
 
def do_http_request(method, url, payload, auth):
    req = requests.Request(method=method, url=url, json=payload, auth=auth)
    prepared = req.prepare()
    pretty_print_POST(prepared)
    r = s.send(prepared)
    try:
        json_resp = r.json()
    except json.decoder.JSONDecodeError:
        json_resp = "None"
    print("Request result: {0}\nResponse headers: {1}\nJSON Response: {2}\n".format(r.status_code, r.headers, json_resp ))
    return json_resp

def get_json_conf(cf):
    try:
        with open(cf, mode="r") as j_object:
           return json.load(j_object)
    except FileNotFoundError as fnf_error:
       print("Config file {0} not found".format(fnf_error))
       sys.exit(1)

def create_profiles(item):
    for payload in get_json_conf(item['config-file']):
        do_http_request(method=item['method'], url=BASE_URL+item['path'], payload=payload, auth=s.auth)

def delete_profiles(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(name = payload['name'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)

def create_templates(item):
    for payload in get_json_conf(item['config-file']):
        do_http_request(method=item['method'], url=BASE_URL+item['path'], payload=payload, auth=s.auth)

def delete_templates(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(name = payload['template-name'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)
        
def create_vlans(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(deviceName = payload['device-name'])
        do_http_request(method=item['method'], url=url, payload=payload, auth=s.auth)

def delete_vlans(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(vlanId=payload['vlan-id'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)
        
def create_subscribers(item):
    for payload in get_json_conf(item['config-file']):
        do_http_request(method=item['method'], url=BASE_URL+item['path'], payload=payload, auth=s.auth)
    
def delete_subscribers(item):
    print(item)
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(orgId=payload['orgId'], customId=payload['customId'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)
        
def create_onts(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(deviceName=payload['device-name'])
        do_http_request(method=item['method'], url=url, payload=payload, auth=s.auth)
        
def delete_onts(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(deviceName=payload['device-name'], ontId=payload['ont-id'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)
    
def create_services(item):
    for payload in get_json_conf(item['config-file']):
        do_http_request(method=item['method'], url=BASE_URL+item['path'], payload=payload, auth=s.auth)
        
def delete_services(item):
    ## For some reason, SMx always returns a 500 error message but the services are deleted anyway.
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(deviceName=payload['device-name'], ontId=payload['ont-id'], portId=payload['ont-port-id'], serviceName=payload['service-name'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)

def synchronize_profiles(item):
    for payload in get_json_conf(item['config-file']):
        url = BASE_URL+item['path'].format(name = payload['name'])
        do_http_request(method=item['method'], url=url, payload={}, auth=s.auth)
        
def do_operation(operation):
    if operation in CONFIG:
        for item in CONFIG[operation]:
            function = OPERATIONS.get(operation, lambda: "Invalid operation: {0}".format(operation))
            function(item)
    else:
        print("Invalid operation: {0}".format(operation))

OPERATIONS = { 'create-profiles':       create_profiles,
                            'synchronize-profiles': synchronize_profiles,
                            'create-templates':   create_templates,
                            'create-vlans':           create_vlans, 
                            'create-subscribers': create_subscribers, 
                            'create-onts':             create_onts, 
                            'create-services':      create_services,
                            'delete-services':      delete_services, 
                            'delete-onts':             delete_onts, 
                            'delete-subscribers':  delete_subscribers,
                            'delete-vlans':            delete_vlans, 
                            'delete-templates':   delete_templates,
                            'delete-profiles':        delete_profiles}

parser = argparse.ArgumentParser()
parser.add_argument("conf", help="the json config file containing the SMx connection details and provisioning details.")
parser.add_argument("operation", help="the name of the operation to perform: create-all, delete-all, or one of the following (note the order of operations): {0}".format(OPERATIONS.keys()))
args = parser.parse_args()

try:
    with open(args.conf, mode="r") as j_object:
       CONFIG = json.load(j_object)
except FileNotFoundError as fnf_error:
   logging.critical("Missing config file {0}".format(fnf_error))
   sys.exit(1)
   
BASE_URL=CONFIG['url']
s.verify=(True if CONFIG['use_ssl'] == 'True' else False)
s.auth=(CONFIG['user'], CONFIG['pass'])

try:
    if args.operation == 'create-all' or args.operation == 'delete-all'  :
        for operation in OPERATIONS.keys():
            if args.operation == 'create-all' and ('create' in operation or 'synchronize' in operation):
                do_operation(operation)
            elif args.operation == 'delete-all' and 'delete' in operation:
                do_operation(operation)
    else:
        do_operation(args.operation)    
except KeyError as k:
            print("Missing expected key {0}".format(k))
            traceback.print_exc()