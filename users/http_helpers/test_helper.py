from rest_framework import status
from rest_framework.response import Response


class TestHelper:
    def handle(self, request):
        return Response({'message': 'Hello World'}, status=status.HTTP_200_OK)
