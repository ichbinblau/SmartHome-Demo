# -*- coding: utf-8 -*-
"""
Model definitions and its Mixins
"""
import datetime
import json
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.mysql import DOUBLE

from DB import exception
from utils import util


Base = declarative_base()


class DefaultMixin(object):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=util.get_utc_now)


class JSONEncoded(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class HelperMixin(object):
    def initialize(self):
        self.update()

    def update(self):
        pass

    @staticmethod
    def type_compatible(value, column_type):
        if value is None:
            return True
        if not hasattr(column_type, 'python_type'):
            return True
        column_python_type = column_type.python_type
        if isinstance(value, column_python_type):
            return True
        from decimal import Decimal
        if column_python_type in [Decimal]:
            return type(value) in [float, int]
        if issubclass(column_python_type, basestring):
            return isinstance(value, basestring)
        if column_python_type in [int, long]:
            return type(value) in [int, long]
        if column_python_type in [float]:
            return type(value) in [float, int]
        if column_python_type in [bool]:
            return type(value) in [bool]
        return False

    def validate(self):
        columns = self.__mapper__.columns
        for column in columns:
            value = getattr(self, column.name)
            if not self.type_compatible(value, column.type):
                raise exception.InvalidParameter(
                        'column %s value %r type is unexpected: %s' % (
                            column.name, value, column.type)
                )

    def to_dict(self):
        keys = self.__mapper__.columns.keys()
        dict_info = {}
        for key in keys:
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, datetime.datetime):
                    value = util.format_datetime(value)
                dict_info[key] = value
        return dict_info

    def join_to_dict(self):
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                       if not k[0] == '_'])
        dict_info = {}
        for key in joined.keys():
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, datetime.datetime):
                    value = util.format_datetime(value)
                if isinstance(value, HelperMixin):
                    value = value.to_dict()
                dict_info[key] = value

        return dict_info

    def join_to_dict_recurse(self):
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                       if not k[0] == '_'])
        dict_info = {}
        for key in joined.keys():
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, datetime.datetime):
                    value = util.format_datetime(value)
                if isinstance(value, HelperMixin):
                    value = value.join_to_dict_recurse()
                dict_info[key] = value

        return dict_info


class User(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'user'

    username = Column(VARCHAR(20))
    password = Column(VARCHAR(64))
    phone = Column(VARCHAR(15))
    gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    gateway = relationship('Gateway', backref='user', lazy=False)

    def __init__(self, username=None, password=None, gateway_id=None):
        self.username = username
        self.password = password
        self.gateway_id = gateway_id

    def __repr__(self):
        return "<User(id='%s',username='%s',password='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.username, self.password, self.gateway_id, str(self.created_at))


class Fan(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'fan'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    # gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="fan", lazy=False)

    def __init__(self, status=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Fan(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Button(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'button'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="button", lazy=False)

    def __init__(self, resource_id=None, status=None):
        self.status = status
        self.resource_id = resource_id
        # self.gateway_id = gateway_id

    def __repr__(self):
        return "<Button(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Temperature(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'temperature'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    temperature = Column(DOUBLE(precision=20, scale=15))
    units = Column(VARCHAR(10))
    range = Column(VARCHAR(20))
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="temperature", lazy=False)

    def __init__(self, temperature=None, units=None, range=None, resource_id=None):
        self.temperature = temperature
        self.units = units
        self.range = range
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Temperature(id='%s',uuid='%s',temperature='%s',units='%s',range='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.temperature), str(self.units), str(self.range),
            str(self.resource.gateway_id), str(self.created_at))


class Rgbled(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'rgbled'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    rgbvalue = Column(VARCHAR(20))
    range = Column(VARCHAR(20))
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="rgbled", lazy=False)

    def __init__(self, rgbvalue=None, range=None, resource_id=None):
        self.rgbvalue = rgbvalue
        self.range = range
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Rgbled(id='%s',uuid='%s',rgbvalue='%s',range='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.rgbvalue), str(self.range), str(self.resource.gateway_id),
            str(self.created_at))


class Led(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'led'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="led", lazy=False)

    def __init__(self, status=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Led(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Buzzer(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'buzzer'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="buzzer", lazy=False)

    def __init__(self, status=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Buzzer(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Illuminance(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'illuminance'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    illuminance = Column(Float)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="illuminance", lazy=False)

    def __init__(self, illuminance=None, resource_id=None):
        self.illuminance = illuminance
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Illuminance(id='%s',uuid='%s',illuminance='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.illuminance), str(self.resource.gateway_id), str(self.created_at))


class Motion(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'motion'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="motion", lazy=False)

    def __init__(self, status=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Motion(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Gas(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'gas'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="gas", lazy=False)

    def __init__(self, status=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Gas(id='%s',uuid='%s',status='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.status), str(self.resource.gateway_id), str(self.created_at))


class Solar(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'solar'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    status = Column(Boolean)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    tiltpercentage = Column(Float)
    lcd_first = Column(VARCHAR(30))
    lcd_second = Column(VARCHAR(30))
    resource = relationship('Resource', backref="solar", lazy=False)

    def __init__(self, status=None, tiltpercentage=None, lcd_first=None, lcd_second=None, resource_id=None):
        self.status = status
        # self.uuid = uuid
        self.resource_id = resource_id
        self.tiltpercentage = tiltpercentage
        self.lcd_first = lcd_first
        self.lcd_second = lcd_second

    def __repr__(self):
        return "<Solar(id='%s',uuid='%s',status='%s',gateway_id='%s',tiltpercentage='%s',lcd_first='%s'," \
               "lcd_second='%s',created_at='%s')>" % (str(self.id), self.resource.uuid, str(self.status),
                                                      str(self.resource.gateway_id), str(self.tiltpercentage),
                                                      self.lcd_first, str(self.lcd_second), str(self.created_at))


class Power(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'power'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    value = Column(Integer)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="power", lazy=False)

    def __init__(self, value=None, resource_id=None):
        self.value = value
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Power(id='%s',uuid='%s',value='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.value), str(self.resource.gateway_id), str(self.created_at))


class Energy(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'energy'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    value = Column(Integer)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="energy", lazy=False)

    def __init__(self, value=None, resource_id=None):
        self.value = value
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Energy(id='%s',uuid='%s',value='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.resource.uuid, str(self.value), str(self.resource.gateway_id), str(self.created_at))


class Environment(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'environment'

    # uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    temperature = Column(FLOAT)
    humidity = Column(FLOAT)
    pressure = Column(FLOAT)
    uv_index = Column(FLOAT)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="environment", lazy=False)

    def __init__(self, temperature=None, humidity=None, pressure=None, uv_index=None, resource_id=None):
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.uv_index = uv_index
        # self.uuid = uuid
        self.resource_id = resource_id

    def __repr__(self):
        return "<Environment(id='%s',uuid='%s',temperature='%s',humidity='%s',pressure='%s',uvIndex='%s'," \
               "gateway_id='%s',created_at='%s')>" % (str(self.id), self.resource.uuid, str(self.temperature),
                                                      str(self.humidity), str(self.pressure), str(self.uv_index),
                                                      str(self.resource.gateway_id), str(self.created_at))


class Audio(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'audio'

    mute = Column(Boolean)
    volume = Column(Integer)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="audio", lazy=False)

    def __init__(self, mute=None, volume=None, resource_id=None):
        self.mute = mute
        self.volume = volume
        self.resource_id = resource_id

    def __repr__(self):
        return "<Audio(id='%s',mute='%s',volume='%s',created_at='%s')>" % \
               (str(self.id), self.mute, str(self.volume), str(self.created_at))


class Brightness(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'brightness'

    brightness = Column(Integer)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="brightness", lazy=False)

    def __init__(self, brightness=None, resource_id=None):
        self.brightness = brightness
        self.resource_id = resource_id

    def __repr__(self):
        return "<Brightness(id='%s',brightness='%s',created_at='%s')>" % \
               (str(self.id), str(self.brightness), str(self.created_at))


class MP3Player(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'mp3player'

    media_states = Column(VARCHAR(50))
    playlist = Column(TEXT)
    state = Column(VARCHAR(15))
    title = Column(VARCHAR(255))
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="mp3player", lazy=False)

    def __init__(self, media_states=None, playlist=None, state=None, title=None, resource_id=None):
        self.mediaStates = media_states
        self.playList = playlist
        self.state = state
        self.title = title
        self.resource_id = resource_id

    def __repr__(self):
        return "<MP3Player(id='%s',mediaStates='%s',playList='%s',state='%s', title='%s', created_at='%s')>" % \
               (str(self.id), self.mediaStates, self.playList, self.state, self.title, str(self.created_at))


class Generic(Base, HelperMixin, DefaultMixin):
    """
    the database model for generic resource
    """
    __tablename__ = 'generic'

    json_data = Column(TEXT)
    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="generic", lazy=False)

    def __init__(self, json_data=None, resource_id=None):
        self.json_data = json_data
        self.resource_id = resource_id

    def __repr__(self):
        return "<Generic(id='%s',json_data='%s', created_at='%s')>" % \
               (str(self.id), self.json_data, str(self.created_at))


class EventLog(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'eventlog'

    type = Column(VARCHAR(10))
    data = Column(VARCHAR(100))
    response_code = Column(Integer)

    def __init__(self, type=None, data=None, response_code=None):
        self.type = type
        self.data = data
        self.response_code = response_code

    def __repr__(self):
        return "<EventLog(id='%s',type='%s',data='%s',response_code='%s',created_at='%s')>" % (
            str(self.id), self.type, self.data, str(self.response_code), str(self.created_at))


class SmsHistroy(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'sms_history'

    gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    uuid = Column(VARCHAR(40), ForeignKey('resource.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    def __init__(self, uuid=None, gateway_id=None):
        self.uuid = uuid
        self.gateway_id = gateway_id

    def __repr__(self):
        return "<SMS History(id='%s',uuid='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.uuid, str(self.gateway_id), str(self.created_at))


class Gateway(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'gateway'

    name = Column(VARCHAR(30))
    url = Column(VARCHAR(100))
    address = Column(VARCHAR(100))
    latitude = Column(VARCHAR(20))
    longitude = Column(VARCHAR(20))
    status = Column(Boolean)

    def __init__(self, name=None, url=None, address=None, latitude=None, longitude=None, status=False):
        self.name = name
        self.url = url
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

    def __repr__(self):
        return "<Gateway(id='%s',name='%s',url='%s',address='%s',latitude='%s', longitude='%s', created_at='%s')>" % (
            str(self.id), self.name, self.url, self.address, self.latitude, self.longitude, str(self.created_at))


class Resource(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'resource'

    uuid = Column(VARCHAR(40), nullable=False, index=True)
    sensor_type_id = Column(Integer, ForeignKey('sensor_type.id', ondelete='CASCADE', onupdate='CASCADE'),
                            nullable=False)
    sensor_group_id = Column(Integer, ForeignKey('sensor_group.id', ondelete='CASCADE', onupdate='CASCADE'),
                             nullable=True)
    status = Column(Boolean)
    gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    path = Column(VARCHAR(60), nullable=False)
    tag = Column(VARCHAR(200), nullable=True)
    observable = Column(Boolean)
    sensor_type = relationship('SensorType', backref='resource', lazy=False)
    sensor_group = relationship('SensorGroup', backref='resource', lazy=False)

    def __init__(self, uuid=None, sensor_type_id=None, path=None, status=None):
        self.uuid = uuid
        self.sensor_type_id = sensor_type_id
        self.path = path
        self.status = status

    def __repr__(self):
        return "<Resource(id='%s', path='%s', status='%s', created_at='%s')>" % (
            str(self.id), self.path, self.status, str(self.created_at))


class SensorType(Base, HelperMixin):
    __tablename__ = 'sensor_type'

    id = Column(Integer, primary_key=True)
    type = Column(VARCHAR(30), nullable=False)
    mapping_class = Column(VARCHAR(20), nullable=False)

    def __init__(self, sensor_type=None, mapping_class=None):
        self.type = sensor_type
        self.mapping_class = mapping_class

    def __repr__(self):
        return "<SensorType(id='%s', type='%s')>" % (str(self.id), self.type)


class SensorGroup(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'sensor_group'

    name = Column(VARCHAR(30), nullable=False)
    color = Column(VARCHAR(10), nullable=False)
    gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    def __init__(self, name=None, color=None, gateway_id=None):
        self.name = name
        self.color = color
        self.gateway_id = gateway_id

    def __repr__(self):
        return "<SensorGroup(id='%s',name='%s',color='%s', gateway_id='%s', created_at='%s')>" % (
            str(self.id), self.name, self.color, str(self.gateway_id), str(self.created_at))


class ActualWeather(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'actual_weather'

    publish_date = Column(DATE)
    region_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    forecast_date = Column(DATE)
    order = Column(Integer)
    temperature = Column(FLOAT)
    humidity = Column(FLOAT)
    weather = Column(VARCHAR(45))

    def __init__(self, publish_date=None, region_id=None, forecast_data=None, order=None, temperature=None,
                 humidity=None, weather=None):
        self.publish_date = publish_date
        self.region_id = region_id
        self.forecast_data = forecast_data
        self.order = order
        self.temperature = temperature
        self.humidity = humidity
        self.weather = weather

    def __repr__(self):
        return "<ActualWeather(id='%s',publish_date='%s',created_at='%s',region_id='%s',forecast_data='%s',order='%s'," \
               "temperature='%s',humidity='%s',weather='%s')>" % (str(self.id), str(self.publish_date), str(self.created_at),
                                                                  str(self.region_id), str(self.forecast_date),
                                                                  str(self.order), str(self.temperature),
                                                                  str(self.humidity), self.weather)


class HisWeather(Base, HelperMixin, DefaultMixin):
    __tablename__='his_weather'

    publish_date = Column(DATE)
    region_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    temperature = Column(FLOAT)
    humidity = Column(FLOAT)
    weather = Column(VARCHAR(45))

    def __init__(self, publish_date=None, region_id=None, temperature=None, humidity=None, weather=None):
        self.publish_date = publish_date
        self.region_id = region_id
        self.temperature = temperature
        self.humidity = humidity
        self.weather = weather

    def __repr__(self):
        return "<HisWeather(id='%s',publish_date='%s',created_at='%s',region_id='%s',temperature='%s',humidity='%s'," \
               "weather='%s')>" % (str(self.id), str(self.publish_date), str(self.created_at), str(self.region_id),
                                   str(self.temperature), str(self.humidity), self.weather)


class PredictedPower(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'predicted_power'

    region_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    predict_date = Column(DATE)
    publish_date = Column(DATE)
    order = Column(Integer)
    power = Column(FLOAT)

    def __init__(self, region_id=None, predict_date=None, publish_date=None, order=None, power=None):
        self.region_id = region_id
        self.predict_date = predict_date
        self.publish_date = publish_date
        self.order = order
        self.power = power

    def __repr__(self):
        return "<PredictedPower(id='%s',created_at='%s',region_id='%s',predict_date='%s',order='%s',power='%s')>" % (
            str(self.id), str(self.created_at), str(self.region_id), str(self.predict_date), str(self.order),
            str(self.power))


class ActualPower(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'actual_power'

    collect_date = Column(DATE)
    region_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    power = Column(FLOAT)

    def __init__(self, collect_date=None, region_id=None, power=None):
        self.collect_date = collect_date
        self.region_id = region_id
        self.power = power

    def __repr__(self):
        return "<ActualPower(id='%s',collect_date='%s',region_id='%s',power='%s')>" % (str(self.id),
                                                                                       str(self.collect_date),
                                                                                       str(self.region_id),
                                                                                       str(self.power))


class DataSet(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'dataset'

    filename = Column(VARCHAR(255))
    dataformat = Column(VARCHAR(10))
    title = Column(VARCHAR(50))
    rows = Column(Integer)
    columns = Column(Integer)
    description = Column(VARCHAR(200))
    uploadtime = Column(DateTime)
    status = Column(VARCHAR(10))

    def __init__(self, filename=None, dataformat=None, title=None, rows=None, columns=None, description=None,
                 uploadtime=None, status=None):
        self.filename = filename
        self.dataformat = dataformat
        self.title = title
        self.rows = rows
        self.columns = columns
        self.description = description
        self.uploadtime = uploadtime
        self.status = status

    def __repr__(self):
        return "<DataSet(id='%s',filename='%s',dataformat='%s',title='%s',rows='%s',columns='%s',description='%s'," \
               "uploadtime='%s')>" % (str(self.id), self.filename, self.dataformat, self.title, str(self.rows),
                                      str(self.columns), self.description, str(self.uploadtime), self.status)


class DataModel(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'data_model'

    dataset_id = Column(Integer, ForeignKey('dataset.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = Column(VARCHAR(100))
    algorithm_type = Column(VARCHAR(50))
    serialization = Column(Integer)
    description = Column(VARCHAR(200))
    status = Column(VARCHAR(1))
    dataset = relationship('DataSet', backref='data_model', lazy=False)

    def __init__(self, dataset_id=None, name=None, algorithm_type=None, serialization=None, description=None,
                 created_at=None, status=None):
        self.dataset_id = dataset_id
        self.name = name
        self.algorithm_type = algorithm_type
        self.serialization = serialization
        self.description = description
        self.created_at = created_at
        self.status = status

    def __repr__(self):
        return "<DataModel(id='%s',dataset_id='%s',name='%s',algorithm_type='%s',serialization='%s',description='%s'," \
               "created_at='%s',status='%s')>" % (str(self.id), str(self.dataset_id), self.name, self.algorithm_type,
                                                  self.serialization, self.description, str(self.created_at),
                                                  str(self.status))


class GatewayModel(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'gateway_model'

    gateway_id = Column(Integer, ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'),
                        unique=True, index=True, nullable=False)
    model_id = Column(Integer, ForeignKey('data_model.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    gateway = relationship('Gateway', backref='gateway_model', lazy=False)
    data_model = relationship('DataModel', backref='gateway_model', lazy=False)

    def __init__(self, gateway_id=None, model_id=None):
        self.gateway_id = gateway_id
        self.model_id = model_id

    def __repr__(self):
        return "<GatewayModel(id='%s',gateway_id='%s',model_id='%s',created_at='%s')>" % (
            str(self.id), str(self.gateway_id), str(self.model_id), str(self.created_at))


class Activity(Base, HelperMixin, DefaultMixin):
    __tablename__ = 'activity'

    resource_id = Column(Integer, ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    resource = relationship('Resource', backref="", lazy=False)
    total = Column(Integer)

    def __init__(self, resource_id=None, total=None):
        self.resource_id = resource_id
        self.resource_id = total

    def __repr__(self):
        return "<Activity(id='%s',resource_id='%s',total='%s',created_at='%s')>" % (
            str(self.id), str(self.resource_id), str(self.total), str(self.created_at))
