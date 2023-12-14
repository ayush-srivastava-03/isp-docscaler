# ******************************************************************************
#
#                                --- WARNING ---
#
#   This work contains trade secrets of DataDirect Networks, Inc.  Any
#   unauthorized use or disclosure of the work, or any part thereof, is
#   strictly prohibited.  Copyright in this work is the property of DataDirect.
#   Networks, Inc. All Rights Reserved. In the event of publication, the.
#   following notice shall apply: (C) 2016, DataDirect Networks, Inc.
#
# ******************************************************************************


""" Utils for EXAScaler configuration.
"""

import re


def split_list_settings(value, separator):
    """ Split value by given separator.
    """

    stripped = (a.strip() for a in value.split(separator))
    return list(a for a in stripped if len(a))

def split_list_settings_regex(value, separator):
    """ Split value by given pattern separator.
    """

    stripped = (a.strip() for a in re.split(separator, value))
    return list(a for a in stripped if len(a))


def parse_index_list(index_lists):
    """ Parse human-readable MDT/OST index lists into python lists

    This function parses target lists throughout exascaler, either
    from the config file or from the command line, and returns a list
    of indexes or raises a ValueError exception if the list is invalid.

    It takes an array of strings as it's options.

    Each string can be of the form "0-1,3,5-6", "0 1 3 5 6", or in any form
    accepted by lustre for ost pools, for example "0-32/2"

    """

    indexes = set()

    for index_spec in index_lists:
        for index_pair in index_spec.split(','):
            parts = index_pair.split('-')
            if len(parts) == 1:
                indexes.add(int(parts[0]))
            elif len(parts) == 2:
                step = 1
                step_pair = parts[1].split('/')
                if len(step_pair) == 1:
                    end = parts[1]
                elif len(step_pair) == 2:
                    step = int(step_pair[1])
                    end = step_pair[0]
                else:
                    raise ValueError

                for index in range(int(parts[0]), int(end) + 1, step):
                    indexes.add(index)
            else:
                raise ValueError

    return indexes


def parse_nodespec(index_lists):

    nodes = list()

    for index_spec in index_lists:
        if index_spec[-1] != ']':
            nodes.append(index_spec)
            continue
        (prefix, suffix) = index_spec.split('[')
        suffix = suffix[:-1]
        # do nothing is it's empty btw the []
        if not suffix:
            continue
        for node_idx in sorted(parse_index_list([suffix])):
            nodes.append('%s%d' % (prefix, node_idx))

    return nodes


def cast_to_bytes(value):
    """ Normalizes values with binary IEC suffixes like 10K (kibi), 128g (gibi), etc. to integers.

    :param value: str.
    :return: int.
    :raises: ValueError.
    """

    match = re.match(r'(?P<value>\d+)\s*(?P<order>[bBkKmMgGtTpPeE])?', value)
    if not match:
        raise ValueError('%r value cannot be casted to bytes.')
    order_str = match.group('order').lower() if match.group('order') else 'b'
    order = {
        'b': 1,
        'k': 1024,
        'm': 1048576,
        'g': 1073741824,
        't': 1099511627776,
        'p': 1125899906842624,
        'e': 1152921504606846976,
    }[order_str]
    return int(match.group('value')) * order


def convert_size_to_gigabytes(size, unit):
    """ Converts the size into a Gigabytes value.
    """

    division_factor = {
        'b':10000000000.0,
        'B':10000000000.0,
        'k':976562.0,
        'K':1000000.0,
        'm':954.0,
        'M':1000.0,
        'g':0.931,
        'G':1.0
    }[unit]
    return size/division_factor
