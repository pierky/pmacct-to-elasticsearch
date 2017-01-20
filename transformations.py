# See TRANSFORMATIONS.md file for details

import json


def parse_conditions_list(c, d):
    if not c:
        raise Exception('Empty list')

    if isinstance(c[0], basestring):
        if c[0] == 'AND':
            if len(c) > 2:
                for sub_c in c[1:]:
                    if not parse_conditions(sub_c, d):
                        return False
                return True
            else:
                return False

        elif c[0] == 'OR':
            if len(c) > 2:
                for sub_c in c[1:]:
                    if parse_conditions(sub_c, d):
                        return True
                return False
            else:
                return True

        else:
            raise Exception(
                'Logical groups must begin with "AND" or "OR" '
                '("{}" found)'.format(c[0])
            )
    else:	
        # default to "AND" if not specified

        for sub_c in c:
            if not parse_conditions(sub_c, d):
                return False
        return True

def parse_conditions_dict(c, d, opfield):
    op = '='
    n = None
    v = None

    for k in c:
        if k == opfield:
            op = c[k]

            if not op in ('=', '>', '>=', '<', '<=', '!=', 'in', 'notin'):
                raise Exception('Unexpected operator: "{}"'.format(op))
	else:
            if n is None:
                n = k
		v = c[k]
            else:
                raise Exception('Only one name/value pair allowed')

    if op in ('in', 'notin') and not isinstance(v, list):
        raise Exception('The "{}" operator requires a list'.format(op))

    if n is None:
        raise Exception('Name/value pair expected')

    if n not in d:
        return False

    if op == '=':
        return d[n] == v
    elif op == '>':
        return d[n] > v
    elif op == '>=':
        return d[n] >= v
    elif op == '<':
        return d[n] < v
    elif op == '<=':
        return d[n] <= v
    elif op == '!=':
        return d[n] != v
    elif op == 'in':
        return d[n] in v
    elif op == 'notin':
        return not d[n] in v
    else:
        raise Exception('Operator not implemented: "{}"'.format(op))

def parse_conditions(c, d, opfield='__op__'):
    if isinstance(c, list):
        return parse_conditions_list(c, d)
    elif isinstance(c, dict):
        return parse_conditions_dict(c, d, opfield)
    else:
        raise Exception('Unexpected object type {} from {}'.format(
            type(c), str(c)
        ))

# returns True or False
def test_transformation(tr):
    ret = True

    try:
        tr_det = 'Transformations matrix ({})'.format(transformation)
    except:
        tr_det = 'Transformations matrix'
	
    if 'Conditions' not in tr:
        raise Exception('{}, "Conditions" is missing'.format(tr_det))

    if 'Actions' not in tr:
        raise Exception('{}, "Actions" is missing'.format(tr_det))

    try:
        parse_conditions(tr['Conditions'], {})
    except Exception as e:
        raise Exception('{}, invalid "Conditions": {}'.format(tr_det, str(e)))
	
    for action in tr['Actions']:
        if 'Type' not in action:
            raise Exception('{}, "Type" is missing'.format(tr_det))

        tr_det += ', action type = {}'.format(action['Type'])

        if action['Type'] not in ('AddField', 'AddFieldLookup', 'DelField'):
            raise Exception('{}, "Type" unknown'.format(tr_det))

        if 'Name' not in action:
            raise Exception('{}, "Name" is missing'.format(tr_det))

        if action['Type'] == 'AddField':
            if 'Value' not in action:
                raise Exception(
                    '{}, "Value" is missing for new field "{}"'.format(
                        tr_det, action['Name']
                    )
                ) 

        if action['Type'] == 'AddFieldLookup':
            if 'LookupFieldName' not in action:
                raise Exception(
                    '{}, "LookupFieldName" is missing for '
                    'new field "{}"'.format(tr_det, action['Name'])
                )
            if 'LookupTable' in action and 'LookupTableFile' in action:
                raise Exception(
                    '{}, only one from "LookupTable" and '
                    '"LookupTableFile" allowed'.format(tr_det)
                )
            if 'LookupTable' not in action and 'LookupTableFile' not in action:
                raise Exception(
                    '{}, "LookupTable" and "LookupTableFile" missing '
                    'for new field "{}"'.format(tr_det, action['Name'])
                )
            if 'LookupTableFile' in action:
                try:
                    with open(action['LookupTableFile'], "r") as f:
                        action['LookupTable'] = json.load(f.read())
                except:
		    raise Exception(
                        '{}, error loading lookup table from {}'.format(
                            tr_det, action['LookupTableFile']
                        )
                    )
