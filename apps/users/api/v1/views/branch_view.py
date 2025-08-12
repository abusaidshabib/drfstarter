"""
User application view
"""
from django.db.models.query import QuerySet
from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from apps.core.utils import format_response, user_branches_company
from apps.users.api.v1.serializers import BranchSerializer
from apps.users.models import Branch


class BranchListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def get_queryset(self):
        _, _, branches = user_branches_company(self.request)
        return branches.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return format_response({
            'message': 'Branch list retrieved successfully',
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,  context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return format_response({
            'message': 'Branch created successfully',
            'results': serializer.data
        }, status_code=status.HTTP_201_CREATED)


class BranchGetUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def get_queryset(self) -> QuerySet[Branch]:
        _, _, branches = user_branches_company(self.request)
        return branches

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return format_response({
            'message': 'Branch retrieved successfully',
            'results': serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return format_response({
            'message': 'Branch updated successfully',
            'results': serializer.data
        }, status_code=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return format_response({
            'message': 'Branch deleted successfully',
            'results': {}
        }, status_code=status.HTTP_204_NO_CONTENT)
