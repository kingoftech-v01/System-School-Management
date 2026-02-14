from rest_framework import viewsets, permissions
from .models import Article, Category
from .serializers import ArticleSerializer, CategorySerializer

class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = ArticleSerializer
    def get_queryset(self):
        return Article.objects.filter(status='published')

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True)
