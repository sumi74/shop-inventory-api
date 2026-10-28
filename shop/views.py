from rest_framework import viewsets
from .models import Category, Product, Sale
from .serializers import CategorySerializer, ProductSerializer, SaleSerializer
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsOwner, IsOwnerOrReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsOwnerOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsOwnerOrReadOnly]

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all().order_by("-created_at")
    serializer_class = SaleSerializer
    http_method_names = ["get", "post", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(sold_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsOwner])
    def summary(self, request):
        today = timezone.localdate()
        sales = Sale.objects.filter(created_at__date=today)
        data = sales.aggregate(total_sales=Sum("total"), number_of_sales=Count("id"))
        return Response({
            "date": today,
            "number_of_sales": data["number_of_sales"],
            "total_sales": data["total_sales"] or 0,
        })