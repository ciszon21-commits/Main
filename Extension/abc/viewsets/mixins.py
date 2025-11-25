from typing import Callable
from typing import overload

from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.db.models import Model as DJModel
from django.db.models import QuerySet
from django.http import HttpResponseBadRequest  # 400
from django.http import HttpResponseNotFound  # 404
from django.http import HttpResponseNotAllowed  # 405
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from Extension.abc import MyModel, MyRequest



""" README
以下的 Mixin class 底層方法都參考自 rest_framework.viewsets.GenericViewSet，
在被繼承的時候記得需要一併繼承 rest_framework.viewsets.GenericViewSet。
"""



class ModelMixin:
    def get_serializer_cls(self) -> 'type[Serializer]':
        return self.get_serializer_class()
    @overload
    def get_model_serializer(self, model:'DJModel', many:'bool'=False, **kwargs) -> 'Serializer': ...
    @overload
    def get_model_serializer(self, models:'list[DJModel]', many:'bool'=False, **kwargs) -> 'Serializer': ...
    def get_model_serializer(self, target, **kwargs) -> 'Serializer':
        return self.get_serializer(target, **kwargs)
    def get_meta_model_cls(self) -> 'type[DJModel]':
        ser = self.get_serializer_cls()
        modelCls = ser.Meta.model
        return modelCls

class DestroyMixin:
    # 刪除時候要設定的要設定欄位名稱，如果是 None 的時候就會直接刪除物件
    destroy_field:'str' = None
    # 如果有設定 destroy_field 的話，那要給這個欄位 update 成什麼值
    destroy_field_val = True



class SingleModelMixin(ModelMixin):
    def get_meta_model(self, request, **kwargs) -> 'DJModel':
        modelCls = self.get_meta_model_cls()
        return modelCls.objects.filter(**kwargs).first()
    def create_meta_model(self, request, **kwargs) -> 'DJModel':
        modelCls = self.get_meta_model_cls()
        return modelCls()

class MultipleModelMixin(ModelMixin):
    # 如果這個 ViewSet 只有一個欄位可以作為大量新增的依據的話，就設定這個
    multiple_field: 'str' = None
    # 如果這個 ViewSet 有多個欄位作為依據的話，request 內需要指定要被 split 的那個欄位
    multiple_fields:'list[str]' = None
    # 要 split 內容的字段
    field_split_step:'str' = ','

    def get_meta_models(self, request, pk:'str'=None, **kwargs) -> 'QuerySet[DJModel]':
        modelCls = self.get_meta_model_cls()
        if not pk: return modelCls.objects.none()
        pks = str(pk).split(self.field_split_step)
        noEmpLam:'Callable[[object],bool]' = lambda i: True if i else False
        pks = list(filter(noEmpLam, pks))
        return modelCls.objects.filter(pk__in=pks)
    def create_meta_models(self, request, **kwargs) -> 'list[DJModel]':
        reqData = MyRequest.request_data_2_dict(request)
        modelCls = self.get_meta_model_cls()
        fieldName = self.get_multiple_field(request, reqData)
        fieldVals = self.get_split_field_vals(request, reqData)
        cmmLambda:'Callable[[str],DJModel]' = lambda v: self.create_meta_model(request, modelCls, reqData, **{fieldName: v})
        with transaction.atomic():
            return list(map(cmmLambda, fieldVals))


    def create_meta_model(self, request, modelCls:'type[DJModel]', reqData:'dict', **kwargs) -> 'DJModel':
        data = reqData.copy()
        data.update(kwargs)
        model = modelCls()
        model = MyModel.model_update(model, **data)
        return model

    def get_multiple_field(self, request:'WSGIRequest', reqData:'dict'=None) -> 'str':
        if self.multiple_field: return self.multiple_field
        if reqData is None:
            reqData = MyRequest.request_data_2_dict(request)
        return reqData.get('multiple_field', '')
    def check_request_multiple_field(self, request:'WSGIRequest', reqData:'dict'=None) -> 'bool':
        field = self.get_multiple_field(request, reqData)
        if not field: return False
        if self.multiple_fields and field not in self.multiple_fields: return False
        return True
    def get_split_field_vals(self, request:'WSGIRequest', reqData:'dict'=None) -> 'list[str]':
        reqData = reqData if reqData is not None else MyRequest.request_data_2_dict(request)
        field = self.get_multiple_field(request, reqData)
        valueStr = reqData.get(field, '')
        if not valueStr: return []
        return str(valueStr).split(self.field_split_step)






class ListModelMixin(ModelMixin):
    """ curl -X GET
        -H 'Content-Type: application/json'
        -d '{field: value}'
        /app_name/api/model_name/
    """
    # 允許被查詢的 fields，可以下 dj filter 的條件式
    filter_fields:'list[str]' = []
    def list(self, request:'WSGIRequest', **kwargs):
        reqData = MyRequest.request_data_2_dict(request)
        reqData = {k: v for k, v in reqData.items() if k in self.filter_fields}
        if not reqData: return Response([])
        modelCls = self.get_meta_model_cls()
        models = modelCls.objects.filter(**reqData)
        modelSers = self.get_model_serializer(models, many=True)
        return Response(modelSers.data)


class CreateModelMixin(SingleModelMixin):
    """ curl -X POST
        -H 'Content-Type: application/json'
        -d '{field: value}'
        /app_name/api/model_name/
    """
    def create(self, request:'WSGIRequest', **kwargs):
        model = self.create_meta_model(request, **kwargs)
        reqData = MyRequest.request_data_2_dict(request)
        model = MyModel.model_update(model, **reqData)
        modelSer = self.get_model_serializer(model)
        return Response(modelSer.data)


class UpdateModelMixin(SingleModelMixin):
    """ curl -X PUT
        -H 'Content-Type: application/json'
        -d '{field: value}'
        /app_name/api/model_name/{id}/
        -- id:'str|int|uuid'
    """
    def update(self, request:'WSGIRequest', **kwargs):
        model = self.get_meta_model(request, **kwargs)
        if not model: return HttpResponseNotFound()
        reqData = MyRequest.request_data_2_dict(request)
        model = MyModel.model_update(model, **reqData)
        modelSer = self.get_model_serializer(model)
        return Response(modelSer.data)


class DestroyModelMixin(SingleModelMixin, DestroyMixin):
    """ curl -X DELETE
        /app_name/api/model_name/{id}/
        -- id:'str|int|uuid'
    """
    def destroy(self, request:'WSGIRequest', **kwargs):
        if self.destroy_field is not None:
            return self._delete_model_by_set_field(request, **kwargs)
        return self._real_delete_model(request, **kwargs)
    def _real_delete_model(self, request:'WSGIRequest', **kwargs):
        model = self.get_meta_model(request, **kwargs)
        if not model: return HttpResponseNotFound()
        model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def _delete_model_by_set_field(self, request:'WSGIRequest', **kwargs):
        model = self.get_meta_model(request, **kwargs)
        if not model: return HttpResponseNotFound()
        delContext = {self.destroy_field: self.destroy_field_val}
        model = MyModel.model_update(model, **delContext)
        modelSer = self.get_model_serializer(model)
        return Response(modelSer.data, status=status.HTTP_204_NO_CONTENT)





class RetrieveMultipleModelMixin(MultipleModelMixin):
    """ curl -X GET
        /app_name/api/model_name/{ids}/
        -- ids:'str' = '1,2,3'
    """
    def retrieve(self, request, **kwargs):
        models = self.get_meta_models(request, **kwargs)
        modelsSer = self.get_model_serializer(models, many=True)
        return Response(modelsSer.data)


class CreateMultipleModelMixin(MultipleModelMixin):
    """ curl -X POST
        -H 'Content-Type: application/json'
        -d '{field: value}'
        /app_name/api/model_name/
    """
    def create(self, request, **kwargs):
        reqData = MyRequest.request_data_2_dict(request)
        if not self.check_request_multiple_field(request, reqData):
            raise HttpResponseBadRequest('合理的 multiple_field 是必須的。')
        models = self.create_meta_models(request, **kwargs)
        modelSers = self.get_model_serializer(models, many=True)
        return Response(modelSers.data)


class UpdateMultipleModelMixin(MultipleModelMixin):
    """ curl -X PUT
        -H 'Content-Type: application/json'
        -d '{field: value}'
        /app_name/api/model_name/{ids}/
        -- ids:'str' = '1,2,3'
    """
    def update(self, request, **kwargs):
        models = self.get_meta_models(request, **kwargs)
        if not models: raise HttpResponseNotFound('沒有找到任何 models')
        reqData = MyRequest.request_data_2_dict(request)
        udLam:'Callable[[DJModel],DJModel]' = lambda m: MyModel.model_update(m, **reqData)
        with transaction.atomic():
            models = list(map(udLam, models))
        modelsSer = self.get_model_serializer(models, many=True)
        return Response(modelsSer.data)


class DestroyMultipleModelMixin(MultipleModelMixin, DestroyMixin):
    """ curl -X DELETE
        /app_name/api/model_name/{ids}/
        -- ids:'str' = '1,2,3'
    """
    def destroy(self, request, **kwargs):
        if self.destroy_field is not None:
            return self._delete_models_by_set_field(request, **kwargs)
        return self._real_delete_models(request, **kwargs)
    def _real_delete_models(self, request:'WSGIRequest', **kwargs):
        models = self.get_meta_models(request, **kwargs)
        if not models: return Response(status=status.HTTP_204_NO_CONTENT)
        models.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def _delete_models_by_set_field(self, request:'WSGIRequest', **kwargs):
        models = self.get_meta_models(request, **kwargs)
        if not models: return Response(status=status.HTTP_204_NO_CONTENT)
        delContext = {self.destroy_field: self.destroy_field_val}
        udLam:'Callable[[DJModel],DJModel]' = lambda m: MyModel.model_update(m, **delContext)
        with transaction.atomic():
            models = list(map(udLam, models))
        modelsSer = self.get_model_serializer(models, many=True)
        return Response(modelsSer.data, status=status.HTTP_204_NO_CONTENT)


