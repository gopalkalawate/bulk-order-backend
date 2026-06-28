import datetime

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response


class LoginHelper:
    def handle(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'error': 'email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        now = datetime.datetime.utcnow()
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': now + datetime.timedelta(minutes=15),
            'iat': now,
        }
        refresh_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': now + datetime.timedelta(days=7),
            'iat': now,
        }

        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({'access': access_token, 'refresh': refresh_token}, status=status.HTTP_200_OK)
