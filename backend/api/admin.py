from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes import models as recipes_models


class ComponentInline(admin.TabularInline):
    model = recipes_models.Amount


class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', )
    list_filter = ('measurement_unit', )


class FollowsAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'cooking_time',
        'author',
        'pub_date'
    )
    list_filter = ('tags',)
    inlines = (ComponentInline,)


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('name',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(recipes_models.User, UserAdmin)
admin.site.register(recipes_models.Tag, TagsAdmin)
admin.site.register(recipes_models.Ingredient, IngredientsAdmin)
admin.site.register(recipes_models.Follow, FollowsAdmin)
admin.site.register(recipes_models.Recipe, RecipeAdmin)
admin.site.register(recipes_models.ShoppingList, ShoppingListAdmin)
admin.site.register(recipes_models.Favorite, FavoriteAdmin)
