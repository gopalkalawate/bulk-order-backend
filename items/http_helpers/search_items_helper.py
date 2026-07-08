from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import F, Q, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.response import Response

from items.models import Item
from items.serializers import ItemSearchSerializer


class SearchItemsHelper:
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 50
    MIN_TRIGRAM_SIMILARITY = 0.1

    def handle(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"error": "q is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = int(request.query_params.get("limit", self.DEFAULT_LIMIT))
        except ValueError:
            return Response({"error": "limit must be numeric"}, status=status.HTTP_400_BAD_REQUEST)
        limit = max(1, min(limit, self.MAX_LIMIT))

        queryset = Item.objects.select_related("category")

        category_id = request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            normalized_is_active = is_active.strip().lower()
            if normalized_is_active not in {"true", "false"}:
                return Response({"error": "is_active must be true or false"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(is_active=normalized_is_active == "true")

        search_query = SearchQuery(q, search_type="plain")
        queryset = (
            queryset.annotate(
                rank=SearchRank(F("search_vector"), search_query),
                name_similarity=Coalesce(TrigramSimilarity("name", q), Value(0.0)),
                description_similarity=Coalesce(TrigramSimilarity("description", q), Value(0.0)),
            )
            .annotate(similarity=F("name_similarity") + F("description_similarity"))
            .filter(Q(search_vector=search_query) | Q(similarity__gte=self.MIN_TRIGRAM_SIMILARITY))
            .annotate(score=F("rank") + F("similarity"))
            .order_by("-score", "name")[:limit]
        )

        serializer = ItemSearchSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
