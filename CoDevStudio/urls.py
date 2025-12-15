"""
URL configuration for CoDevStudio project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("Home.urls")),
    path("profile/", include("UserProfile.urls")),
    path("archive/", include("SinoArchive.urls")),
    path("showcase/", include("DevShowcase.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path('gallery/', include('ImageGallery.urls')),
    path('single_auth/', include('SingleAuth.urls')),
    path('courses/', include('CourseRegistration.urls')),
    path('tutorials/', include('TutorialHub.urls', namespace='tutorialhub')),
    path('rnd-request/', include('RndRequest.urls')),
    path('news/', include('NewsSubscriber.urls')),
]

# 開發環境下提供 media 檔案服務
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
