import django_filters

import recipes.models as models


class IngredientsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains')

    class Meta:
        model = models.Ingredient
        fields = ('name',)


class RecipesFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug')
    is_favorited = django_filters.BooleanFilter(
        field_name='is_favorited',
        method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart')

    class Meta:
        model = models.Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset.exclude(favorites__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset.exclude(shopping_list__user=self.request.user)
