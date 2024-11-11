# tests/views/test_login_view.py

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import MagicMock, patch
from ..models import Session
from .fixtures.common_fixtures import api_client, create_user

@pytest.mark.django_db
@patch('accounts.views.LoginView._create_session')
@patch('utils.encode_token')
@patch('utils.redis_client_ins.set_access_token')
def test_login_success(mock_set_access_token, mock_encode_token, mock_create_session, api_client, create_user):
    # Arrange
    url = reverse('login')  # Ensure your URL is named 'login'
    user = create_user(username='testuser', password='testpassword')
    
    # Mock session creation
    mock_session = MagicMock(spec=Session)
    mock_session.id = 'session123'
    mock_create_session.return_value = mock_session
    
    # Mock token encoding
    def encode_token_side_effect(payload):
        return f"token_{payload['type']}"
    mock_encode_token.side_effect = encode_token_side_effect

    data = {
        "username": "testuser",
        "password": "testpassword"
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data['data']
    assert 'refresh' in response.data['data']
    assert response.data['data']['access'] == 'token_access'
    assert response.data['data']['refresh'] == 'token_refresh'
    mock_set_access_token.assert_called_with(token='token_access')


@pytest.mark.django_db
def test_login_invalid_credentials(api_client, create_user):
    # Arrange
    url = reverse('login')  # Ensure your URL is named 'login'
    create_user(username='testuser', password='testpassword')
    
    data = {
        "username": "testuser",
        "password": "wrongpassword"
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['data'] is None
    assert response.data['error'] == "Invalid credentials."

@pytest.mark.django_db
@patch('accounts.views.LoginView._authenticate_user')
def test_login_authentication_failure(mock_authenticate_user, api_client, create_user):
    # Arrange
    url = reverse('login') 
    create_user(username='testuser', password='testpassword')
    mock_authenticate_user.return_value = None

    data = {
        "username": "testuser",
        "password": "testpassword"
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['data'] is None
    assert response.data['error'] == "Invalid credentials."