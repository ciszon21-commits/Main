"""
URL configuration for CoDevStudio project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Home.urls')),
    path('gallery/', include('ImageGallery.urls')),
    path('single_auth/', include('SingleAuth.urls')),
    path('courses/', include('CourseRegistration.urls')),
]

# 開發環境下提供 media 檔案服務
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

