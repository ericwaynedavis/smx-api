#!/usr/bin/env python3.8
import argparse
import json
import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

create_operations = ['create-profiles', 'create-subs-onts', 'create-services']
delete_operations = ['delete-services', 'delete-subs-onts', 'delete-profiles']

parser = argparse.ArgumentParser()
parser.add_argument("conf", help="the json config file containing the SMx connection details and provisioning details.")
parser.add_argument("operation", help="the name of the operation to perform: create-all, delete-all, or one of the following: {0}".format(create_operations + delete_operations))
args = parser.parse_args()

try:
    with open(args.conf, mode="r") as j_object:
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
    
def do_operation(operation):    
    for item in operation:
        try:
            with open(item['config-file'], mode="r") as j_object:
               config = json.load(j_object)
        except FileNotFoundError as fnf_error:
           print("Missing config file {0}".format(fnf_error))
           sys.exit(1)
         
        #print(config)
        
        ## This code was intended to allow one to embed variables
        ## into the path elements surrounded by % symbols. The variable
        ## name should be a key in the json config file that resolves to 
        ## a value that becomes part of the path. I decided not to add
        ## variables to the config file and so this code never gets used.
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
        for payload in config:
            ## TODO if the operation is a delete operation, will need additional logic here to
            ## extract the key/value pairs from the payload and build up the path statement.
            ## Delete operations do not have a json payload in the HTML body. All the attributes
            ## for the delete POST are passed as part of the URL.
            req = requests.Request(method=item['method'], url=URL+path, json=payload, auth=AUTH)
            prepared = req.prepare()
            pretty_print_POST(prepared)
            r = s.send(prepared)
            try:
                json_resp = r.json()
            except json.decoder.JSONDecodeError:
                json_resp = "None"
            print("Request result: {0}\nResponse headers: {1}\nJSON Response: {2}\n".format(r.status_code, r.headers, json_resp ))
            #PP.pprint(r.json())
        
s = requests.Session()
s.verify=SSL
s.auth=AUTH

if args.operation == 'create-all':
    for item in create_operations:
        do_operation(CONFIG[item])
elif args.operation == 'delete-all':
    for item in delete_operations:
        do_operation(CONFIG[item])
else:
    do_operation(CONFIG[args.operation])    
