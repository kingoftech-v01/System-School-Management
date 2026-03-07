from rest_framework import viewsets, permissions
from .models import Book, BorrowRecord
from .serializers import BookSerializer, BorrowRecordSerializer

class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookSerializer
    def get_queryset(self):
        return Book.objects.all()

class BorrowRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BorrowRecordSerializer
    def get_queryset(self):
        return BorrowRecord.objects.all()
