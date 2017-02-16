# This code is Copyright 2014-2017 by Pier Carlo Chiodi.
# See full license in LICENSE file.

# See TRANSFORMATIONS.md file for details

import json


from errors import P2ESError

# Parse list of conditions c against data d.
# Returns: True | False (conditions matched / did not match).
# Raises exceptions: yes.
def parse_conditions_list(c, d):
    if not c:
        raise P2ESError('Empty list')

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
            raise P2ESError(
                'Logical groups must begin with "AND" or "OR" '
                '("{}" found)'.format(c[0])
            )
    else:	
        # default to "AND" if not specified

        for sub_c in c:
            if not parse_conditions(sub_c, d):
                return False
        return True

# Parse condition c against data d, using operator opfield.
# Returns: True | False (condition matched / did not match).
# Raises exceptions: yes.
def parse_conditions_dict(c, d, opfield):
    op = '='
    n = None
    v = None

    for k in c:
        if k == opfield:
            op = c[k]

            if not op in ('=', '>', '>=', '<', '<=', '!=', 'in', 'notin'):
                raise P2ESError('Unexpected operator: "{}"'.format(op))
	else:
            if n is None:
                n = k
		v = c[k]
            else:
                raise P2ESError('Only one name/value pair allowed')

    if op in ('in', 'notin') and not isinstance(v, list):
        raise P2ESError('The "{}" operator requires a list'.format(op))

    if n is None:
        raise P2ESError('Name/value pair expected')

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
        raise P2ESError('Operator not implemented: "{}"'.format(op))

# Parse conditions c against data d.
# Return: True | False (conditions matched / did not match).
# Raises exception: yes.
def parse_conditions(c, d, opfield='__op__'):
    if isinstance(c, list):
        return parse_conditions_list(c, d)
    elif isinstance(c, dict):
        return parse_conditions_dict(c, d, opfield)
    else:
        raise P2ESError('Unexpected object type {} from {}'.format(
            type(c), str(c)
        ))

# Tests if a transformation syntax is valid.
# Returns: True | False.
# Raises exceptions: yes.
def test_transformation(tr):
    ret = True

    try:
        tr_det = 'Transformations matrix ({})'.format(transformation)
    except:
        tr_det = 'Transformations matrix'
	
    if 'Conditions' not in tr:
        raise P2ESError('{}, "Conditions" is missing'.format(tr_det))

    if 'Actions' not in tr:
        raise P2ESError('{}, "Actions" is missing'.format(tr_det))

    try:
        parse_conditions(tr['Conditions'], {})
    except P2ESError as e:
        raise P2ESError('{}, invalid "Conditions": {}'.format(tr_det, str(e)))
	
    for action in tr['Actions']:
        if 'Type' not in action:
            raise P2ESError('{}, "Type" is missing'.format(tr_det))

        tr_det += ', action type = {}'.format(action['Type'])

        if action['Type'] not in ('AddField', 'AddFieldLookup', 'DelField'):
            raise P2ESError('{}, "Type" unknown'.format(tr_det))

        if 'Name' not in action:
            raise P2ESError('{}, "Name" is missing'.format(tr_det))

        if action['Type'] == 'AddField':
            if 'Value' not in action:
                raise P2ESError(
                    '{}, "Value" is missing for new field "{}"'.format(
                        tr_det, action['Name']
                    )
                ) 

        if action['Type'] == 'AddFieldLookup':
            if 'LookupFieldName' not in action:
                raise P2ESError(
                    '{}, "LookupFieldName" is missing for '
                    'new field "{}"'.format(tr_det, action['Name'])
                )
            if 'LookupTable' in action and 'LookupTableFile' in action:
                raise P2ESError(
                    '{}, only one from "LookupTable" and '
                    '"LookupTableFile" allowed'.format(tr_det)
                )
            if 'LookupTable' not in action and 'LookupTableFile' not in action:
                raise P2ESError(
                    '{}, "LookupTable" and "LookupTableFile" missing '
                    'for new field "{}"'.format(tr_det, action['Name'])
                )
            if 'LookupTableFile' in action:
                try:
                    with open(action['LookupTableFile'], "r") as f:
                        action['LookupTable'] = json.load(f)
                except Exception as e:
		    raise P2ESError(
                        '{}, error loading lookup table from {}: {}'.format(
                            tr_det, action['LookupTableFile'], str(e)
                        )
                    )

if __name__ == '__main__':
    #Test conditions
    #-------------------
    
    #C = [ { "Name": "Bob" }, { "Age": 16, "__op__": ">=" } ]
    #C = [ "OR", { "Name": "Bob" }, { "Name": "Tom" } ]
    C = [ "OR",
        [ { "Name": "Bob" }, { "Age": 16, "__op__": ">=" } ],
        { "Name": "Tom" },
        [ { "Name": "Lisa" }, { "Age": 20, "__op__": ">="  } ]
    ]
    #C = [ "Invalid" ]
    
    Data = [	
    	{ "Name": "Bob", "Age": 15 },
    	{ "Name": "Bob", "Age": 16 },
    	{ "Name": "Ken", "Age": 14 },
    	{ "Name": "Tom", "Age": 14 },
    	{ "Name": "Tom", "Age": 20 },
    	{ "Name": "Lisa", "Age": 15 },
    	{ "Name": "Lisa", "Age": 22 }
    ]
    
    print(C)
    for Person in Data:
        try:
            if parse_conditions(C, Person):
                print( "YES - %s" % Person )
            else:
                print( "--- - %s" % Person )
        except P2ESError as e:
            print( "ParseConditions error: %s" % str(e) )
            raise


