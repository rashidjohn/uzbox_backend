import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price    = django_filters.NumberFilter(field_name="price",          lookup_expr="gte")
    max_price    = django_filters.NumberFilter(field_name="price",          lookup_expr="lte")
    category     = django_filters.CharFilter(field_name="category__slug")
    in_stock     = django_filters.BooleanFilter(method="filter_in_stock")
    has_discount = django_filters.BooleanFilter(method="filter_has_discount")
    ids          = django_filters.CharFilter(method="filter_ids")

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_price__isnull=False)
        return queryset.filter(discount_price__isnull=True)

    def filter_ids(self, queryset, name, value):
        """Vergul bilan ajratilgan UUID lar: ?ids=uuid1,uuid2,uuid3"""
        id_list = [v.strip() for v in value.split(",") if v.strip()]
        if id_list:
            return queryset.filter(id__in=id_list)
        return queryset

    class Meta:
        model  = Product
        fields = ["category", "min_price", "max_price", "in_stock", "has_discount", "ids"]
