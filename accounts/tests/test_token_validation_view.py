# tests/views/test_token_validation_view.py

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
import jwt
from datetime import datetime, timedelta
from ..models import Session  # Adjust based on your app name
from django.conf import settings
from .fixtures.common_fixtures import api_client, create_user, create_session

@pytest.mark.django_db
@patch('utils.decode_token')
@patch('utils.redis_client_ins.get_access_token')
def test_token_validation_valid(mock_get_access_token, mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('token-validation')  # Ensure your URL is named 'token-validation'
    user = create_user(username='testuser', password='testpassword')
    session = create_session(user=user)
    valid_token = 'valid_token'

    mock_get_access_token.return_value = b'valid'
    mock_decode_token.return_value = {
        "user_id": user.id,
        "session_id": str(session.id),
        "exp": datetime.utcnow() + timedelta(seconds=60),
        "type": "access"
    }

    data = {
        "token": valid_token
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['is_valid'] is True
    assert response.data['data']['message'] == "Token is valid."

@pytest.mark.django_db
@patch('utils.decode_token')
@patch('utils.redis_client_ins.get_access_token')
def test_token_validation_invalid_or_expired(mock_get_access_token, mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('token-validation')  # Ensure your URL is named 'token-validation'
    user = create_user(username='testuser', password='testpassword')
    session = create_session(user=user)
    invalid_token = 'invalid_token'

    mock_get_access_token.return_value = None

    data = {
        "token": invalid_token
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['is_valid'] is False
    assert response.data['data']['message'] == "Token is invalid or expired."

@pytest.mark.django_db
@patch('utils.decode_token')
def test_token_validation_expired_signature(mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('token-validation')  # Ensure your URL is named 'token-validation'
    user = create_user(username='testuser', password='testpassword')
    session = create_session(user=user)
    expired_token = 'expired_token'

    mock_decode_token.side_effect = jwt.ExpiredSignatureError

    data = {
        "token": expired_token
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['is_valid'] is False
    assert response.data['data']['message'] == "Token is invalid or expired."

@pytest.mark.django_db
@patch('utils.decode_token')
def test_token_validation_invalid_token_error(mock_decode_token, api_client, create_user, create_session):
    # Arrange
    url = reverse('token-validation')  # Ensure your URL is named 'token-validation'
    user = create_user(username='testuser', password='testpassword')
    session = create_session(user=user)
    invalid_token = 'invalid_token'

    mock_decode_token.side_effect = jwt.InvalidTokenError

    data = {
        "token": invalid_token
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['data']['is_valid'] is False
    assert response.data['data']['message'] == "Token is invalid or expired."