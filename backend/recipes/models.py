from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Name')
    measurement_unit = models.CharField(
        max_length=10,
        verbose_name='Measurement_unit')

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=60,
        verbose_name='Name',
        db_index=True,
        unique=True)
    color = ColorField(
        'HEX code',
        format='hex',
        unique=True)
    slug = models.SlugField(
        max_length=200,
        verbose_name='slug',
        unique=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    pub_date = models.DateTimeField(
        'Publication date',
        auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Recipe author')
    name = models.CharField(
        max_length=200,
        verbose_name='Name')
    text = models.TextField(
        max_length=1000,
        verbose_name='Recipe description')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Tags')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ingredients')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Cooking time',
        validators=[MinValueValidator(1, 'Минимальное значение - 1.')])
    image = models.ImageField(
        null=True,
        upload_to='recipes/images/',
        verbose_name='Image',
        default=None)

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ingredient')
    amount = models.IntegerField(
        verbose_name='Quantity of ingredients',
        validators=[MinValueValidator(1, 'Минимальное значение - 1.')])

    class Meta:
        verbose_name = 'IngredientRecipe'
        verbose_name_plural = 'IngredientsRecipe'
        default_related_name = 'ingridients_recipe'
        constraints = [
            UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredients')]

    def __str__(self):
        return f'{self.recipe}: {self.ingredient} – {self.amount}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe',
        related_name='in_favorite')

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        default_related_name = 'favorites'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorites')]

    def __str__(self):
        return f'{self.user} избран {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='User')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Recipe')

    class Meta:
        verbose_name = 'ShoppingCart'
        verbose_name_plural = 'ShoppingCarts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_hopping_cart')]

    def __str__(self):
        return f'{self.recipe} - добавлено.'
