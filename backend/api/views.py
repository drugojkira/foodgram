from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.mixins import GetListViewSet
from api.pagination import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.recipes_utils import format_shopping_cart
from api.serializers import (
    AvatarSerializer, IngredientSerializer,
    RecipeGetSerializer, RecipeCreateUpdateSerializer,
    RecipeToShoppingListSerializer, SubscriptionsSerializer,
    TagSerializer, UserSubscriptionSerializer
)
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tag, UserFavorite, UserShoppingList
)
from users.models import UserSubscriptions

User = get_user_model()


class UserViewSet(UserViewSet):
    """Модифицируем UserViewSet из djoser."""

    pagination_class = FoodgramPagination

    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        ["put"],
        detail=False,
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
        serializer_class=AvatarSerializer,
    )
    def avatar(self, request):
        """Представление для взаимодействия пользователя со своим аватаром."""
        user = request.user
        serializer = self.get_serializer(
            user, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        if request.user.avatar:
            request.user.avatar.delete()
            request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ["post"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """
        Подписываем текущего пользователя на другого пользователя.
        """
        user = request.user
        subscription = get_object_or_404(User, pk=id)
        data = {"user": user.id, "subscription": subscription.id}
        serializer = UserSubscriptionSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписываем текущего пользователя от другого пользователя."""
        subscription = get_object_or_404(
            UserSubscriptions, user=request.user, subscription_id=id
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], permission_classes=(IsAuthenticated,), detail=False)
    def subscriptions(self, request):
        """Получаем список подписок текущего пользователя."""
        user = self.request.user
        subscriptions = user.subscriptions.all()
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionsSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(GetListViewSet):
    """Представление для получения ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("name",)


class TagViewSet(GetListViewSet):
    """Представление для получения тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    http_method_names = ("get", "post", "patch", "delete")
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeGetSerializer

    @action(["get"], detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        """Формируем короткую ссылку на рецепт."""
        short_url_code = Recipe.objects.get(pk=pk).short_url_code
        short_url = request.build_absolute_uri(
            f"/{settings.SHORT_LINK_URL_PATH}/{short_url_code}/"
        )
        return Response(
            {"short-link": short_url},
            status=status.HTTP_200_OK,
        )

    @action(
        ["post", "delete"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Обработка добавления и удаления рецептов из избранного."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            # Проверка, если рецепт уже в избранном
            if UserFavorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Добавление рецепта в избранное
            UserFavorite.objects.create(user=user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)

        # Удаление рецепта из избранного
        favorite = UserFavorite.objects.filter(user=user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепт не найден в избранном."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        ["post", "delete"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Обработка добавления и удаления рецептов из списка покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            # Проверка, если рецепт уже в списке покупок
            if UserShoppingList.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {"detail": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Добавление рецепта в список покупок
            UserShoppingList.objects.create(user=user, recipe=recipe)
            return Response(status=status.HTTP_201_CREATED)

        # Удаление рецепта из списка покупок
        shopping_list = UserShoppingList.objects.filter(
            user=user, recipe=recipe
        )
        if shopping_list.exists():
            shopping_list.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепт не найден в списке покупок."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(["get"], detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Формирует и скачивает список покупок в виде текстового файла."""
        user = request.user

        # Получаем ингредиенты и рецепты из списка покупок пользователя
        ingredients = RecipeIngredient.objects.filter(
            recipe__usershoppinglist__user=user
        ).values(
            "ingredient__name", "ingredient__measurement_unit"
        ).annotate(amount=Sum("amount")).order_by("ingredient__name")

        recipes = Recipe.objects.filter(usershoppinglist__user=user)

        # Формируем текст для файла со списком покупок
        shopping_cart_content = format_shopping_cart(ingredients, recipes)

        # Создаём HTTP-ответ с файлом для скачивания
        response = HttpResponse(
            shopping_cart_content, content_type='text/plain'
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.txt"'

        return response
