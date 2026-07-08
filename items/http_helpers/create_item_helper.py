from rest_framework import status
from rest_framework.response import Response

from items.serializers import ItemSerializer


class CreateItemHelper:
    def handle(self, request):
        serializer = ItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.save()
        return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)
