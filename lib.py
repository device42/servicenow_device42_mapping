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


def from_d42(source, mapping, mapping_api, target_api, resource_api):
    source_key = mapping.attrib['source']
    key = mapping.attrib['key']
    target_batch = target_api.request(mapping_api.get_snow_api_url(mapping.attrib['model']), 'GET')['result']
    for row in source[source_key]:
        data = {}
        fields = mapping.findall('field')
        sys_id = None
        # check that current device already linked
        if key in row:
            for target_row in target_batch:
                if target_row[key] == row[key] + ' copied from Device42':
                    sys_id = target_row['sys_id']
                    break

        for field in fields:
            if field.attrib['resource'] not in row or row[field.attrib['resource']] is None:
                continue

            if field.attrib['resource'] == 'name':
                data[field.attrib['target']] = typer(field.attrib['type'],
                                                     row[field.attrib['resource']]) + ' copied from Device42'

            elif field.attrib['resource'] == 'mac_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = \
                        typer(field.attrib['type'], row[field.attrib['resource']][int(field.attrib['element'])]['mac'])

            elif field.attrib['resource'] == 'ip_addresses':
                if len(row[field.attrib['resource']]) > 0:
                    data[field.attrib['target']] = typer(
                        field.attrib['type'], row[field.attrib['resource']][int(field.attrib['element'])]['ip'])

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
        if sys_id is not None:
            data.pop(key, None)
            api_result = target_api.request(mapping_api.get_snow_api_url(mapping.attrib['model']) + '/' + sys_id,
                                            'PATCH', data)
        else:
            api_result = target_api.request(mapping_api.get_snow_api_url(mapping.attrib['model']),
                                            'POST', data)

        if DEBUG:
            print data
            print api_result

        print '.\n'
