from rest_framework import generics
from .models import Product, Price
from .serializers import ProductSerializer, PriceSerializer
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import BasePermission, SAFE_METHODS


class AdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated  
        return request.user.is_staff  

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'This user already created.'}, status=status.HTTP_400_BAD_REQUEST)
        if username==password:
            return Response({'error': "Your password and username shouldn't be the same."}, status=status.HTTP_400_BAD_REQUEST)
        User.objects.create_user(username=username, password=password)
        return Response({'message': 'registration successful.'}, status=status.HTTP_201_CREATED)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'Wrong username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
class WholeAPIView(generics.ListAPIView):
    permission_classes = [AdminOrReadOnly]
    queryset = Price.objects.select_related('product').all() 
    serializer_class = PriceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'market',
        'brand', 
        'product_name', 
        'product_id',
        'price_id',
        'special_price',
        'regular_price',
        'price_date',
        'product_image',
        'campaign'
        ]
    
class ProductAPIView(generics.ListAPIView):  
    permission_classes = [AdminOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'market',
        'brand', 
        'product_name', 
        'product_id',
        'product_image'
        ]
    pagination_class = LimitOffsetPagination

class PriceAPIView(generics.ListAPIView): 
    permission_classes = [AdminOrReadOnly]
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'product_id',
        'price_id',
        'special_price',
        'regular_price',
        'price_date',
        'campaign'
        ]
    pagination_class = LimitOffsetPagination
