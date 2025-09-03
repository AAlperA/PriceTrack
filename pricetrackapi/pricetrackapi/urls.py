from django.contrib import admin
from django.urls import path
from products.views import (
    RegisterAPIView,
    LoginAPIView,
    ProductAPIView,
    PriceAPIView,
    WholeAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterAPIView.as_view(), name='register'),
    path('api/login/', LoginAPIView.as_view(), name='login'),

    path('api/whole/', WholeAPIView.as_view(), name='price-with-product-list'),

    path('api/products/', ProductAPIView.as_view(), name='product-list'),

    path('api/prices/', PriceAPIView.as_view(), name='price-list')
]