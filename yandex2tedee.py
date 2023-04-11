import requests
import time

authorization = "PersonalKey YOUR_KEY_HERE"
#В данной переменной необходимо указать свой Personal token, полученный на сайте Tedee.a
#По уму, нужно делать через OAuth2.0, но компания отказала мне в регистрации моего приложения по причине того, что они якобы не продают свой продукт в СНГ. Впрочем, до определенных событий я экземпляр такого замка приобрести смог, поэтому и написал этот код.

def get_dev(event):
    url = 'https://api.tedee.com/api/v1.29/my/lock'
    headers = {'Authorization': authorization, 'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    response = response.json()
    y_devices = []
    for device in response['result']:
        y_device = {
            'id': str(device['id']),
            'name': device['name'],
            'type': 'devices.types.openable',
            'capabilities': [{
                'type': 'devices.capabilities.on_off',
                'retrievable': True,
            }],
            "properties": [{
                "type": "devices.properties.float",
                "parameters": {
                    "instance": "battery_level",
                    "unit": "unit.percent"
                }
            }],
        };
        y_devices.append(y_device)

    return {"request_id": event["headers"]["request_id"],
        "payload": {
            "user_id": str(response['result'][0]["shareDetails"]["userId"]),
            "devices": y_devices
        }
    };

def get_lock_state(event):
    ret_devices = []
    for y_device in event['payload']['devices']:
        url = 'https://api.tedee.com/api/v1.29/my/lock/' + y_device["id"]
        headers = {'Authorization': authorization, 'accept': 'application/json'}
        response = requests.get(url, headers=headers)
        response = response.json()

        t_device = response["result"]
        if t_device["lockProperties"]["state"] == 6:
            value = False
        else:
            value = True
        ret_device = {
            "id": y_device["id"],
            "capabilities": [
                {
                    "type": "devices.capabilities.on_off",
                    "state": {
                        "instance": "on",
                        "value": value
                    }
                }
            ],
            "properties": [{
                "type": "devices.properties.float",
                "state": {
                    "instance": "battery_level",
                    "value": t_device["lockProperties"]["batteryLevel"]
                }
            }]
        }
        ret_devices.append(ret_device)
        
    return {
        "request_id": event["headers"]["request_id"],
        "payload": {
            "devices": ret_devices
        }
    };

def switch(event):
    ret_devices = []
    for y_device in event['payload']['devices']:
        to_unlock = y_device["capabilities"][0]["state"]["value"]
        error_code = ""
        error_message = ""

        url = 'https://api.tedee.com/api/v1.29/my/lock/' + y_device["id"]
        headers = {'Authorization': authorization, 'accept': 'application/json'}
        response = requests.get(url, headers=headers)
        response = response.json()

        t_device = response["result"]

        if t_device["lockProperties"]["isCharging"]:
            status = "ERROR",
            error_code = "DEVICE_BUSY",
            error_message = "Device is charging"
        else:
            if to_unlock:
                url = "https://api.tedee.com/api/v1.29/my/lock/" + y_device["id"] + "/operation/unlock"
            else:
                url = "https://api.tedee.com/api/v1.29/my/lock/" + y_device["id"] + "/operation/lock"
            headers = {'Authorization': authorization, 'accept': 'application/json'}
            response = requests.post(url, headers=headers)
            response = response.json()

            if response["success"]:
                status = "DONE"
            else:
                status = "ERROR"
                error_code = "INTERNAL_ERROR"

        ret_device = {
            "id": y_device["id"],
            "capabilities": [
                {
                    "type": "devices.capabilities.on_off",
                    "state": {
                        "instance": "on",
                        "action_result": {
                            "status": status,
                            "error_code": error_code,
                            "error_message": error_message
                        }
                    }
                }
            ]
        }
        ret_devices.append(ret_device)
          
    return {
        "request_id": event["headers"]["request_id"],
        "payload": {
            "devices": ret_devices
        }
    };


def handler(event, context):
    if (event['request_type'] == 'discovery'):
        return get_dev(event)
    if (event['request_type'] == 'action'):
        return switch(event)
    if (event['request_type'] == 'query'):
        return get_lock_state(event)
