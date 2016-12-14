import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DEBUG = False


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
            linked_objects[obj['u_device42_id']] = obj['sys_id']
    return linked_objects


def to_d42(source, mapping, _target, _resource, target_api, resource_api):
    key = mapping.attrib['key']
    for row in source['result']:
        data = {}
        fields = mapping.findall('field')
        sys_id = row['sys_id']
        stored_device42_id = row['u_device42_id'] if len(row['u_device42_id']) > 0 else None
        for field in fields:
            if field.attrib['resource'] not in row or row[field.attrib['resource']] is None:
                continue

            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'],
                                                     row[field.attrib['resource']]) + ' copied from ServiceNow'

            elif 'sub_field' in field.attrib:
                sub_link = re.search(r'.service-now.com(.+)', row[field.attrib['resource']]['link'])
                sub_link = sub_link.group(1)
                sub_field_objects = resource_api.request(sub_link, 'GET')['result']
                data[field.attrib['target']] = typer(field.attrib['type'], sub_field_objects[field.attrib['sub_field']])

                if 'sub_field2' in field.attrib:
                    sub_link2 = re.search(r'.service-now.com(.+)', sub_field_objects[field.attrib['sub_field']]['link'])
                    sub_link2 = sub_link2.group(1)
                    sub_field2_objects = resource_api.request(sub_link2, 'GET')['result']
                    data[field.attrib['target']] = typer(field.attrib['type'], sub_field2_objects[field.attrib['sub_field2']])

            else:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])

        # update or create new
        if stored_device42_id is not None:
            data[key] = stored_device42_id
            old_name = data['name']
            data.pop('name', None)
            api_result = target_api.request(_target.attrib['path'], _target.attrib['update_method'], data)

            if int(api_result['code']) == 3:
                # resend if device removed
                stored_device42_id = None
                data['name'] = old_name
                api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)
        else:
            api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)

        if DEBUG:
            print data
            print api_result

        # update stored device in ServiceNow
        if stored_device42_id is None:
            _resource.attrib['path'] + '/' + sys_id
            resource_api.request(_resource.attrib['path'] + '/' + sys_id, 'PATCH', {
                'u_device42_id': api_result['msg'][1]
            })

        print '.\n'


def from_d42(source, mapping, _target, _resource, target_api, resource_api):
    source_key = mapping.attrib['source']
    key = mapping.attrib['key']
    for row in source[source_key]:
        data = {}
        fields = mapping.findall('field')
        # check current device in already linked devices
        linked_objects = get_linked_objects(_target, target_api)
        linked_sys_id = linked_objects[str(row[key])] if str(row[key]) in linked_objects else None
        for field in fields:
            if field.attrib['resource'] not in row or row[field.attrib['resource']] is None:
                continue

            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'],
                                                     row[field.attrib['resource']]) + ' copied from Device42'

            elif field.attrib['resource'] == 'mac_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = typer(field.attrib['type'],
                                                         row[field.attrib['resource']][int(field.attrib['element'])]['mac'])

            elif field.attrib['resource'] == 'ip_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = typer(field.attrib['type'],
                                                         row[field.attrib['resource']][int(field.attrib['element'])]['ip'])

            elif field.attrib['resource'] == 'tags':
                data[field.attrib['target']] = ', '.join(row[field.attrib['resource']])

            elif 'checker' in field.attrib:
                sub_field_objects = target_api.request(field.attrib['checker'], 'GET')['result']

                parent = None
                for sub_field_object in sub_field_objects:
                    if str(sub_field_object['name']) == str(row[field.attrib['resource']]):
                        parent = sub_field_object['sys_id']
                        break

                if parent is None:
                    parent = target_api.request(field.attrib['checker'], 'POST', {
                        'name': row[field.attrib['resource']],
                    })['result']['sys_id']

                result = parent
                if 'checker2' in field.attrib and field.attrib['resource2'] in row:
                    sub_field2_objects = target_api.request(field.attrib['checker2'], 'GET')['result']

                    child = None
                    for sub_field2_object in sub_field2_objects:
                        if str(sub_field2_object['name']) == str(row[field.attrib['resource2']]):
                            child = sub_field2_object['sys_id']
                            break

                    if child is None:
                        child = target_api.request(field.attrib['checker2'], 'POST', {
                            'name': row[field.attrib['resource2']]
                        })['result']['sys_id']

                    result = child

                data[field.attrib['target']] = result

            else:
                data[field.attrib['target']] = typer(field.attrib['type'], row[field.attrib['resource']])

        # update or create new
        if linked_sys_id is not None:
            data.pop('name', None)
            api_result = target_api.request(_target.attrib['path'] + '/' + linked_sys_id,
                                            _target.attrib['update_method'], data)
        else:
            data['u_device42_id'] = row[key]
            api_result = target_api.request(_target.attrib['path'], _target.attrib['method'], data)

        if DEBUG:
            print data
            print api_result

        print '.\n'

