from rest_framework import status
from rest_framework.response import Response

from items.models import Item
from items.serializers import ItemSerializer


class UpdateItemHelper:
    def handle(self, request, item_id):
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ItemSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.save()
        return Response(ItemSerializer(item).data, status=status.HTTP_200_OK)
