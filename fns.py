import re

DEBUG = True

def typer(condition, item):
    if str(item) == '':
        return
    if condition == 'integer':
        return int(item)
    if condition == 'float':
        return float(item)
    if condition == 'string':
        return str(item)


def get_linked_devices(_target, target_api):
    linked_devices = {}
    devices = target_api.request(_target.attrib['path'], 'GET')['result']
    for device in devices:
        if device['u_device42_object_type'] == 'device':
            linked_devices[device['u_device42_id']] = device['sys_id']
    return linked_devices



def cmdb_ci_aix_server(source, mapping, _target, _resource, target_api, resource_api):
    for row in source['result']:
        data = {}
        subs = []
        fields = mapping.findall('field')
        stored_device_id = row['u_device42_id'] if len(row['u_device42_id']) > 0 else None
        for field in fields:
            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']]) + ' copied from ServiceNow'
            elif field.attrib['resource'] == 'model_id' and field.attrib['resource'] not in subs:
                # skip twice call subfields params
                subs.append(field.attrib['resource'])

                sub_link = re.search(r'.service-now.com(.+)', row[field.attrib['resource']]['link'])
                sub_link = sub_link.group(1)
                sub_fields = resource_api.request(sub_link, 'GET')['result']
                hw = {}

                if field.attrib['sub_field'] == 'manufacturer':
                    sub_link2 = re.search(r'.service-now.com(.+)', sub_fields[field.attrib['sub_field']]['link'])
                    sub_link2 = sub_link2.group(1)
                    sub_fields2 = resource_api.request(sub_link2, 'GET')['result']
                    data[field.attrib['target']] = typer(field.attrib['type'], sub_fields2[field.attrib['sub_field2']])

                if field.attrib['sub_field'] == 'name':
                    data[field.attrib['target']] = typer(field.attrib['type'], sub_fields[field.attrib['sub_field']])
                    
            elif field.attrib['resource'] == 'sys_id':
                sys_id = row[field.attrib['resource']]
            else:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])

        # update or create new
        if stored_device_id is not None:
            data['device_id'] = stored_device_id
            data.pop('name', None)
            api_result = target_api.request(_target.attrib['path'], _target.attrib['update_method'], data)
        else:
            api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)

        if DEBUG:
            print data
            #print api_result

        # update stored device in ServiceNow
        if stored_device_id is None:
            _resource.attrib['path'] + '/' + sys_id
            resource_api.request(_resource.attrib['path'] + '/' + sys_id, 'PATCH', {
                'u_device42_id': api_result['msg'][1],
                'u_device42_object_type': 'device'
            })


def to_cmdb_ci_aix_server(source, mapping, _target, _resource, target_api, resource_api):
    print get_linked_devices(_target, target_api)

    for row in source['Devices']:
        data = {}
        fields = mapping.findall('field')
        for field in fields:
            try:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])
            except:
                data[field.attrib['target']]  = 'None'

            print data[field.attrib['target']] 
            
            #target_api.request(_target.attrib['path'], _target.attrib['method'], data)





