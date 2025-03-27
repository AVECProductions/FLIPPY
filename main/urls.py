from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scanners', views.ActiveScannerViewSet)
router.register(r'listings', views.ListingViewSet)
router.register(r'keywords', views.KeywordViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
] 