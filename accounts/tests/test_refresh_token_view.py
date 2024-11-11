# tests/views/test_refresh_token_view.py

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from ..models import Session  # Adjust the import based on your app name
from .fixtures.common_fixtures import api_client, create_user, create_session


@pytest.mark.django_db
@patch('utils.decode_token')
def test_refresh_token_invalid(mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('refresh-token')  # Ensure your URL is named 'refresh-token'
    user = create_user(username='testuser3', password='testpassword')
    session = create_session(user=user)
    
    mock_decode_token.side_effect = jwt.InvalidTokenError

    data = {
        "refresh": "invalid_token"
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error'] == "Invalid refresh token."


@pytest.mark.django_db
@patch('utils.decode_token')
def test_refresh_token_wrong_type(mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('refresh-token')  # Ensure your URL is named 'refresh-token'
    user = create_user(username='testuser6', password='testpassword')
    session = create_session(user=user)
    
    wrong_payload = {
        "user_id": user.id,
        "session_id": str(session.id),
        "exp": datetime.utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRATION_SECONDS),
        "type": "access"  # Should be 'refresh'
    }
    refresh_token = jwt.encode(wrong_payload, settings.SECRET_KEY, algorithm='HS256')

    mock_decode_token.return_value = wrong_payload

    data = {
        "refresh": refresh_token
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error'] == "Invalid refresh token."
