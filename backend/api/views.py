from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
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
from api.recipes_utils import (
    add_recipe_to_list,
    create_file_for_shopping_cart,
    delete_recipe_from_list
)
from api.serializers import (
    AvatarSerializer, IngredientSerializer,
    RecipeGetSerializer, RecipePostSerializer,
    RecipeToFavoriteSerializer, RecipeToShoppingListSerializer,
    SubscriptionsSerializer, TagSerializer,
    UserSubscriptionSerializer
)
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tag,
    UserFavorite, UserShoppingList
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
        if request.user.avatar:
            request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ["post"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """
        Подписываем или удаляем подписку текущего пользователя
        на другого пользователя.
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
    def delete_subscribe(self, request, id=None):
        deleted_subscriptions = UserSubscriptions.objects.filter(
            user=request.user, subscription=get_object_or_404(User, pk=id)
        ).delete()
        if deleted_subscriptions[0]:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Вы не были подписаны на этого пользователя"},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
            return RecipePostSerializer
        return super().get_serializer_class()

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
        if request.method == "POST":
            return add_recipe_to_list(
                request=request, pk=pk, serializer=RecipeToFavoriteSerializer
            )
        return delete_recipe_from_list(
            request=request,
            pk=pk,
            model=UserFavorite
        )

    @action(
        ["post", "delete"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        if request.method == "POST":
            return add_recipe_to_list(
                request=request,
                pk=pk,
                serializer=RecipeToShoppingListSerializer
            )
        return delete_recipe_from_list(
            request=request,
            pk=pk,
            model=UserShoppingList
        )

    @action(["get"], detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачивание ингредиентов из списка покупок."""
        user = request.user

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__usershoppinglist__user=user
            ).values(
                "ingredient__name", "ingredient__measurement_unit"
            ).annotate(
                amount=Sum("amount")
            ).order_by("ingredient__name")
        )

        return create_file_for_shopping_cart(ingredients)
