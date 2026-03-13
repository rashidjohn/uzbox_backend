import hashlib
import base64
import json
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.orders.models import Order

logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")


def _get_order(order_id, user=None):
    """Order olish — None bo'lsa 400, topilmasa None qaytaradi"""
    if not order_id:
        return None, Response({"error": "order_id majburiy"}, status=400)
    try:
        qs = Order.objects.filter(id=order_id)
        if user:
            qs = qs.filter(user=user)
        return qs.get(), None
    except (Order.DoesNotExist, Exception):
        return None, None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def click_create_url(request):
    order_id = request.data.get("order_id")
    if not order_id:
        return Response({"error": "order_id majburiy"}, status=400)
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Buyurtma topilmadi"}, status=404)

    if order.payment_method != "click":
        return Response({"error": "Bu buyurtma Click orqali tolanmaydi"}, status=400)
    if order.status != "pending":
        return Response({"error": "Buyurtma allaqachon tolangan yoki bekor qilingan"}, status=400)

    amount     = int(order.total_price)
    service_id = settings.CLICK_SERVICE_ID
    merchant_id = settings.CLICK_MERCHANT_ID

    if service_id and merchant_id:
        payment_url = (
            f"https://my.click.uz/services/pay"
            f"?service_id={service_id}"
            f"&merchant_id={merchant_id}"
            f"&amount={amount}"
            f"&transaction_param={order_id}"
            f"&return_url={FRONTEND_URL}/payment/success"
        )
        is_test = False
    else:
        payment_url = f"{FRONTEND_URL}/payment/test?method=click&order_id={order_id}&amount={amount}"
        is_test = True

    logger.info(f"Click URL yaratildi: order={order_id}, test={is_test}")
    return Response({"payment_url": payment_url, "is_test": is_test, "amount": amount, "order_id": str(order_id)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payme_create_url(request):
    order_id = request.data.get("order_id")
    if not order_id:
        return Response({"error": "order_id majburiy"}, status=400)
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Buyurtma topilmadi"}, status=404)

    if order.payment_method != "payme":
        return Response({"error": "Bu buyurtma Payme orqali tolanmaydi"}, status=400)
    if order.status != "pending":
        return Response({"error": "Buyurtma allaqachon tolangan yoki bekor qilingan"}, status=400)

    amount      = int(order.total_price)
    merchant_id = settings.PAYME_MERCHANT_ID

    if merchant_id:
        params = json.dumps({
            "m":          merchant_id,
            "ac.order_id": str(order_id),
            "a":           amount * 100,
            "c":           f"{FRONTEND_URL}/payment/success",
        })
        encoded     = base64.b64encode(params.encode()).decode()
        payment_url = f"https://checkout.paycom.uz/{encoded}"
        is_test     = False
    else:
        payment_url = f"{FRONTEND_URL}/payment/test?method=payme&order_id={order_id}&amount={amount}"
        is_test     = True

    logger.info(f"Payme URL yaratildi: order={order_id}, test={is_test}")
    return Response({"payment_url": payment_url, "is_test": is_test, "amount": amount, "order_id": str(order_id)})


@api_view(["POST"])
@permission_classes([AllowAny])
def click_webhook(request):
    """Click: action=0 Prepare, action=1 Complete"""
    try:
        action         = int(request.data.get("action", -1))
        order_id       = request.data.get("merchant_trans_id")
        amount         = request.data.get("amount")
        click_trans_id = request.data.get("click_trans_id")
        sign_time      = request.data.get("sign_time")
        sign_string    = request.data.get("sign_string")
    except (TypeError, ValueError):
        return Response({"error": -8, "error_note": "INVALID REQUEST"})

    # Imzo tekshirish (faqat real key bo'lganda)
    if settings.CLICK_SECRET_KEY:
        expected = hashlib.md5(
            f"{click_trans_id}{settings.CLICK_SERVICE_ID}{settings.CLICK_SECRET_KEY}"
            f"{order_id}{amount}{action}{sign_time}".encode()
        ).hexdigest()
        if sign_string != expected:
            logger.warning(f"Click sign xato: order={order_id}")
            return Response({"error": -1, "error_note": "SIGN CHECK FAILED"})

    try:
        order = Order.objects.get(id=order_id)
    except (Order.DoesNotExist, Exception):
        return Response({"error": -5, "error_note": "ORDER NOT FOUND"})

    if action == 0:  # Prepare
        try:
            if abs(float(order.total_price) - float(amount)) > 0.01:
                return Response({"error": -2, "error_note": "INCORRECT AMOUNT"})
        except (TypeError, ValueError):
            return Response({"error": -2, "error_note": "INCORRECT AMOUNT"})
        if order.status != "pending":
            return Response({"error": -4, "error_note": "ALREADY PAID"})
        return Response({
            "click_trans_id":    click_trans_id,
            "merchant_trans_id": order_id,
            "merchant_prepare_id": order_id,
            "error": 0, "error_note": "Success"
        })

    elif action == 1:  # Complete
        if order.status == "paid":
            return Response({"error": -4, "error_note": "ALREADY PAID"})
        order.status     = "paid"
        order.payment_id = str(click_trans_id)
        order.save(update_fields=["status", "payment_id"])
        logger.info(f"Click tolandi: order={order_id}")
        return Response({
            "click_trans_id":    click_trans_id,
            "merchant_trans_id": order_id,
            "error": 0, "error_note": "Success"
        })

    return Response({"error": -8, "error_note": "ERROR IN REQUEST"})


@api_view(["POST"])
@permission_classes([AllowAny])
def payme_webhook(request):
    """Payme JSON-RPC webhook"""
    method = request.data.get("method")
    params = request.data.get("params", {})

    if method == "CheckPerformTransaction":
        order_id = params.get("account", {}).get("order_id")
        try:
            order = Order.objects.get(id=order_id)
            if order.status != "pending":
                return Response({"error": {"code": -31050, "message": "Already paid or cancelled"}})
            return Response({"result": {"allow": True}})
        except (Order.DoesNotExist, Exception):
            return Response({"error": {"code": -31050, "message": "Order not found"}})

    elif method == "PerformTransaction":
        order_id       = params.get("account", {}).get("order_id")
        transaction_id = params.get("id")
        try:
            order = Order.objects.get(id=order_id)
            if order.status == "paid":
                return Response({"result": {"transaction": order.payment_id, "state": 2,
                                            "perform_time": int(timezone.now().timestamp() * 1000)}})
            order.status     = "paid"
            order.payment_id = str(transaction_id)
            order.save(update_fields=["status", "payment_id"])
            logger.info(f"Payme tolandi: order={order_id}")
            return Response({"result": {"transaction": transaction_id, "state": 2,
                                        "perform_time": int(timezone.now().timestamp() * 1000)}})
        except (Order.DoesNotExist, Exception):
            return Response({"error": {"code": -31050, "message": "Order not found"}})

    elif method == "CancelTransaction":
        order_id = params.get("account", {}).get("order_id")
        try:
            order = Order.objects.get(id=order_id)
            if order.status not in ("pending",):
                return Response({"error": {"code": -31007, "message": "Cannot cancel"}})
            order.status = "cancelled"
            order.save(update_fields=["status"])
            return Response({"result": {"state": -1,
                                        "cancel_time": int(timezone.now().timestamp() * 1000)}})
        except (Order.DoesNotExist, Exception):
            return Response({"error": {"code": -31050, "message": "Order not found"}})

    return Response({"error": {"code": -32601, "message": "Method not found"}})


@api_view(["POST"])
@permission_classes([AllowAny])
def test_confirm_payment(request):
    """TEST ONLY — faqat DEBUG=True da ishlaydi"""
    if not settings.DEBUG:
        return Response({"error": "Faqat test rejimda ishlaydi"}, status=403)

    order_id = request.data.get("order_id")
    if not order_id:
        return Response({"error": "order_id majburiy"}, status=400)

    try:
        order = Order.objects.get(id=order_id)
    except (Order.DoesNotExist, Exception):
        return Response({"error": "Buyurtma topilmadi"}, status=404)

    if order.status == "paid":
        return Response({"success": True, "message": "Allaqachon tolangan", "status": "paid"})

    order.status     = "paid"
    order.payment_id = f"TEST-{str(order_id)[:8].upper()}"
    order.save(update_fields=["status", "payment_id"])
    logger.info(f"Test payment: order={order_id}")
    return Response({"success": True, "order_id": str(order_id), "status": "paid"})
