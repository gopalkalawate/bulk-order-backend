from rest_framework import status
from rest_framework.response import Response

from items.serializers import ItemCategorySerializer


class CreateItemCategoryHelper:
    def handle(self, request):
        serializer = ItemCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category = serializer.save()
        return Response(ItemCategorySerializer(category).data, status=status.HTTP_201_CREATED)
