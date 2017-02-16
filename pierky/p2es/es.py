# This code is Copyright 2014-2017 by Pier Carlo Chiodi.
# See full license in LICENSE file.

import json
import urllib2

from errors import P2ESError

# Sends data to ES.
# Raises exceptions: yes.
def send_to_es(CONFIG, index_name, data):
    # HTTP bulk insert toward ES

    url = '{}/{}/{}/_bulk'.format(
        CONFIG['ES_URL'],
        index_name,
        CONFIG['ES_Type']
    )

    try:
        http_res = urllib2.urlopen(url, data)
    except Exception as e:
        raise P2ESError(
            'Error while executing HTTP bulk insert on {} - {}'.format(
                index_name, str(e)
            )
        )

    # Interpreting HTTP bulk insert response

    http_plaintext = http_res.read()

    if(http_res.getcode() != 200):
        raise P2ESError(
            'Bulk insert on {} failed - '
            'HTTP status code = {} - '
            'Response {}'.format(
                index_name, http_res.getcode(), http_plaintext
            )
        )

    try:
        json_res = json.loads(http_plaintext)
    except Exception as e:
        raise P2ESError(
            'Error while decoding JSON HTTP response - '
            '{} - '
            'first 100 characters: {}'.format(
                str(e),
                http_plaintext[:100],
            )
        )

    if json_res['errors']:
        raise P2ESError(
            'Bulk insert on {} failed to process '
            'one or more documents'.format(index_name)
        )

# Checks if index_name exists.
# Returns: True | False.
# Raises exceptions: yes.
def does_index_exist(index_name, CONFIG):
    url = '{}/{}'.format(CONFIG['ES_URL'], index_name)

    try:
            head_req = urllib2.Request(url)
            head_req.get_method = lambda : 'HEAD'
            http_res = urllib2.urlopen(head_req)
            return http_res.getcode() == 200
    except urllib2.HTTPError as err:
        if err.code == 404:
            return False
        else:
            raise P2ESError(
                'Error while checking if {} index exists: {}'.format(
                    index_name, str(err)
                )
            )
    except Exception as err:
        raise P2ESError(
            'Error while checking if {} index exists: {}'.format(
                index_name, str(err)
            )
        )


# Creates index 'index_name' using template given in config.
# Raises exceptions: yes.
def create_index(index_name, CONFIG):

    # index already exists?
    if does_index_exist(index_name, CONFIG):
        return

    # index does not exist, creating it
    tpl_path = '{}/{}'.format(CONFIG['CONF_DIR'], CONFIG['ES_IndexTemplateFileName'])

    try:
        with open(tpl_path, "r") as f:
            tpl = f.read()
    except Exception as e:
        raise P2ESError(
            'Error while reading index template from file {}: {}'.format(
                tpl_path, str(e)
            )
        )

    url = '{}/{}'.format(CONFIG['ES_URL'], index_name)

    last_err = None
    try:
        http_res = urllib2.urlopen(url, tpl)
    except Exception as e:
        # something went wrong: does index exist anyway?
        last_err = str(e)
        pass

    try:
        if does_index_exist(index_name, CONFIG):
            return
    except:
        pass

    err = "An error occurred while creating index {} from template {}: "
    if last_err:
        err += last_err
    else:
        err += "error unknown"
    raise P2ESError(err.format(index_name, tpl_path))

def prepare_for_http_auth(CONFIG):
    if CONFIG['ES_AuthType'] != 'none':
        pwdman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwdman.add_password(
            None,
            CONFIG['ES_URL'],
            CONFIG['ES_UserName'],
            CONFIG['ES_Password']
        )

        if CONFIG['ES_AuthType'] == 'basic':
            auth_handler = urllib2.HTTPBasicAuthHandler(pwdman)
        elif CONFIG['ES_AuthType'] == 'digest':
            auth_handler = urllib2.HTTPDigestAuthHandler(pwdman)
        else:
            raise P2ESError(
                'Unexpected authentication type: {}'.format(CONFIG['ES_AuthType'])
            )

        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)
