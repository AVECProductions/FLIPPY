from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scanners', views.ActiveScannerViewSet)
router.register(r'listings', views.ListingViewSet)
router.register(r'keywords', views.KeywordViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'scanner-locations', views.ScannerLocationMappingViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/keywords/by_scanner/', views.KeywordViewSet.as_view({'get': 'by_scanner'})),
    path('api/keywords/update_for_scanner/', views.KeywordViewSet.as_view({'post': 'update_for_scanner'})),
] 