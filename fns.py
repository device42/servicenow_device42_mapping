import re

DEBUG = True

def typer(condition, item):
    try:
        if condition == 'integer':
            return int(item)
        elif condition == 'float':
            return float(item)
        elif condition == 'string':
            return str(item)
    except:
        return ''


def get_linked_objects(_target, target_api):
    linked_objects = {}
    objects = target_api.request(_target.attrib['path'], 'GET')['result']
    for obj in objects:
        if 'u_device42_id' in obj:
            linked_devices[obj['u_device42_id']] = obj['sys_id']
    return linked_objects


def to_d42(source, mapping, _target, _resource, target_api, resource_api):
    source_key = mapping.attrib['key']
    key = mapping.attrib['key']
    for row in source['result']:
        data = {}
        subs = []
        fields = mapping.findall('field')
        sys_id = row['sys_id']
        stored_device42_id = row['u_device42_id'] if len(row['u_device42_id']) > 0 else None
        for field in [x if x.attrib['resource'] in row else None for x in fields]:
            if field is None:
                continue
            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']]) + ' copied from ServiceNow'
            elif field.attrib['resource'] == 'model_id' and 'model_id' not in subs:
                # call once
                subs.append('model_id')

                sub_link = re.search(r'.service-now.com(.+)', row[field.attrib['resource']]['link'])
                sub_link = sub_link.group(1)
                sub_fields = resource_api.request(sub_link, 'GET')['result']
                hw = {}

                sub_link2 = re.search(r'.service-now.com(.+)', sub_fields[field.attrib['sub_field']]['link'])
                sub_link2 = sub_link2.group(1)
                sub_fields2 = resource_api.request(sub_link2, 'GET')['result']
                data['manufacturer'] = typer(field.attrib['type'], sub_fields2[field.attrib['sub_field2']])
                data['hardware'] = typer(field.attrib['type'], sub_fields[field.attrib['sub_field']])
                    
            else:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])

        # update or create new
        if stored_device42_id is not None:
            data[key] = stored_device42_id
            data.pop('name', None)
            api_result = target_api.request(_target.attrib['path'], _target.attrib['update_method'], data)
        else:
            api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)

        if DEBUG:
            print data
            print api_result

        # update stored device in ServiceNow
        if stored_device42_id is None:
            _resource.attrib['path'] + '/' + sys_id
            resource_api.request(_resource.attrib['path'] + '/' + sys_id, 'PATCH', {
                'u_device42_id': api_result['msg'][1],
            })


def from_d42(source, mapping, _target, _resource, target_api, resource_api):
    source_key = mapping.attrib['key']
    key = mapping.attrib['key']
    for row in source[source_key]:
        data = {}
        subs = []
        fields = mapping.findall('field')
        # check current device in already linked devices
        linked_objects = get_linked_objects(_target, target_api)
        linked_sys_id = linked_objects[str(row[key])] if str(row[key]) in linked_objects else None
        for field in [x if x.attrib['resource'] in row else None for x in fields]:
            if field is None:
                continue
            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']]) + ' copied from Device42'
            elif field.attrib['resource'] == 'mac_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']][int(field.attrib['element'])]['mac'])
            elif field.attrib['resource'] == 'ip_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']][int(field.attrib['element'])]['ip'])
            elif field.attrib['target'] == 'model_id' and 'model_id' not in subs:

                # call once
                subs.append('model_id')

                manufacturer_id = None
                companies = target_api.request('/api/now/table/core_company', 'GET')['result']
                for company in companies:
                    if company['name'] == row['manufacturer']:
                        manufacturer_id = company['sys_id']
                        break

                if manufacturer_id is not None:
                    model_id = None
                    models = target_api.request('/api/now/table/cmdb_model', 'GET')['result']
                    for model in models:
                        if model['name'] == row['hw_model']:
                            model_id = model['sys_id']
                            break

                    if model_id is None:
                        model_id = target_api.request('/api/now/table/cmdb_model', 'POST', {
                            'name': row['hw_model'],
                            'manufacturer': manufacturer_id
                        })['result']['sys_id']

                else:
                    manufacturer_id = target_api.request('/api/now/table/core_company', 'POST', {
                        'name': row['manufacturer']
                    })['result']['sys_id']

                    model_id = target_api.request('/api/now/table/cmdb_model', 'POST', {
                        'name': row['hw_model'],
                        'manufacturer': manufacturer_id
                    })['result']['sys_id']

                data['model_id'] = model_id
            elif field.attrib['resource'] == 'tags':
                data[field.attrib['target']] = ', '.join(row[field.attrib['resource']])
            else:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])

        # update or create new
        if linked_sys_id is not None:
            data.pop('name', None)
            api_result = target_api.request(_target.attrib['path'] + '/' + linked_sys_id, _target.attrib['update_method'], data)
        else:
            data['u_device42_id'] = row[key]
            api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)

        if DEBUG:
            print linked_sys_id
            print api_result


