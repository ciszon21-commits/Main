from django.urls import path
from .views import (
    RndRequestListView,
    RndRequestDetailView,
    RndRequestCreateView,
    RndRequestUpdateView,
    vote_request,
    update_status,
    add_comment,
)

app_name = 'rndrequest'

urlpatterns = [
    path('', RndRequestListView.as_view(), name='request_list'),
    path('<int:pk>/', RndRequestDetailView.as_view(), name='request_detail'),
    path('create/', RndRequestCreateView.as_view(), name='request_create'),
    path('<int:pk>/edit/', RndRequestUpdateView.as_view(), name='request_edit'),
    path('<int:pk>/vote/', vote_request, name='request_vote'),
    path('<int:pk>/status/', update_status, name='request_status'),
    path('<int:pk>/comment/', add_comment, name='request_comment'),
]
