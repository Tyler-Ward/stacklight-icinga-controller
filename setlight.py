#!/usr/bin/env python

import requests
import json
import time
import os

icinga_address = os.environ.get("ICINGA_ADDRESS","localhost")
icinga_port = os.environ.get("ICINGA_PORT","5665")
icinga_api_user = os.environ.get("ICINGA_API_USER")
icinga_api_password = os.environ.get("ICINGA_API_PASSWORD")
stacklight_address = os.environ.get("STACKLIGHT_ADDRESS")

if stacklight_address is None:
    print("STACKLIGHT_ADDRESS environment variable must be set")
    exit()

if icinga_api_user is None:
    print("ICINGA_API_USER environment variable must be set")
    exit()

if icinga_api_password is None:
    print("ICINGA_API_PASSWORD environment variable must be set")
    exit()

request_url = "https://{}:{}/v1/objects/services".format(icinga_address, icinga_port)
headers = {
        'Accept': 'application/json',
        'X-HTTP-Method-Override': 'GET'
        }
requestdata = {
        "attrs": [ "name", "state", "state_type", "last_hard_state", "acknowledgement", "downtime_depth"],
        "joins": [ "host.name", "host.state"],
}

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

while True:
    r = requests.post(request_url,
            headers=headers,
            auth=(icinga_api_user, icinga_api_password),
            data=json.dumps(requestdata),
            verify=False)

    states={}

    if (r.status_code == 200):
        data = r.json()
        for service in data["results"]:
            if service["attrs"]["acknowledgement"] == 0 and service["attrs"]["downtime_depth"] == 0:
                states[int(service["attrs"]["last_hard_state"])] = states.get(int(service["attrs"]["last_hard_state"]),0)+1

        colour="off"
        if states.get(2,0)>=1:
            colour="red"
        elif states.get(1,0)>=1:
            colour="yellow"
        else:
            colour="off"

        print("setting to {}".format(colour))
        r = requests.post(
            "http://{}/set".format(stacklight_address),
            data="mode={}".format(colour),
            verify=False)

        time.sleep(5)
