import json

def textToJson(file):
    txtfile = open(file)
    devices = txtfile.read()
    devDict = json.loads(devices)

    return devDict

devices = textToJson("devices.txt")
print(devices)
