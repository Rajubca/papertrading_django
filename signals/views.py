# signals/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import TradeSignal
from .serializers import TradeSignalSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q


def broadcast(sig: TradeSignal):
    layer = get_channel_layer()
    data = TradeSignalSerializer(sig).data
    async_to_sync(layer.group_send)("signals:all", {"type":"notify","data":data})
    async_to_sync(layer.group_send)(f"signals:{sig.symbol}", {"type":"notify","data":data})

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in ("GET","HEAD","OPTIONS") or (request.user and request.user.is_staff)

class TradeSignalViewSet(viewsets.ModelViewSet):
    queryset = TradeSignal.objects.all()
    serializer_class = TradeSignalSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        sig = serializer.save()
        broadcast(sig)
    
    @action(detail=False, methods=["get"])
    def feed(self, request):
        """
        Returns latest N signals. Optional ?symbol= filters (case-insensitive, supports partials).
        Params: symbol (optional), limit (default 50, max 200)
        """
        symbol_q = (request.query_params.get("symbol") or "").strip()
        try:
            limit = max(1, min(200, int(request.query_params.get("limit", 50))))
        except ValueError:
            limit = 50

        qs = self.get_queryset().order_by("-created_at")
        if symbol_q:
            qs = qs.filter(
                Q(symbol__iexact=symbol_q) |
                Q(symbol__istartswith=symbol_q) |
                Q(symbol__icontains=symbol_q)
            )

        ser = self.get_serializer(qs[:limit], many=True)
        return Response(ser.data)

