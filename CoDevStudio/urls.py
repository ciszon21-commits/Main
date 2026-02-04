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
    path('carbon/', include('CarbonEstimation.urls')),
    path('program-db/', include('ProgramDbRegistry.urls')),
    path('budget/', include('BudgetReview.urls')),
    path('er-model/', include('ERModelGenerator.urls')),  # ER Model 圖表產生器
    path('ev-signing/', include('EVCodeSigning.urls')),  # EV Code Signing 簽章管理
    path('knowledge/', include('TeamKnowledgeHub.urls')),  # 團隊知識管理
    path('synonyms/', include('SynonymManager.urls')),  # 同義詞建置工具
    path('patent/', include('PatentRegistry.urls')),  # 專利申請管理
    path('site360/', include('site360.urls')),  # Site360 360照片瀏覽
    path('Diversion-Tunnel/', include('Inlet_Design.urls')),  # 水利工程隧道水理設計模組
    path('drone/', include('DroneReservation.urls')),  # 園路無人機預約
    path('reservoir-hydro/', include('ReservoirHydro.urls')),  # 水庫水文水理計算平台
    path('search/', include('OpenSearch.urls')),  # OpenSearch 搜尋引擎
    path('geodatahub/', include('GeoDataHub.urls')),  # 地圖導向資料管理平台
    path('geocoding/', include('GeoCoding.urls')),  # 地址編碼服務
    path('bidqa/', include('BidQA.urls')),  # 標案問答管理
    path('circle-optimizer/', include('CircleOptimizer.urls')),  # 圓優化工具
    # path('consistency/', include('DesignConsistency.urls')),
    path('chat/', include('SinoChat.urls', namespace='sinochat')),  # Sinotech 聊天室
    path('interview/', include('InterviewAssessment.urls', namespace='interview_assessment')),
    path('gravity-pipe/', include('GravityPipeCalc.urls')),  # 重力管水理計算器
    path('soilmove/', include('SoilMove.urls', namespace='SoilMove')),  # 土石方查詢
    path('rpg/', include('EngineerRPG.urls')),  # 現場監造工程師職涯冒險培訓系統
    path('finance/', include('FinanceInsight.urls')),  # 財經新聞與選股建議
    path('carbon-plbc/', include('CarbonPLBC.urls', namespace='carbonplbc')),  # 外部碳排放計算系統 (PL-BC)
]

# 條件載入 ClashClassifier API
if getattr(settings, 'ENABLE_CLASH_CLASSIFIER', False):
    urlpatterns.append(path('api/clash/', include('ClashClassifier.urls')))  # 碰撞報告分類 API

# 開發環境下提供 media 檔案服務
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
