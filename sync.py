import json
import base64
import requests
import xml.etree.ElementTree as eTree
from lib import *

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Service:
    def __init__(self, settings):
        self.user = settings.attrib["user"]
        self.password = settings.attrib["password"]
        self.url = settings.attrib["url"]


class ServiceNow(Service):
    def request(self, path, method, data=()):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        result = {}
        if method == 'GET':
            response = requests.get(self.url + path, auth=(self.user, self.password),
                                    headers=headers, verify=False)
            result = response.json()
        elif method == 'POST':
            response = requests.post(self.url + path, {}, data, auth=(self.user, self.password),
                                     headers=headers, verify=False)
            result = response.json()
        elif method == 'PUT':
            response = requests.put(self.url + path, json.dumps(data), auth=(self.user, self.password),
                                    headers=headers, verify=False)
            result = response.json()
        elif method == 'PATCH':
            response = requests.patch(self.url + path, json.dumps(data), auth=(self.user, self.password),
                                      headers=headers, verify=False)
            result = response.json()
        return result


class Device42(Service):
    def request(self, path, method, data=()):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(self.user + ':' + self.password),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        result = None

        if method == 'GET':
            response = requests.get(self.url + path,
                                    headers=headers, verify=False)
            result = response.json()
        elif method == 'POST':
            response = requests.post(self.url + path, data,
                                     headers=headers, verify=False)
            result = response.json()
        elif method == 'PUT':
            response = requests.put(self.url + path, data,
                                    headers=headers, verify=False)
            result = response.json()
        elif method == 'PATCH':
            response = requests.patch(self.url + path, json.dumps(data), auth=(self.user, self.password),
                                      headers=headers, verify=False)
            result = response.json()
        return result


def init_services(settings):
    return {
        'serviceNow': ServiceNow(settings.find('servicenow')),
        'device42': Device42(settings.find('device42'))
    }


def task_execute(task, services):
    print 'Execute task:', task.attrib['description']

    _resource = task.find('api/resource')
    _target = task.find('api/target')

    if _resource.attrib['target'] == 'serviceNow':
        resource_api = services['serviceNow']
        target_api = services['device42']
    else:
        resource_api = services['device42']
        target_api = services['serviceNow']

    mapping = task.find('mapping')
    source = resource_api.request(_resource.attrib['path'], _resource.attrib['method'])
    globals()[mapping.attrib['callback']](source, mapping, _target, _resource, target_api, resource_api)


print 'Running...'

# Load mapping
config = eTree.parse('mapping.xml')
meta = config.getroot()

# Init transports services
services = init_services(meta.find('settings'))

# Parse tasks
tasks = meta.find('tasks')
for task in tasks:
    if task.attrib['enable'] == 'true':
        task_execute(task, services)
