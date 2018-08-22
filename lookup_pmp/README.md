PMP Lookup Plugin
==================

This role provides a lookup plugin to get passwords from [Password Manager Pro](https://www.manageengine.com/products/passwordmanagerpro) (PMP).

Requirements
------------

Tested on Ansible 2.3.2.0

Dependencies
------------

None

Role Variables
--------------

The plugin allows to set the connection parameters using the following variables.

```yaml

pmp_lookup_config:
    pmpserver: your.server.com
    authtoken: YOUR-REST-API-TOKEN-HERE

```

Usage
-----

```yaml

---
# Reading PMP Credentials from pmp_lookup_config
- name: Lookup PMP Password
  set_fact:
    sql_password: "lookup('pmp', 'resourceName=SQL;accountName=Admin')"

# Overriding PMP Credentials specified in pmp_lookup_config
- name: Lookup PMP Password
  set_fact:
    sql_password: "lookup('pmp', 'resourceName=SQL;accountName=Admin;pmpserver=localhost;authtoken=yadayada')"
```

License
=======

BSD


Contributors
============

Carlos Mendible <https://github.com/cmendible>.