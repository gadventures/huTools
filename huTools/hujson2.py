#!/usr/bin/env python
# encoding: utf-8
"""
hujson.py - extended json - tries to be compatible with simplejson

hujson can encode additional types like decimal and datetime into valid json.

Created by Maximillian Dornseif on 2010-09-10.
Copyright (c) 2010, 2012, 2013 HUDORA. All rights reserved.
"""
from __future__ import unicode_literals
from builtins import str
import datetime
import decimal
import json


def _unknown_handler(value):
    """Helfer für json.dmps()) - stammt aus hujson"""
    if isinstance(value, datetime.date):
        return str(value)
    elif isinstance(value, datetime.datetime):
        return value.isoformat() + 'Z'
    elif isinstance(value, decimal.Decimal):
        return str(value)
    elif hasattr(value, 'dict_mit_positionen') and callable(value.dict_mit_positionen):
        # helpful for our internal data-modelling
        return value.dict_mit_positionen()
    elif hasattr(value, 'as_dict') and callable(value.as_dict):
        # helpful for structured.Struct() Objects
        return value.as_dict()
    # for Google AppEngine
    elif hasattr(value, 'properties') and callable(value.properties):
        properties = value.properties()
        if isinstance(properties, dict):
            keys = (key for (key, datatype) in properties.items()
                if datatype.__class__.__name__ not in ['BlobProperty'])
        elif isinstance(properties, (set, list)):
            keys = properties
        else:
            return {}
        return dict((key, getattr(value, key)) for key in keys)
    elif hasattr(value, 'to_dict') and callable(value.to_dict):
        # ndb
        tmp = value.to_dict()
        if 'id' not in tmp and hasattr(value, 'key') and hasattr(value.key, 'id') and callable(value.key.id):
            tmp['id'] = value.key.id()
        return tmp
    elif hasattr(value, '_to_entity') and callable(value._to_entity):
        retdict = dict()
        value._to_entity(retdict)
        return retdict
    elif 'google.appengine.api.users.User' in str(type(value)):
        return "%s/%s" % (value.user_id(), value.email())
    elif 'google.appengine.api.datastore_types.Key' in str(type(value)):
        return str(value)
    elif 'google.appengine.api.datastore_types.BlobKey' in str(type(value)):
        return str(value)
    # for Google AppEngine `ndb`
    elif (hasattr(value, '_properties') and hasattr(value._properties, 'items')
        and callable(value._properties.items)):
            return dict([(k, v._get_value(value)) for k, v in list(value._properties.items())])
    elif hasattr(value, 'urlsafe') and callable(value.urlsafe):
        return str(value.urlsafe())
    #elif hasattr(value, '_get_value') and callable(value._get_value):
    #    retdict = dict()
    #    value._get_value(retdict)
    #    return retdict
    raise TypeError("%s(%s)" % (type(value), value))


def dumps(val, indent=' '):
    return json.dumps(val, sort_keys=True, indent=bool(indent), ensure_ascii=True,
                      default=_unknown_handler)


def loads(data):
    return json.loads(data)
