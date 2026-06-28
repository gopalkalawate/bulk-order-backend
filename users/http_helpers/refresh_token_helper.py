import datetime

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from users.models import User


class RefreshTokenHelper:
    def handle(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        user_id = payload.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        now = datetime.datetime.utcnow()
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': now + datetime.timedelta(minutes=15),
            'iat': now,
        }
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({'access': access_token}, status=status.HTTP_200_OK)
