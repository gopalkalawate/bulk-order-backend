from rest_framework import status
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer


class GetUserHelper:
    def handle(self, request):
        email_id = request.query_params.get('email')
        try:
            user = User.objects.get(email=email_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
