from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .promo import PromoCode


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def check_promo_view(request):
    """
    POST /api/orders/promo/check/
    Body: {"code": "SALE20", "order_total": 500000}
    """
    code_str    = request.data.get("code", "").strip().upper()
    order_total = float(request.data.get("order_total", 0))

    if not code_str:
        return Response({"valid": False, "error": "Promo-kod kiriting"}, status=400)

    try:
        promo = PromoCode.objects.get(code__iexact=code_str)
    except PromoCode.DoesNotExist:
        return Response({"valid": False, "error": "Promo-kod topilmadi"}, status=404)

    valid, message = promo.is_valid(order_total)
    if not valid:
        return Response({"valid": False, "error": message}, status=400)

    discount = promo.calculate_discount(order_total)
    return Response({
        "valid":          True,
        "code":           promo.code,
        "discount_type":  promo.discount_type,
        "discount_value": float(promo.discount_value),
        "discount_amount": discount,
        "final_total":    round(order_total - discount, 2),
    })
