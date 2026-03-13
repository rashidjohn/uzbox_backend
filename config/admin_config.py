from django.contrib import admin
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


class UzBoxAdminSite(admin.AdminSite):
    site_header = "UzBox Admin"
    site_title  = "UzBox"
    index_title = "Boshqaruv paneli"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            from apps.orders.models import Order
            from apps.products.models import Product
            from apps.users.models import User

            today     = timezone.now().date()
            this_week = timezone.now() - timedelta(days=7)
            this_month = timezone.now() - timedelta(days=30)

            # Asosiy raqamlar
            total_orders   = Order.objects.count()
            total_revenue  = Order.objects.filter(status="delivered").aggregate(s=Sum("total_price"))["s"] or 0
            total_users    = User.objects.filter(is_staff=False).count()
            total_products = Product.objects.filter(is_active=True).count()
            low_stock      = Product.objects.filter(stock__lt=5, is_active=True).count()

            # Bugungi
            today_orders   = Order.objects.filter(created_at__date=today).count()
            today_revenue  = Order.objects.filter(
                created_at__date=today, status__in=["paid","delivered"]
            ).aggregate(s=Sum("total_price"))["s"] or 0

            # Bu hafta
            week_orders  = Order.objects.filter(created_at__gte=this_week).count()
            week_revenue = Order.objects.filter(
                created_at__gte=this_week, status__in=["paid","delivered"]
            ).aggregate(s=Sum("total_price"))["s"] or 0

            # Status breakdown
            status_stats = Order.objects.values("status").annotate(count=Count("id"))
            status_map = {s["status"]: s["count"] for s in status_stats}

            # So'ngi 5 buyurtma
            recent_orders = Order.objects.select_related("user").order_by("-created_at")[:5]

            extra_context.update({
                "total_orders":   total_orders,
                "total_revenue":  f"{int(total_revenue):,}",
                "total_users":    total_users,
                "total_products": total_products,
                "low_stock":      low_stock,
                "today_orders":   today_orders,
                "today_revenue":  f"{int(today_revenue):,}",
                "week_orders":    week_orders,
                "week_revenue":   f"{int(week_revenue):,}",
                "status_pending":    status_map.get("pending", 0),
                "status_paid":       status_map.get("paid", 0),
                "status_processing": status_map.get("processing", 0),
                "status_shipped":    status_map.get("shipped", 0),
                "status_delivered":  status_map.get("delivered", 0),
                "status_cancelled":  status_map.get("cancelled", 0),
                "recent_orders":  recent_orders,
            })
        except Exception:
            pass
        return super().index(request, extra_context=extra_context)


admin.site.__class__ = UzBoxAdminSite
