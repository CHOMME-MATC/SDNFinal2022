'''

Date: 4/27/22

Authors: Chance Homme, Elija Muller, Cole Ringenberg


This script updates the file of nxos and iosxe devices and creates a mass update for devices changing
the addressing from 172.16 to 172.32 this includes interface addresses, hsrp and ospf instances.


'''
# import statements importing various libraries responsible for parsing xml, netconf function, request, json, and ordered dictionaries

import xml.etree.ElementTree as ET
import xmltodict
import xml.dom.minidom
from lxml import etree
from ncclient import manager
from collections import OrderedDict
import requests 
import json

#getCookie was imported from the turnipTheBeet git repository

def getNXCookie(addr): # function responsible for renewing the authentication cookie for the NXAPI
    

    url = "https://"+ addr + "/api/aaaLogin.json" # url contains the destination for the api call, with addr being the ip address of the
                                                  # device being passed to the function
    
    payload= {"aaaUser" : # the payload contains the username and password to authenticate with the nxos api 
              {"attributes" :
                   {"name" : "cisco",
                    "pwd" : "cisco"}
               }
          }

    response = requests.post(url, json=payload, verify = False) # repsone sends the api call to the location specified in the url variable

    return response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"] # the api response is returned to the program for further use


def createNXVLAN(mgmtIP, vlan, vlanName, authCookie): # function responsible for creating a VLAN on NXAPI devices

    url = 'https://' + mgmtIP + '/api/mo/sys.json' # url contains the destination for the api call, with mgmtIP being the ip address of the
                                                  # device being passed to the function

    payload = { # the payload iterates through the model, passing vlan and vlanName to fabEncap and name attributes respectively 
          "topSystem": {
            "children": [
              {
                "bdEntity": {
                  "children": [
                    {
                      "l2BD": {
                        "attributes": {
                          "fabEncap": vlan,
                          "name": vlanName
                        }
                      }
                    }
                  ]
                }
              }
            ]
          }
        }






    headers ={ # headers specify the type of input sent to the api and the cookie that is being used to authenticate with the device
        'Content-Type': 'text/plain',
        'Cookie': 'APIC-cookie=' + authCookie
        }
    
    response = requests.request("POST", url, headers=headers, verify=False, data=json.dumps(payload)) #  repsone sends the api post call to the location specified in the url variable

    return response # response is returned back to code for further use



def changeNXINTAddress(mgmtIP, intName, newIP, authCookie): # function responsible for changing addressing on NXAPI device interfaces

    url = 'https://' + mgmtIP + '/api/mo/sys.json' # url contains the destination for the api call, with mgmtIP being the ip address of the
                                                  # device being passed to the function


    payload = { # the payload iterates through the model, passing intName and newIP to id and addr attributes respectively 
  "topSystem": {
    "children": [
      {
        "ipv4Entity": {
          "children": [
            {
              "ipv4Inst": {
                "children": [
                  {
                    "ipv4Dom": {
                      "attributes": {
                        "name": "default"
                      },
                      "children": [
                        {
                          "ipv4If": {
                            "attributes": {
                              "id": intName
                            },
                            "children": [
                              {
                                "ipv4Addr": {
                                  "attributes": {
                                    "addr": newIP}}}]}}]}}]}}]}},{
                                        "interfaceEntity": {
                                          "children": [{
                                          "sviIf": {
                                            "attributes": {
                                              "adminSt": "up",
                                                  "id": intName}}}]}}]}}


    headers ={ # headers specify the type of input sent to the api and the cookie that is being used to authenticate with the device
        'Content-Type': 'text/plain',
        'Cookie': 'APIC-cookie=' + authCookie
        }
    
    response = requests.request("POST", url, headers=headers, verify=False, data=json.dumps(payload)) #  repsone sends the api post call to the location specified in the url variable

    return response # response is returned back to code for further use



def createNXSVI(mgmtIP, intName, newIP, authCookie): # function responsible for creating SVI config on NXAPI devices

    url = 'https://' + mgmtIP + '/api/mo/sys.json' # url contains the destination for the api call, with mgmtIP being the ip address of the
                                                  # device being passed to the function


    payload = { # the payload iterates through the model, passing intName and newIP to id and addr attributes respectively 
      "topSystem": {
        "children": [
          {
            "ipv4Entity": {
              "children": [
                {
                  "ipv4Inst": {
                    "children": [
                      {
                        "ipv4Dom": {
                          "attributes": {
                            "name": "default"
                          },
                          "children": [
                            {
                              "ipv4If": {
                                "attributes": {
                                  "id": intName
                                },
                                "children": [
                                  {
                                    "ipv4Addr": {
                                      "attributes": {
                                        "addr": newIP}}}]}}]}}]}}]}},{
                                            "interfaceEntity": {
                                              "children": [{
                                              "sviIf": {
                                                "attributes": {
                                                  "adminSt": "up",
                                                      "id": intName}}}]}}]}}


    headers ={ # headers specify the type of input sent to the api and the cookie that is being used to authenticate with the device
        'Content-Type': 'text/plain',
        'Cookie': 'APIC-cookie=' + authCookie
        }
    
    response = requests.request("POST", url, headers=headers, verify=False, data=json.dumps(payload)) #  repsone sends the api post call to the location specified in the url variable

    return response # response is returned back to code for further use


def changeNXHSRP(mgmtIP, intName, hsrpIP, authCookie): # function responsible for creating HSRP config on NXAPI devices

    url = 'https://' + mgmtIP + '/api/mo/sys.json' # url contains the destination for the api call, with mgmtIP being the ip address of the
                                                  # device being passed to the function


    payload = { # the payload iterates through the model, passing intName, hsrpID, and hsrpIP to id and ip attributes respectively 
      "topSystem": {
        "children": [
          {
            "interfaceEntity": {
              "children": [
                {
                  "sviIf": {
                    "attributes": {
                      "id": intName
                    }
                  }
                }
              ]
            }
          },
          {
            "hsrpEntity": {
              "children": [
                {
                  "hsrpInst": {
                    "children": [
                      {
                        "hsrpIf": {
                          "attributes": {
                            "id": intName
                          },
                          "children": [
                            {
                              "hsrpGroup": {
                                "attributes": {
                                  "af": "ipv4",
                                  "id": '10',
                                  "ip": hsrpIP,
                                  "ipObtainMode": "admin"
                                }
                              }
                            }
                          ]
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        ]
      }
    }






    headers ={ # headers specify the type of input sent to the api and the cookie that is being used to authenticate with the device
        'Content-Type': 'text/plain',
        'Cookie': 'APIC-cookie=' + authCookie
        }
    
    response = requests.request("POST", url, headers=headers, verify=False, data=json.dumps(payload)) #  repsone sends the api post call to the location specified in the url variable

    return response # response is returned back to code for further use






def changeNXOSPF(mgmtIP, procID, intName, authCookie): # function responsible for creating OSPF config on NXAPI devices

    url = 'https://' + mgmtIP + '/api/mo/sys.json' # url contains the destination for the api call, with mgmtIP being the ip address of the
                                                  # device being passed to the function


    payload = { # the payload iterates through the model, passing intName, area, and procID to id, area, and name attributes respectively
    "topSystem": {
    "children": [{
        "ospfEntity": {
          "children": [{
              "ospfInst": {
                "attributes": {
                  "name": procID},
                "children": [{
                    "ospfDom": {
                      "attributes": {
                        "name": "default"},
                      "children": [{
                          "ospfIf": {
                            "attributes": {
                              "advertiseSecondaries": "yes", # advertiseSecondaries set to no so that the routing table is not mixed up with the previous address configured
                              "area": '0.0.0.0',
                              "id": intName
                            }}}]}}]}}]}},{"interfaceEntity": {
                                "children": [{
                                "sviIf": {
                                "attributes": {
                                "id": intName}}}]}}]}}

    headers ={ # headers specify the type of input sent to the api and the cookie that is being used to authenticate with the device
        'Content-Type': 'text/plain',
        'Cookie': 'APIC-cookie=' + authCookie
        }
    
    response = requests.request("POST", url, headers=headers, verify=False, data=json.dumps(payload)) #  repsone sends the api post call to the location specified in the url variable

    return response # response is returned back to code for further use



def hsrpIPValue(modifiedIP): # Function responsible for making the hsrp address for each interface 

    seperateOctets = modifiedIP.split('.') #variable that splits the modifiedIP on the decimals for easier handling of octets
    
    octetList = [] #empty list which will contain octets       

    for octet in seperateOctets: #for loop adding all octets of the ip address to the list of octets
        octetList.append(octet)

    octetList[3] = '1'  # the last octet is changed to the lowest address for the hsrp pairing


    hsrpIP = octetList[0]+'.'+octetList[1]+'.'+octetList[2]+'.'+octetList[3] # the address is restrung together and stored as hsrpIP

    return hsrpIP # hsrpIP is returned for further use




def addIPValue(ip): # Function responsible for adding values to pre existing ip address

    seperateOctets = ip.split('.') #variable that splits the ip on the decimals for easier handling of octets
    
    octetList = [] #empty list which will contain octets       

    for octet in seperateOctets: #for loop adding all octets of the ip address to the list of octets
        octetList.append(octet)

    octetList[1] = int(octetList[1]) + 15 # The second octet of the address will be changed to an integer and have 5 added to it, after that
                                         # has been done, it will be turned back into a string and concatenated with the other octets in
                                         # octetList to be stored as one string value which is will be stored as the ipPlusFive variable
 
    
    octetList[1] = str(octetList[1])

    ipPlusFifteen = octetList[0]+'.'+octetList[1]+'.'+octetList[2]+'.'+octetList[3]

    return ipPlusFifteen # ipPlusFifteen is returned for further use


def modifyIOSXEInt(apiCall, userSN, modifiedIP, userInt, userDesc): # function responsible for modifying the dicitonary containing the device data

    null = 'null' # function in progress


def modifyIOSXEOSPF(deviceName):


    # print statement is used to tell the user to manually change the ospf parameters on the ios xe device 
    print('Manually change the OSPF network statement on', deviceName, ' to match the addressing change from the 172.16 network to the 172.31 Network. You have 120 seconds to do so.')

    time.sleep(120) # time is used to delay the main script by 120 seconds in order to allow for manual changes

    



# hard code testing and model brain storm of main, ignore commented sections below hardcode variables


nxVlanName = 'TestVlan'

nxVLAN = 'vlan-120'

vlanAddress = '172.16.120.3'

cookie = getNXCookie('10.10.20.178')

sviName = 'vlan 120'

intName = 'vlan 101'

oldvlanAddr = '172.16.101.3'


modifiedIP = addIPValue(vlanAddress)

oldmodifiedIP = addIPValue(oldvlanAddr)


print(modifiedIP)
print('addIPValue works')

newHSRPAddr = hsrpIPValue(modifiedIP)
newoldHSRPAddr = hsrpIPValue(oldmodifiedIP)


print(newHSRPAddr)
print('hsrpIPValue works')


enterVLAN = createNXVLAN('10.10.20.178', nxVLAN, nxVlanName, cookie)


print('createVLAN works')


newAddress = modifiedIP + '/24'
fullAddress = oldmodifiedIP + '/24'

enterSVI = createNXSVI('10.10.20.178', sviName, newAddress, cookie)
changeoldVLAN  = createNXSVI('10.10.20.178', intName, fullAddress, cookie)


print('createSVI works')

enterHSRP = changeNXHSRP('10.10.20.178', sviName, newHSRPAddr, cookie)
editHSRP = changeNXHSRP('10.10.20.178', intName, newoldHSRPAddr, cookie)


print('createHSRP works')

enterOSPF = changeNXOSPF('10.10.20.178', '1', sviName, cookie)

editOSPF = changeNXOSPF('10.10.20.178', '1', intName, cookie)

print('changeOSPF works')

'''
data = datafile



for device in data:

    mgmtIP = device['mgmtIP']

    deviceName = device['hostname']


    if data['type'].lower == 'nxos':
        
        cookie = getNXCookie(mgmtIP)

        getnxapidata = nxapidatafunct(mgmtip,etc)

'''        

##        cookie = getNXCookie('10.10.20.177')
##
##        enterVLAN = createVLAN('10.10.20.177', nxVLAN, nxVlanName, cookie)
##
##        enterSVI = createSVI(mgmtIP, nxVLAN, newAddress, cookie)
##
##        modifiedIP = addIPValue(intIp)
##
##        enterHSRP = createHSRP('10.10.20.177', interfaceName, newHSRPAddr, newHSRPGroup, cookie)
##
##        enterOSPF = changeOSPF(mgmtIP, OSPFProc, OSPFArea, interfaceName, cookie)

'''


    elif data['type'].lower == 'ios-xe':

        callDevice =  function to get device response

        for interface in callDevice['interface']:

            modifiedIP = addIPValue(intIp)

            changeInt = modifyIOSXEInt(apiCall, userSN, modifiedIP, userInt, userDesc)

        changeOSPF = modifyIOSXEOSPF(deviceName)

'''

        







