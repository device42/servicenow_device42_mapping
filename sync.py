import json
import base64
import requests
import xml.etree.ElementTree as eTree
from lib import *


class Mapping:
    def __init__(self):
        pass

    @staticmethod
    def get_d42_api_url(model):
        return {
            'device': '/api/1.0/devices/all',
            'hardware': '/api/1.0/hardwares/',
            'service': '/api/1.0/services/',
            'software': '/api/1.0/software/',
            'company': '/api/1.0/vendors/',

        }[model]

    @staticmethod
    def get_snow_api_url(model):
        return {
            'device': '/api/now/table/cmdb_ci_server',
            'hardware': '/api/now/table/cmdb_ci_hardware',
            'service': '/api/now/table/cmdb_ci_service',
            'software': '/api/now/table/cmdb_ci_spkg',
            'company': '/api/now/table/core_company',
        }[model]


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
            response = requests.get(self.url + path, auth=(self.user, self.password), headers=headers)
            result = response.json()
        elif method == 'POST':
            response = requests.post(self.url + path, {}, data, auth=(self.user, self.password), headers=headers)
            result = response.json()
        elif method == 'PUT':
            response = requests.put(self.url + path, json.dumps(data), auth=(self.user, self.password), headers=headers)
            result = response.json()
        elif method == 'PATCH':
            response = requests.patch(self.url + path, json.dumps(data), auth=(self.user, self.password), headers=headers)
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
            response = requests.get(self.url + path, headers=headers, verify=False)
            result = response.json()
        elif method == 'POST':
            response = requests.post(self.url + path, data, headers=headers, verify=False)
            result = response.json()
        elif method == 'PUT':
            response = requests.put(self.url + path, data, headers=headers, verify=False)
            result = response.json()
        elif method == 'PATCH':
            response = requests.patch(self.url + path, json.dumps(data), auth=(self.user, self.password), headers=headers)
            result = response.json()
        return result


def init_services(settings):
    return {
        'serviceNow': ServiceNow(settings.find('servicenow')),
        'device42': Device42(settings.find('device42'))
    }


def task_execute(task, services):
    print 'Execute task:', task.attrib['description']

    resource_api = services['device42']
    target_api = services['serviceNow']

    mapping = task.find('mapping')
    mapping_api = Mapping()
    source = resource_api.request(
        mapping_api.get_d42_api_url(mapping.attrib['model']),
        'GET'
    )
    globals()[mapping.attrib['callback']](source, mapping, mapping_api, target_api, resource_api)


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
