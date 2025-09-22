from datetime import datetime
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Receipt
from .serializers import (
    ReceiptSerializer,
    ReceiptCreateSerializer,
    ReceiptListSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user

        # Write permissions are only allowed to the owner of the receipt.
        return obj.user == request.user


class ReceiptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing receipts.

    Provides:
    - POST: Create new receipt with image upload
    - GET: List user's receipts with optional monthly filtering
    - PATCH/PUT: Update receipt (optional, if time allows)
    - DELETE: Delete receipt (optional, if time allows)
    """

    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """Return receipts for the current user with optional filtering."""
        queryset = Receipt.objects.filter(user=self.request.user)

        # Optional month filtering: ?month=YYYY-MM
        month_filter = self.request.query_params.get("month")
        if month_filter:
            try:
                # Parse the month filter (format: YYYY-MM)
                year, month = month_filter.split("-")
                year, month = int(year), int(month)
                queryset = queryset.filter(date__year=year, date__month=month)
            except (ValueError, AttributeError):
                # Invalid month format, return empty queryset
                queryset = queryset.none()

        return queryset.order_by("-date", "-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return ReceiptCreateSerializer
        elif self.action == "list":
            return ReceiptListSerializer
        return ReceiptSerializer

    def create(self, request, *args, **kwargs):
        """Create a new receipt."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.save()

        # Return canonicalized payload with image_url
        response_serializer = ReceiptSerializer(receipt, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "month",
                openapi.IN_QUERY,
                description="Optional month filter in format YYYY-MM (e.g., 2024-01). If provided, only receipts from this month will be returned.",
                type=openapi.TYPE_STRING,
                required=False,
                pattern=r"^\d{4}-\d{2}$",
            )
        ],
        responses={
            200: openapi.Response(
                description="List of receipts (optionally filtered by month)"
            )
        },
    )
    def list(self, request, *args, **kwargs):
        """List user's receipts with optional filtering."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific receipt."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update a receipt (PATCH/PUT)."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.save()

        # Return canonicalized payload with image_url
        response_serializer = ReceiptSerializer(receipt, context={"request": request})
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a receipt."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter(
                "month",
                openapi.IN_QUERY,
                description="Month filter in format YYYY-MM (e.g., 2024-01)",
                type=openapi.TYPE_STRING,
                required=True,
                pattern=r"^\d{4}-\d{2}$",
            )
        ],
        responses={
            200: openapi.Response(
                description="Monthly summary data",
                examples={
                    "application/json": {
                        "month": "2024-01",
                        "total_count": 15,
                        "total_amount": "234.56",
                        "receipts": [],
                    }
                },
            ),
            400: openapi.Response(
                description="Bad request - invalid or missing month parameter"
            ),
        },
    )
    @action(detail=False, methods=["get"])
    def monthly_summary(self, request):
        """
        Get monthly summary of receipts.
        Returns total count and sum for the specified month.
        """
        month_filter = request.query_params.get("month")
        if not month_filter:
            return Response(
                {"error": "month parameter is required (format: YYYY-MM)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year, month = month_filter.split("-")
            year, month = int(year), int(month)
        except (ValueError, AttributeError):
            return Response(
                {"error": "Invalid month format. Use YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        receipts = Receipt.objects.filter(
            user=request.user, date__year=year, date__month=month
        )

        total_count = receipts.count()
        total_amount = sum(receipt.price for receipt in receipts)

        return Response(
            {
                "month": month_filter,
                "total_count": total_count,
                "total_amount": str(total_amount),
                "receipts": ReceiptListSerializer(
                    receipts, many=True, context={"request": request}
                ).data,
            }
        )
