#!/usr/bin/env python3.8
import argparse
import json
import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument("cf", help="cf the config file containing the SMx connection details and provisioning details.")
args = parser.parse_args()

try:
    with open(args.cf, mode="r") as j_object:
       CONFIG = json.load(j_object)
except FileNotFoundError as fnf_error:
   logging.critical("Missing config file {0}".format(fnf_error))
   sys.exit(1)
   
URL=CONFIG['url']
AUTH=(CONFIG['user'], CONFIG['pass'])
SSL=(True if CONFIG['use_ssl'] == 'True' else False)

def pretty_print_POST(req):

    print('{}\n{}\r\n{}\r\nRequest Body: {}\r\n'.format(
        '-----------HTTP REQUEST-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body
    ))

s = requests.Session()
s.verify=SSL
s.auth=AUTH

for item in CONFIG['configs']:
    try:
        with open(item['config-file'], mode="r") as j_object:
           config = json.load(j_object)
    except FileNotFoundError as fnf_error:
       print("Missing config file {0}".format(fnf_error))
       sys.exit(1)
    
    m = re.search('%(.+?)%', item['path']) 
    if m:
        print("m: {0}".format(m))
        element_list = m.group(1).split('.')
        print(m.group(1))
        print(element_list)
        element = CONFIG.get(element_list[0])
        if len(element_list) > 1:
            for i in range(1, len(element_list)):
                element = element.get(element_list[i])
        path = re.sub('%'+m.group(1)+'%', element, item['path'])
    else:
        path = item['path']
    req = requests.Request(method=item['method'], url=URL+path, json=config, auth=AUTH)
    prepared = req.prepare()
    pretty_print_POST(prepared)
    r = s.send(prepared)
    try:
        json_resp = r.json()
    except json.decoder.JSONDecodeError:
        json_resp = "None"
    print("Request result: {0}\nResponse headers: {1}\nJSON Response: {2}\n".format(r.status_code, r.headers, json_resp ))
    #PP.pprint(r.json())
    
    
