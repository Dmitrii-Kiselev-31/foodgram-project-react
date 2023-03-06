from django.contrib import admin
from django.contrib.admin import display

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    list_filter = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'slug']
    list_filter = ['name']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'author', 'in_favorite']
    readonly_fields = ['in_favorite']
    list_filter = ['author', 'name', 'tags']

    @display(description='Добавлено в избранное')
    def in_favorite(self, obj):
        return obj.in_favorite.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    list_filter = ['user']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    list_filter = ['user']


@admin.register(IngredientRecipe)
class IngredientForRecipesAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
    list_filter = ['recipe', 'ingredient']
