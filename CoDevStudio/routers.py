from django.db import models
from django.conf import settings


READ_DB_LABELS = getattr(settings, 'READ_DB_LABELS', [])
WRITE_DB_LABELS = getattr(settings, 'WRITE_DB_LABELS', [])
MIGRATE_DB_LABELS = getattr(settings, 'MIGRATE_DB_LABELS', [])


class DataBaseRouter:
    _read_db_labels = READ_DB_LABELS
    _write_db_labels = WRITE_DB_LABELS
    _migrate_db_labels = MIGRATE_DB_LABELS
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

