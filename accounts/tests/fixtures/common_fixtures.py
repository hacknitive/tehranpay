# tests/fixtures/common_fixtures.py

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch
from ...models import Session

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def _create_user(username='testuser', password='testpassword',):
        return User.objects.create_user(username=username, password=password)
    return _create_user

@pytest.fixture
def create_session(db, create_user):
    def _create_session(user=None, revoked=False):
        if not user:
            user = create_user()
        return Session.objects.create(user=user, revoked=revoked)
    return _create_session

@pytest.fixture
def mock_encode_token():
    with patch('authentication.utils.encode_token') as mock:
        yield mock

@pytest.fixture
def mock_decode_token():
    with patch('authentication.utils.decode_token') as mock:
        yield mock

@pytest.fixture
def mock_redis_client():
    with patch('authentication.utils.redis_client_ins') as mock:
        yield mock