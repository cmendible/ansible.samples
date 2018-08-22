import json
import urllib2
import ssl

from ansible import errors
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.template import Templar

default_context = 'pmp_lookup_config'

def fill_context(ctx, inject, **kwargs):
    '''Make a complete context from a partial context from an
    iterator call, and configuration information.

    :param dict ctx: query context
    :param dict inject: Ansible variables
    :param kwargs: additional arguments from direct lookup() call
    :return: the configuration dictionary
    :rtype: dict

    '''

    # Start with default config

    fctx = inject.get(default_context, {}).copy()
    fctx['context'] = fctx.copy()

    # Load named config context and overrides from ctx and kwargs

    for d in [ctx, kwargs]:
        if 'context' in d:
            parent_context = d.pop('context')
            if parent_context in inject:
                named_ctx = inject[parent_context]
            else:
                raise errors.AnsibleError(
                    'context %s does not exist' % parent_context)

            # Update filled context with named context

            fctx.update(named_ctx)
            fctx['context'] = fctx.copy()

        fctx.update(d)

    return fctx


class LookupModule(LookupBase):

    def render_template(self, inject, v):
        return Templar(loader=self._loader, variables=inject).template(v)

    def run(self, terms, variables, **kwargs):
        # Get context
        ctx = {}
        ctx = fill_context(ctx, variables, **kwargs)
        ctx = self.render_template(variables, ctx)

        result = []

        for term in terms:
            # Get parameters from terms
            parameterlines = term.split(';')

            # grab config items and set defaults
            parameters = {
                'resourceName': None,
                'accountName': None,
                'pmpserver': ctx.pop('pmpserver', None),
                'authtoken': ctx.pop('authtoken', None)
            }

            # Override parameter values if specified
            try:
                for line in parameterlines:
                    # get key & value
                    key, value = line.split('=')
                    # check if the key exists in the parameters object
                    assert key in parameters
                    # override the value
                    parameters[key] = value
            except ValueError as value_error:
                raise errors.AnsibleError(value_error)
            except AssertionError as assertion_error:
                raise errors.AnsibleError(assertion_error)

            # Setup the SSL Context
            context = ssl._create_unverified_context()

            # Get the Resource Id
            url = "https://%s/restapi/json/v1/resources?AUTHTOKEN=%s" % (
                parameters['pmpserver'], parameters['authtoken'])

            data = urllib2.urlopen(url, context=context).read()
            json_data = json.loads(data)

            resource_id = ''
            for k in json_data['operation']['Details']:
                if parameters['resourceName'].upper() in k['RESOURCE NAME'].upper():
                    resource_id = k['RESOURCE ID']
                    break

            if resource_id:
                # Get the Account Id.
                url = "https://%s/restapi/json/v1/resources/%s/accounts?AUTHTOKEN=%s" % (
                    parameters['pmpserver'], resource_id, parameters['authtoken'])
                data = urllib2.urlopen(url, context=context).read()
                json_data = json.loads(data)

                account_id = ''
                for k in json_data['operation']['Details']['ACCOUNT LIST']:
                    if k['ACCOUNT NAME'].upper() == parameters['accountName'].upper():
                        account_id = k['ACCOUNT ID']
                        break

                if account_id:
                     # Get the Password.
                    url = "https://%s/restapi/json/v1/resources/%s/accounts/%s/password?AUTHTOKEN=%s" % (
                        parameters['pmpserver'], resource_id, account_id, parameters['authtoken'])
                    data = urllib2.urlopen(url, context=context).read()
                    json_data = json.loads(data)
                    result.append(json_data['operation']
                                  ['Details']['PASSWORD'])
                    return result

            raise errors.AnsibleError('PMP Lookup Failed...')
