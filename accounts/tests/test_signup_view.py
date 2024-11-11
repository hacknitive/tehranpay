import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from .fixtures.common_fixtures import api_client, create_user

@pytest.mark.django_db
def test_signup_success(api_client):
    # Arrange
    url = reverse('signup')  # Ensure your URL is named 'signup'
    data = {
        "username": "newuser",
        "password": "newpassword123",
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['error'] is None
    assert response.data['message'] == "Operation succeeded."
    assert response.data['data']['username'] == "newuser"
    assert User.objects.filter(username="newuser").exists()

@pytest.mark.django_db
def test_signup_missing_fields(api_client):
    # Arrange
    url = reverse('signup')  # Ensure your URL is named 'signup'
    data = {
        "username": "newuser",
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Adjust based on your serializer's error structure
    assert 'password' in response.data

@pytest.mark.django_db
def test_signup_existing_user(api_client, create_user):
    # Arrange
    url = reverse('signup')  # Ensure your URL is named 'signup'
    create_user(username='existinguser', password='password123')
    data = {
        "username": "existinguser",
        "password": "newpassword123",
    }

    # Act
    response = api_client.post(url, data, format='json')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Adjust based on your serializer's error structure
    assert 'username' in response.data