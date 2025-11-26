from django.db import models
from django.conf import settings
# from PMIS import models as PmisModels

class DataBaseRouter:
    _read_db_labels = [
        'BimAuth',
        'PMIS',
    ]
    _write_db_labels = [
        'BimAuth',
    ]
    _migrate_db_labels = []
    def db_for_read(self, model:'models.Model', **hints) -> 'str':
        app_label = model._meta.app_label
        if app_label in self._read_db_labels:
            return app_label.lower()
        return 'default'
    def db_for_write(self, model:'models.Model', **hints) -> 'str':
        app_label = model._meta.app_label
        if app_label in self._write_db_labels:
            return app_label.lower()
        return 'default'
    def allow_relation(self, obj1:'models.Model', obj2:'models.Model', **hints) -> 'bool':
        return True
    def allow_migrate(self, db:'str', app_label:'str', model_name:'str'=None, **hints) -> 'bool':
        if app_label in self._migrate_db_labels:
            return db.lower() == app_label.lower()
        return db == 'default'

