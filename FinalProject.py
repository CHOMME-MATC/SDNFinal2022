'''

Date: 4/27/22

Authors: Chance Homme, Elija Muller, Cole Ringenberg


This script imports and can update a file of nxos and iosxe devices and creates a mass update for devices changing
the addressing from 172.16 to 172.32 this includes interface addresses, hsrp and ospf instances.


'''
# import statements importing various libraries responsible for parsing xml, netconf function, request, json, and ordered dictionaries

import xml.etree.ElementTree as ET
import xmltodict
import xml.dom.minidom
from lxml import etree
from ncclient import manager
import requests 
import json
import time
import sys
import requests
import re


def userInput(prompt, answerList): #User input function

    answer = input(prompt) #variable that tracks the users input according to the prompt that was passed to the function.

    while answer not in answerList: #while loop that will return the initial inpuy prompt if the users answer is not valid 
        print('Please respond using a valid answer.')
        answer = input(prompt)

    return answer

def textToJson(file): # function responsible for converting the textfile to json
    txtfile = open(file) 
    devices = txtfile.read()
    devDict = json.loads(devices)

    return devDict # devDict is returned to main for further use

def writeFileChanges(updatedDict, file): # function responsible for updating the textfile
    txtfile = open(file, 'w')
    content = json.dumps(updatedDict)
    txtfile.write(content)
    txtfile.close()

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
    print(type(Switch))
    return Switch


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

    octetList[1] = int(octetList[1]) + 15 # The second octet of the address will be changed to an integer and have 15 added to it, after that
                                         # has been done, it will be turned back into a string and concatenated with the other octets in
                                         # octetList to be stored as one string value which is will be stored as the ipPlusFive variable
 
    
    octetList[1] = str(octetList[1])

    ipPlusFifteen = octetList[0]+'.'+octetList[1]+'.'+octetList[2]+'.'+octetList[3]

    return ipPlusFifteen # ipPlusFifteen is returned for further use


def modifyIOSXEInt(modifiedIP, userInt): # function responsible for modifying the dicitonary containing the device data

    #xmlBase is the base config template used to push address changes on iosxe devices using the %var% format for configurable items

    xmlBase = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns = "urn:ietf:params:xml:ns:netconf:base:1.0">  
		<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
			<interface>
                            <%intName%>
				<name>%intNum%</name>
				
				<ip>                                    
                                    <address>
                                        <primary>
                                            <address>%addr%</address>
                                            <mask>%mask%</mask>
                                         </primary>
                                    </address>                                   
				</ip>				
			    </GigabitEthernet>
			</interface>
		    
                </native>
        </config>"""

    # Lines 152-155 were imported from the turnipTheBeet git repository

    intNumber = userInt[-1:] # intNumber stores the number of the interface
    
    intName = userInt[:-1] # intName stores the name of the interface

    # lines below are replacing the address, interface name, interface number, and subnet mask variables with user specified parameters on all
    # interfaces besides the first gigabit ethernet interface

           
    xmlBase = xmlBase.replace("%addr%", modifiedIP)
    xmlBase = xmlBase.replace("%intName%", intName)
    xmlBase = xmlBase.replace("%intNum%", intNumber)
    xmlBase = xmlBase.replace("%mask%", '255.255.255.252')

    
    return xmlBase # the xml config is returned to main for further use




def netconfCall(xmlConf, mgmtIP): # function used to make netconf call

# with statement passes the mgmtIP and other information to specify the location and auth credientials of the device

    with manager.connect(host=mgmtIP,port='830',username='cisco',password='cisco',hostkey_verify=False) as m:

        netconf_reply = m.edit_config(target = 'running', config = xmlConf) # netconf call is made using passed xml config and information from line 48 
        
#        print(netconf_reply) test print statment



def modifyIOSXEOSPF(deviceName):


    # print statement is used to tell the user to manually change the ospf parameters on the ios xe device 
    print('Enter the network 172.16.252.0 0.0.3.255 area 0 command on ' +deviceName +' to match the addressing change from the 172.16 network to the 172.31 Network. You have 120 seconds to do so.')

    time.sleep(1) # time is used to delay the main script by 120 seconds in order to allow for manual changes

    

# main

count = 2

devices = textToJson('devices.txt')

listofDevices = devices['devices']

print('The Contents of the device dictionary are as follows:')

for device in listofDevices:

    print(device)

askforUpdate = userInput('\nWould you like to add, delete, or edit the contents of the device dictionary? [Edit, Delete, Add, No Change]: ', ['edit','Edit','Delete','delete','add','no change','No Change'])

if askforUpdate.lower() == 'edit':

    deviceNum = input('Which entry would you like to update? ')

    while int(deviceNum) > 4:
        print('That is not a valid entry number')
        deviceNum = input('Which entry would you like to update? ')

    else:
        entryNum = int(deviceNum) - 1
        deviceHN = input('\nWhat is the hostname of the device? ')
        deviceType = input('\nWhat is the ios type of the device? [NXOS or IOS-XE]: ')
        deviceIP = input('\nWhat is the Management IP of the device? ')

        newValues = {"hostname": deviceHN, "devicetype": deviceType, "mgmtIP" : deviceIP}

        listofDevices[entryNum] = newValues

        print(listofDevices)
        writeFileChanges(devices,'devices.txt')
        

elif askforUpdate.lower() == 'add':
    
    deviceHN = input('\nWhat is the hostname of the device? ')
    deviceType = input('\nWhat is the ios type of the device? [NXOS or IOS-XE]: ')
    deviceIP = input('\nWhat is the Management IP of the device? ')

    newValues = {"hostname": deviceHN, "devicetype": deviceType, "mgmtIP" : deviceIP}

    listofDevices.append(newValues)
    print(listofDevices)
    writeFileChanges(devices, 'devices.txt')
    
    

elif askforUpdate.lower() == 'delete':

    deviceNum = input('Which entry would you like to remove? ')
    entryNum = int(deviceNum) - 1

    while int(deviceNum) > 4:
        print('That is not a valid entry number')
        deviceNum = input('Which entry would you like to update? ')

    else:

        del listofDevices[entryNum]
        print(listofDevices)
        writeFileChanges(devices,'devices.txt')
        
     

elif askforUpdate.lower() == 'no change':
    
    askforMassChange = userInput('Would you like to push the changes to all device configs? [Y or N]: ', ['y','n','Y','N'])

    if askforMassChange.lower() == 'n':
        print('No changes were made to the above devices')

    elif askforMassChange.lower() == 'y':
        
        for device in listofDevices:
            if device['devicetype'].lower() == 'ios-xe':

                
                    
                iosxeDict = getRouterIPs(device['mgmtIP'])
    
                for interface in iosxeDict:
                    intNumber = interface[-1:]
                    
                    if int(intNumber) > 1:
                                
                        modifiedIP = addIPValue(iosxeDict[interface])
                        xmlConf = modifyIOSXEInt(modifiedIP, interface)
                        ioscall = netconfCall(xmlConf, device['mgmtIP'])
                        changeospf = modifyIOSXEOSPF(device['hostname'])
            
            elif device['devicetype'].lower() == 'nxos':

                # lines 611 to 624 are made to add the vlan interface on dist-sw01&2
                
                if count < 4:
                    newVlan = 'vlan-120'
                    sviName = 'vlan 120'
                    vlanName = 'TestVlan'
                    vlanAddress = '172.16.120' + ('.'+str(count))
                    cookie = getNXCookie(device['mgmtIP'])
                    enterVLAN = createNXVLAN(device['mgmtIP'], newVlan, vlanName, cookie)
                    modifiedIP = addIPValue(vlanAddress)
                    vlanHSRPAddr = hsrpIPValue(modifiedIP)
                    newAddress = modifiedIP + '/24'
                    enterSVI = createNXSVI(device['mgmtIP'], sviName, newAddress, cookie)
                    enterHSRP = changeNXHSRP(device['mgmtIP'], sviName, vlanHSRPAddr, cookie)
                    enterOSPF = changeNXOSPF(device['mgmtIP'], '1', sviName, cookie)
                    count +=1
                

                interfaceDict = getSwitchIPs(device['mgmtIP'])

                for interface in interfaceDict.keys():
                    if interface.startswith('Vlan'):
                        print(interfaceDict[interface])
                        print(interface)
                        intNumber = interface.lower()[-3:] # intNumber stores the number of the interface
                        intName = interface.lower()[:-3] # intName stores the name of the interface)
                        interfacename = intName + ' ' + intNumber
                        print(interfacename)
                        cookie = getNXCookie(device['mgmtIP'])
                        modifiedIP = addIPValue(interfaceDict[interface])
                        HSRPAddr = hsrpIPValue(modifiedIP)
                        fullAddress = modifiedIP + '/24'
                        changeoldVLAN = createNXSVI(device['mgmtIP'], interfacename, fullAddress, cookie)
                        changeHSRP = changeNXHSRP(device['mgmtIP'], interfacename, vlanHSRPAddr, cookie)
                        changeOSPF = changeNXOSPF(device['mgmtIP'], '1', interface, cookie)

                    elif interface.startswith('Eth'):
                        print(interfaceDict[interface])
                        print(interface)
                        cookie = getNXCookie(device['mgmtIP'])
                        modifiedIP = addIPValue(interfaceDict[interface])
                        HSRPAddr = hsrpIPValue(modifiedIP)
                        fullAddress = modifiedIP + '/30'
                        changeoldInt = createNXSVI(device['mgmtIP'], interface, fullAddress, cookie)
                        changeHSRP = changeNXHSRP(device['mgmtIP'], interface, vlanHSRPAddr, cookie)
                        changeOSPF = changeNXOSPF(device['mgmtIP'], '1', interface, cookie)


                            
                            
                            

                            


            

        


