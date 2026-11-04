import pytest
from django.contrib.auth import get_user_model
User = get_user_model()

@pytest.fixture
def user_student(db):
    return User.objects.create_user(username="aluno1", password="senha123")

