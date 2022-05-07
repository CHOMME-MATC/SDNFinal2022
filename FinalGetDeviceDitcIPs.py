# Cole Ringenberg 5/7/2022
'''
The goal of this scrip is to make api calls to network devices, pull interface information, create dictionaries containing interface names and
IP addresses for said network devices.
'''

import sys
import requests
import json
import re

# List of mgmt IP's for devices
deviceIP = ['10.10.20.175', '10.10.20.176', '10.10.20.177', '10.10.20.178']

# makes restconf call to the IOS-XE routers and get itetf-ipv4 interface information
def getIOSXE_IP(deviceIP):

    url = "https://"+ deviceIP +":443/restconf/data/ietf-interfaces:interfaces"

    username = 'cisco'
    password = 'cisco'
    payload={}
    headers = {
      'Content-Type': 'application/yang-data+json',
      'Accept': 'application/yang-data+json',
      'Authorization': 'Basic cm9vdDpEX1ZheSFfMTAm'
    }

    response = requests.request("GET", url, auth = (username,password), verify = False, headers=headers, data=payload)

    intDict = response.json()['ietf-interfaces:interfaces']['interface']

    return intDict

# parces out the returned data from the devices and creates a dictionary with interface names as the key and IP as the value 
def createIntDict(interfaces):

    devDict = {}

    for interface in interfaces:
        if interface['name'] != 'Loopback0':
            devDict.update({f"{interface['name']}" : f"{interface['ietf-ip:ipv4']['address'][0]['ip']}"})
    
    return devDict

# condenses the code to only need to pass a management address of a router to run the all the funcitons
def getRouterIPs(IP):

    # accepts the management IP of a IOS-XE device and returns a response dictionary
    response = getIOSXE_IP(IP)

    # iterates through the response and return a dictionary of IP's where the key is the interface name and the value is the IP
    # note that you can set the variable to be the name of the device you are iterating the response from
    devDict = createIntDict(response)

    return devDict

# api request that runs a show ip interface brief and returns the response dicitonary
def nexos9000(command, IP): 

    switchuser='cisco'
    switchpassword='cisco'

    url='https://' + IP + '/ins'
    myheaders={'content-type':'application/json-rpc'}
    payload=[
      {
        "jsonrpc": "2.0",
        "method": "cli",
        "params": {
          "cmd": command,
          "version": 1
        },
        "id": 1
      }
    ]

    response = requests.post(url,data=json.dumps(payload),verify=False,headers=myheaders,auth=(switchuser,switchpassword)).json()

    return response

# Iterates the response dictionary and creates a dictionary that has the interface name for the key and the IP as the value
def iterateSwitchDict(switchDict):

    devDict = {}

    parsedSwitchDict = switchDict['result']['body']['TABLE_intf']['ROW_intf']

    for interface in parsedSwitchDict:
        
        devDict.update({f"{interface['intf-name']}" : f"{interface['prefix']}"})

    return devDict

# Condenses the code to allow for easy iteration
def getSwitchIPs(IP):

    # accept the mgmt IP and sends a show ip interface brief command to the switch and returns a response dicitonary
    switchIPDict = nexos9000("show ip interface brief", IP)

    # parces out the response dictionary and creates a dictionary containing the int name as the key and the IP as the value
    Switch = iterateSwitchDict(switchIPDict)

    return Switch

'''
Note for the person doing the previous step in the project you can iterate your code through the getRouterIPs or getSwitchIPs

Example:

for mgmtIP in mgmtIPDictionary:
    router = getRouterIPs(mgmtIP)
    print(router)

Just make sure you are using the proper function for the correct type of device (Router or Switch)
'''
# runs a function that has nested functions inside of it that runs the portion of the script that get a dictionary of interface IP for the routers    
Router1 = getRouterIPs(deviceIP[0])
Router2 = getRouterIPs(deviceIP[1])

print(Router1)
print(Router2)

# runs a function that has nested functions inside of it that runs the portion of the script that get a dictionary of interface IP for the switches  
Switch1 = getSwitchIPs(deviceIP[2])
Switch2 = getSwitchIPs(deviceIP[3])

print(Switch1)
print(Switch2)
