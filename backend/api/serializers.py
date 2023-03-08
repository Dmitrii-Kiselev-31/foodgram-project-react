from django.db.transaction import atomic
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import status
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField,
                                        SlugRelatedField, ValidationError)

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User


class UsersSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user,
                                      author=obj).exists())


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ['email', 'id',
                  'username', 'first_name',
                  'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    @atomic
    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name',
                  'color', 'slug']


class CreateRecipeIngredientSerializer(ModelSerializer):
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ['id', 'amount']


class ShortRecipeSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class IngredientRecipeSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        source='ingredient',
        read_only=True)
    name = SlugRelatedField(
        source='ingredient',
        slug_field='name',
        read_only=True)
    measurement_unit = SlugRelatedField(
        source='ingredient',
        slug_field='measurement_unit',
        read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ['id', 'name',
                  'measurement_unit',
                  'amount']


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        read_only=True,
        source='ingridients_recipe')
    author = UsersSerializer(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    is_favorited = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time']

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and Favorite.objects.filter(recipe=obj,
                user=user).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and ShoppingCart.objects.filter(recipe=obj,
                user=user).exists())


class CreateRecipeSerializer(ModelSerializer):
    author = UsersSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = CreateRecipeIngredientSerializer(many=True)
    cooking_time = IntegerField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ['id', 'image', 'tags', 'author',
                  'ingredients', 'name', 'text', 'cooking_time']

    def validate_tags(self, value):
        if not value:
            raise ValidationError({'Выберите теги.'})
        if len(value) != len(set(value)):
            raise ValidationError({'Теги повторяются.'})
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError({'Выберите ингредиенты.'})
        len_amount = [i for i in value if int(i['amount']) <= 0]
        if len_amount:
            raise ValidationError({'Выберите кол-во ингредиентов.'})
        values_id = [i['id'] for i in value]
        if len(values_id) != len(set(values_id)):
            raise ValidationError({'Ингредиенты повторяются.'})
        return value

    @atomic
    def create_ingredients(self, recipe, ingredients):
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(
                recipe=recipe,
                ingredient_id=row.get('id'),
                amount=row.get('amount'),
            ) for row in ingredients])

    @atomic
    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user,
                                       **validated_data)
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class FollowSerializer(ModelSerializer):
    recipes = SerializerMethodField()
    recipes_count = IntegerField(source='recipes.count',
                                 read_only=True)
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count']
        read_only_fields = ['email', 'username']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user,
                                      author=obj).exists())

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes,
                                           many=True,
                                           read_only=True)
        return serializer.data

    def validate(self, data):
        user = self.context.get('request').user
        check_sub = Follow.objects.filter(author=self.instance,
                                          user=user).exists()
        if check_sub:
            raise ValidationError(
                detail='Подписка уже есть.',
                code=status.HTTP_400_BAD_REQUEST)
        if user == self.instance:
            raise ValidationError(
                detail='Это ваш аккаунт.',
                code=status.HTTP_400_BAD_REQUEST)
        return data
