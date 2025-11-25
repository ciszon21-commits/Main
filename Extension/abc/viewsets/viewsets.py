from rest_framework import mixins, viewsets

from . import permissions
from . import mixins as ABCMixins




class ReadOnlyViewSet(
        mixins.RetrieveModelMixin,
        ABCMixins.ListModelMixin,
        viewsets.GenericViewSet
    ):
    """
    def retrieve(self, request, **kwargs): ...
    def list(self, request, **kwargs): ...
    """
    authentication_classes = (permissions.CsrfExemptSessionAuthentication,)


class CreateViewSet(
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        ABCMixins.CreateModelMixin,
        mixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet
    ):
    """ 只改 create，其他按照 viewsets.ModelViewSets
    def retrieve(self, request, **kwargs): ...
    def list(self, request, **kwargs): ...
    def create(self, request, **kwargs): ...
    def update(self, request, **kwargs): ...
    def destroy(self, request, **kwargs): ...
    """
    authentication_classes = (permissions.CsrfExemptSessionAuthentication,)

class UpdateViewSet(
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        ABCMixins.UpdateModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet
    ):
    """ 只改 update，其他按照 viewsets.ModelViewSets
    def retrieve(self, request, **kwargs): ...
    def list(self, request, **kwargs): ...
    def create(self, request, **kwargs): ...
    def update(self, request, **kwargs): ...
    def destroy(self, request, **kwargs): ...
    """
    authentication_classes = (permissions.CsrfExemptSessionAuthentication,)


class MyModelViewSet(
        mixins.RetrieveModelMixin,
        ABCMixins.ListModelMixin,
        ABCMixins.CreateModelMixin,
        ABCMixins.UpdateModelMixin,
        ABCMixins.DestroyModelMixin,
        viewsets.GenericViewSet,
    ):
    """ 可以改的全都要改
    def retrieve(self, request, **kwargs): ...
    def list(self, request, **kwargs): ...
    def create(self, request, **kwargs): ...
    def update(self, request, **kwargs): ...
    def destroy(self, request, **kwargs): ...
    """
    authentication_classes = (permissions.CsrfExemptSessionAuthentication,)


class MyMultipleModelViewSet(
        ABCMixins.ListModelMixin,
        ABCMixins.CreateMultipleModelMixin,
        ABCMixins.UpdateMultipleModelMixin,
        ABCMixins.DestroyMultipleModelMixin,
        viewsets.GenericViewSet,
    ):
    """ 可以大量設置 model 的 ViewSet
    def retrieve(self, request, **kwargs): ...
    def list(self, request, **kwargs): ...
    def create(self, request, **kwargs): ...
    def update(self, request, **kwargs): ...
    def destroy(self, request, **kwargs): ...
    """
    authentication_classes = (permissions.CsrfExemptSessionAuthentication,)

