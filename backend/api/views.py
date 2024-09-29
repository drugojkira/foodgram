from api.filters import RecipeFilter
from api.pagination import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.recipes_utils import format_shopping_cart
from api.serializers import (AvatarSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             SubscriptionsSerializer, TagSerializer)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Ingredient, Recipe, RecipeIngredient, Tag,
                            UserFavorite, UserShoppingList, UserSubscriptions)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


class ExtendedUserViewSet(DjoserUserViewSet):
    """Модифицированный UserViewSet из djoser."""

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
        """Подписываем текущего пользователя на другого пользователя."""
        user = request.user
        subscription_user = get_object_or_404(User, pk=id)

        # Проверка на самоподписку
        if user == subscription_user:
            raise ValidationError("Нельзя подписаться на самого себя.")

        subscription, created = UserSubscriptions.objects.get_or_create(
            user=user, author=subscription_user
        )
        if not created:
            return Response(
                {"detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "detail": (
                    f"Подписка на пользователя {subscription_user.username} "
                    "успешно оформлена."
                )
            },
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписываем текущего пользователя от другого пользователя."""
        subscription = get_object_or_404(
            UserSubscriptions, user=request.user, author_id=id
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], permission_classes=(IsAuthenticated,), detail=False)
    def subscriptions(self, request):
        """Получаем список подписок текущего пользователя."""
        user = request.user
        subscriptions = UserSubscriptions.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionsSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ("get", "post", "patch", "delete")
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

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
        return self._handle_favorite_or_cart(request, pk, UserFavorite)

    @action(
        ["post", "delete"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Обработка добавления и удаления рецептов из списка покупок."""
        return self._handle_favorite_or_cart(request, pk, UserShoppingList)

    def _handle_favorite_or_cart(self, request, pk, model_class):
        """Обработчик для добавления и удаления рецептов из списков."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "DELETE":
            list_item = get_object_or_404(
                model_class, user=user, recipe=recipe
            )
            list_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        _, created = model_class.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError("Рецепт уже добавлен.")
        return Response(status=status.HTTP_201_CREATED)

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

        return FileResponse(
            shopping_cart_content, as_attachment=True,
            filename="shopping_cart.txt"
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получения ингредиентов.
    Поддерживает методы list и retrieve (только чтение).
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для получения тегов.
    Поддерживает методы list и retrieve (только чтение).
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
