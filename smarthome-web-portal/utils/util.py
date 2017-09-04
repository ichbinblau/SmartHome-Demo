# -*- coding: utf-8 -*-
"""
Module to provider util functions in all compass code
"""
import datetime
import logging
import json
from os.path import join
import re
import sys
from pytz import timezone, all_timezones, utc
from utils.settings import PROJECT_ROOT


def get_utc_now():
    """get current datetime in utc format"""
    return datetime.datetime.utcnow()


def is_dst(zonename):
    """
    Check whether the timezone is in day light saving
    :param zonename: timezone in string
    :return: true/false
    """
    tz = timezone(zonename)
    now = utc.localize(datetime.datetime.utcnow())
    return now.astimezone(tz).dst() != datetime.timedelta(0)


def get_utc_offset(zone_name):
    """
    get utc time zone offset from the time zone name, eg. zone_name: 'US/Pacific'
    """
    for tz in all_timezones:
        if zone_name in tz:
            tz_offset = timezone(zone_name)
            utc = get_utc_now()
            return tz_offset.utcoffset(utc, is_dst=is_dst(zone_name)).total_seconds()/60/60
    return None


def get_local_datetime_now(tz):
    """
    Get the datetime.now in specified timezone
    :param tz: timezone in string
    :return: the current datetime in utc
    """
    return utc.localize(get_utc_now(), is_dst=is_dst(tz)).astimezone(timezone(tz))


def toUTC(d, tz):
    """
    Convert unware datetime in this timezone to utc time
    :param d: timezone unaware datetime
    :param tz: timezone in string
    :return: datetime in utc
    """
    tz = timezone(tz)
    return tz.normalize(tz.localize(d)).astimezone(utc)


def parse_datetime(date_time, exception_class=Exception):
    """Parse datetime str to get datetime object."""
    try:
        return datetime.datetime.strptime(
            date_time, '%Y-%m-%d %H:%M:%S'
        )
    except Exception as error:
        logging.exception(error)
        raise exception_class(
            'date time %s format is invalid' % date_time
        )


def parse_datetime_range(date_time_range, exception_class=Exception):
    """parse datetime range str to pair of datetime objects."""
    try:
        start, end = date_time_range.split(',')
    except Exception as error:
        logging.exception(error)
        raise exception_class(
            'there is no `,` in date time range %s' % date_time_range
        )
    if start:
        start_datetime = parse_datetime(start, exception_class)
    else:
        start_datetime = None
    if end:
        end_datetime = parse_datetime(end, exception_class)
    else:
        end_datetime = None
    return start_datetime, end_datetime


def parse_request_arg_dict(arg, exception_class=Exception):
    """parse string to dict."""
    arg_dict = {}
    arg_pairs = arg.split(';')
    for arg_pair in arg_pairs:
        try:
            arg_name, arg_value = arg_pair.split('=', 1)
        except Exception as error:
            logging.exception(error)
            raise exception_class(
                'there is no `=` in %s' % arg_pair
            )
        arg_dict[arg_name] = arg_value
    return arg_dict


def format_datetime(date_time):
    """Generate string from datetime object."""
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def merge_dict(lhs, rhs, override=True):
    """Merge nested right dict into left nested dict recursively.

    :param lhs: dict to be merged into.
    :type lhs: dict
    :param rhs: dict to merge from.
    :type rhs: dict
    :param override: the value in rhs overide the value in left if True.
    :type override: boolean
    """
    if not isinstance(lhs, dict) or not isinstance(rhs, dict):
        if override:
            return rhs
        else:
            return lhs

    for key, value in rhs.items():
        if key not in lhs:
            lhs[key] = rhs[key]
        else:
            lhs[key] = merge_dict(lhs[key], value, override)

    return lhs


def parse_time_interval(time_interval_str):
    if not time_interval_str:
        return 0

    time_interval_tuple = [
        time_interval_element
        for time_interval_element in time_interval_str.split(' ')
        if time_interval_element
    ]
    time_interval_dict = {}
    time_interval_unit_mapping = {
        'd': 'days',
        'w': 'weeks',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds'
    }
    for time_interval_element in time_interval_tuple:
        mat = re.match(r'^([+-]?\d+)(w|d|h|m|s).*', time_interval_element)
        if not mat:
            continue

        time_interval_value = int(mat.group(1))
        time_interval_unit = time_interval_unit_mapping[mat.group(2)]
        time_interval_dict[time_interval_unit] = (
            time_interval_dict.get(time_interval_unit, 0) + time_interval_value
        )

    time_interval = datetime.timedelta(**time_interval_dict)
    if sys.version_info[0:2] > (2, 6):
        return time_interval.total_seconds()
    else:
        return (
            time_interval.microseconds + (
                time_interval.seconds + time_interval.days * 24 * 3600
            ) * 1e6
        ) / 1e6


def is_instance(instance, expected_types):
    """Check instance type is in one of expected types.

    :param instance: instance to check the type.
    :param expected_types: types to check if instance type is in them.
    :type expected_types: list of type

    :returns: True if instance type is in expect_types.
    """
    for expected_type in expected_types:
        if isinstance(instance, expected_type):
            return True

    return False


def pretty_print(*contents):
    """pretty print contents."""
    if len(contents) == 0:
        print ""
    else:
        print "\n".join(content for content in contents)


def dict_to_str(item):
    ret_str = "{"
    for key, value in item.items():
        sub_str = "\"%s\":\"%s\",\n" % (key, value)
        ret_str += sub_str
    ret_str = ret_str.strip(",") + "}"
    return ret_str


def get_full_path(*path):
    return join(PROJECT_ROOT, *path)


def get_class(kls):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        parts = kls.split('.')
    except ValueError:
        msg = "%s doesn't look like a module path" % kls
        raise ImportError(msg)

    module = ".".join(parts[:-1])
    m = __import__(module)
    try:
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            m.__name__, comp)
        raise ImportError(msg)


def is_json(myjson):
    """
    Check whether a string is a json object.
    :param myjson: the string to check
    :return: True/False
    """
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True


def url_join(*args):
    """
    Concat given arguments into a url. Trailing and leading slashes are
    stripped for each argument.
    """
    return "/".join(map(lambda x: str(x).strip('/'), args))


if __name__ == "__main__":
    print url_join("http://localhost:3423/", '/api/oic')
