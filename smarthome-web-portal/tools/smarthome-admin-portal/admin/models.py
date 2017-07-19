# -*- coding: utf-8 -*-
"""
Model definition
"""
import datetime
import functools
from admin import db
from admin import utils


def wrap_to_dict(support_keys=[], **filters):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return _wrapper_dict(
                func(*args, **kwargs), support_keys, **filters
            )
        return wrapper
    return decorator


def _wrapper_dict(data, support_keys, **filters):
    """Helper for warpping db object into dictionary."""
    if isinstance(data, list):
        return [
            _wrapper_dict(item, support_keys, **filters)
            for item in data
        ]
    if isinstance(data, HelperMixin):
        data = data.join_to_dict()
        # data = data.to_dict()
    if not data:
        return None
    # if not isinstance(data, dict):
    #     raise exception.InvalidResponse(
    #         'response %s type is not dict' % data
    #     )
    info = {}
    for key in support_keys:
        if key in data:
            if key in filters:
                filter_keys = filters[key]
                if isinstance(filter_keys, dict):
                    info[key] = _wrapper_dict(
                        data[key], filter_keys.keys(),
                        **filter_keys
                    )
                else:
                    info[key] = _wrapper_dict(
                        data[key], filter_keys
                    )
            else:
                info[key] = data[key]
    return info


class HelperMixin(object):
    def initialize(self):
        self.update()

    def update(self):
        pass

    def to_dict(self):
        keys = self.__mapper__.columns.keys()
        dict_info = {}
        for key in keys:
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, datetime.datetime):
                    value = utils.format_datetime(value)
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
                    value = utils.format_datetime(value)
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
                    value = utils.format_datetime(value)
                if isinstance(value, HelperMixin):
                    value = value.join_to_dict_recurse()
                dict_info[key] = value

        return dict_info


class CRUDMixin(object):
    """A CRUD mixin for model classes"""
    @classmethod
    def get_or_404(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def create(cls, **kwargs):
        inst = cls(**kwargs)
        return inst.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class Gateway(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'gateway'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(30))
    url = db.Column(db.VARCHAR(100))
    address = db.Column(db.VARCHAR(100))
    latitude = db.Column(db.VARCHAR(20))
    longitude = db.Column(db.VARCHAR(20))
    status = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)

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


class User(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(20))
    password = db.Column(db.VARCHAR(64))
    phone = db.Column(db.VARCHAR(15))
    gateway_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    gateway = db.relation('Gateway', backref='user', lazy=False)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)

    def __init__(self, username=None, password=None, gateway_id=None, phone=None):
        self.username = username
        self.password = password
        self.gateway_id = gateway_id
        self.phone = phone

    def __repr__(self):
        return "<User(id='%s',username='%s',password='%s',gateway_id='%s',created_at='%s')>" % (
            str(self.id), self.username, self.password, self.gateway_id, str(self.created_at))


class DataSet(CRUDMixin, HelperMixin, db.Model):
    __tablename__= 'dataset'

    id = db.Column(db.Integer,primary_key=True)
    filename = db.Column(db.VARCHAR(255))
    dataformat = db.Column(db.VARCHAR(10))
    title = db.Column(db.VARCHAR(50))
    rows = db.Column(db.Integer)
    columns = db.Column(db.Integer)
    description = db.Column(db.VARCHAR(200))
    uploadtime = db.Column(db.DateTime)
    status = db.Column(db.VARCHAR(10))

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


class DataModel(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'data_model'

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.VARCHAR(100))
    algorithm_type = db.Column(db.VARCHAR(50))
    serialization = db.Column(db.Integer)
    description = db.Column(db.VARCHAR(200))
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)
    status = db.Column(db.VARCHAR(1))
    dataset = db.relationship('DataSet', backref=db.backref('data_model', lazy='joined'), lazy='joined')

    def __init__(self, dataset_id=None, name=None, algorithm_type=None, serialization=None, description=None,
                 status=None):
        self.dataset_id = dataset_id
        self.name = name
        self.algorithm_type = algorithm_type
        self.serialization = serialization
        self.description = description
        # self.created_at = created_at
        self.status = status

    def __repr__(self):
        return "<DataModel(id='%s',dataset_id='%s',name='%s',algorithm_type='%s',serialization='%s',description='%s'," \
               "created_at='%s',status='%s')>" % (str(self.id), str(self.dataset_id), self.name, self.algorithm_type,
                                                  self.serialization, self.description, str(self.created_at),
                                                  str(self.status))


class ActualWeather(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'actual_weather'

    id = db.Column(db.Integer, primary_key=True)
    publish_date = db.Column(db.DATE)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)
    region_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    forecast_date = db.Column(db.DATE)
    order = db.Column(db.Integer)
    temperature = db.Column(db.FLOAT)
    humidity = db.Column(db.FLOAT)
    weather = db.Column(db.VARCHAR(45))

    def __init__(self, publish_date=None, region_id=None, forecast_date=None, order=None,
                 temperature=None, humidity=None, weather=None):
        self.publish_date = publish_date
        # self.created_at = created_at
        self.region_id = region_id
        self.forecast_date = forecast_date
        self.order = order
        self.temperature = temperature
        self.humidity = humidity
        self.weather = weather

    def __repr__(self):
        return "<ActualWeather(id='%s',publish_date='%s',created_at='%s',region_id='%s',forecast_date='%s'," \
               "order='%s',temperature='%s',humidity='%s',weather='%s')>" % (str(self.id),str(self.publish_date),
                                                                             str(self.created_at), str(self.region_id),
                                                                             str(self.forecast_date), str(self.order),
                                                                             str(self.temperature), str(self.humidity),
                                                                             self.weather)


class HisWeather(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'his_weather'

    id = db.Column(db.Integer, primary_key=True)
    publish_date = db.Column(db.DATE)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)
    region_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    temperature = db.Column(db.FLOAT)
    humidity = db.Column(db.FLOAT)
    weather = db.Column(db.VARCHAR(45))

    def __init__(self, publish_date=None, region_id=None, temperature=None, humidity=None,
                 weather=None):
        self.publish_date = publish_date
        # self.created_at = created_at
        self.region_id = region_id
        self.temperature = temperature
        self.humidity = humidity
        self.weather = weather

    def __repr__(self):
        return "<HisWeather(id='%s',publish_date='%s',created_at='%s',region_id='%s',temperature='%s',humidity='%s'," \
               "weather='%s')>" % (str(self.id), str(self.publish_date), str(self.created_at), str(self.region_id),
                                   str(self.temperature), str(self.humidity), self.weather)


class PredictedPower(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'predicted_power'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)
    region_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    predict_date = db.Column(db.DATE)
    publish_date = db.Column(db.DATE)
    order = db.Column(db.Integer)
    power = db.Column(db.FLOAT)

    def __init__(self, region_id=None, predict_date=None, publish_date=None, order=None, power=None):
        self.publish_date = publish_date
        self.region_id = region_id
        self.predict_date = predict_date
        self.order = order
        self.power = power

    def __repr__(self):
        return "<PredictedPower(id='%s',created_at='%s',region_id='%s',predict_date='%s',order='%s',power='%s')>" % \
               (str(self.id), str(self.created_at), str(self.region_id), str(self.predict_date), str(self.order),
                str(self.power))


class ActualPower(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'actual_power'

    id = db.Column(db.Integer, primary_key=True)
    collect_date = db.Column(db.DATE)
    region_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    power = db.Column(db.FLOAT)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)

    def __init__(self, collect_date=None, region_id=None, power=None):
        self.collect_date = collect_date
        self.region_id = region_id
        self.power = power

    def __repr__(self):
        return "<ActualPower(id='%s',collect_date='%s',region_id='%s',power='%s')>" % (str(self.id), str(self.collect_date),
                                                                                       str(self.region_id), str(self.power))


class GatewayModel(CRUDMixin, HelperMixin, db.Model):
    __tablename__ = 'gateway_model'

    id = db.Column(db.Integer, primary_key=True)
    gateway_id = db.Column(db.Integer, db.ForeignKey('gateway.id', ondelete='CASCADE', onupdate='CASCADE'),
                           unique=True, index=True, nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('data_model.id', ondelete='CASCADE', onupdate='CASCADE'),
                         nullable=False)
    created_at = db.Column(db.DateTime, default=utils.get_utc_now)
    gateway = db.relationship('Gateway', backref=db.backref('gateway_model', lazy='joined'), lazy='joined')
    data_model = db.relationship('DataModel', backref=db.backref('gateway_model', lazy='joined'), lazy='joined')

    def __init__(self, gateway_id=None, model_id=None):
        self.gateway_id = gateway_id
        self.model_id = model_id

    def __repr__(self):
        return "<GatewayModel(id='%s',gateway_id='%s',model_id='%s',created_at='%s')>" % (
            str(self.id), str(self.gateway_id), str(self.model_id), str(self.created_at))
