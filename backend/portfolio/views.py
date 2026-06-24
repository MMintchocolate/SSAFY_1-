from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import PortfolioItem


def _serialize(item):
    return {
        'id':        item.id,
        'symbol':    item.symbol,
        'name':      item.name,
        'quantity':  float(item.quantity),
        'avg_price': float(item.avg_price),
        'cost':      float(item.quantity * item.avg_price),
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def portfolio_list(request):
    if request.method == 'GET':
        items = PortfolioItem.objects.filter(user=request.user)
        return Response([_serialize(i) for i in items])

    # POST — 추가 or 수량·단가 업데이트
    data = request.data
    symbol    = str(data.get('symbol', '')).strip().upper()
    name      = str(data.get('name', '')).strip()
    quantity  = data.get('quantity')
    avg_price = data.get('avg_price')

    if not all([symbol, name, quantity, avg_price]):
        return Response({'error': 'symbol, name, quantity, avg_price 모두 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        quantity  = float(quantity)
        avg_price = float(avg_price)
        if quantity <= 0 or avg_price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response({'error': 'quantity와 avg_price는 양수여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    item, created = PortfolioItem.objects.update_or_create(
        user=request.user, symbol=symbol,
        defaults={'name': name, 'quantity': quantity, 'avg_price': avg_price},
    )
    return Response(_serialize(item), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def portfolio_detail(request, pk):
    item = get_object_or_404(PortfolioItem, pk=pk, user=request.user)

    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PUT
    data = request.data
    try:
        item.quantity  = float(data.get('quantity',  item.quantity))
        item.avg_price = float(data.get('avg_price', item.avg_price))
        item.name      = str(data.get('name', item.name)).strip()
        if item.quantity <= 0 or item.avg_price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response({'error': '올바른 수량과 단가를 입력하세요.'}, status=status.HTTP_400_BAD_REQUEST)

    item.save()
    return Response(_serialize(item))
