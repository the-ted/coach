---
name: backend
description: Write production-ready Django/DRF backend code with Django ORM, DRF serializers, JWT auth, Django Channels, testing, and proper architecture. Use when creating API endpoints, database models, or backend services.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Django/DRF Backend Development Instructions

When writing backend code, follow these Django/DRF patterns:

## Project Structure

**Always use this Django app structure:**
```
services/backend/
├── apps/
│   ├── authentication/      # User model, JWT auth
│   ├── [feature]/
│   │   ├── models.py       # Django ORM models
│   │   ├── serializers.py  # DRF serializers
│   │   ├── views.py        # API views/viewsets
│   │   ├── urls.py         # URL routing
│   │   ├── services.py     # Business logic (optional)
│   │   ├── permissions.py  # Custom permissions
│   │   └── tests/          # pytest tests
│   └── core/               # Shared utilities
├── [project_name]/         # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py            # ASGI for Channels
└── manage.py
```

**Flow**: URL → View → Serializer → Model → Database

## Django Models

Use Django ORM for all database models:

```python
from django.db import models
from django.utils import timezone
import uuid

class Item(models.Model):
    """Item model with standard fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='items')

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
        ]

    def __str__(self):
        return self.name
```

**Rules:**
- Use UUIDField for primary keys
- Add `db_index=True` for frequently queried fields
- Include `created_at` and `updated_at` timestamps
- Define `Meta` class with `db_table`, `ordering`
- Add custom indexes for common query patterns
- Use `related_name` for reverse relations
- Add docstrings to models

## DRF Serializers

Create separate serializers for different use cases:

```python
from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model."""

    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'owner', 'owner_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate name is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

class ItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating items."""

    class Meta:
        model = Item
        fields = ['name', 'description']

    def create(self, validated_data):
        # Owner is set in the view
        return super().create(validated_data)

class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    class Meta:
        model = Item
        fields = ['id', 'name', 'created_at']
```

**Rules:**
- Separate serializers for list/detail/create/update
- Use `read_only_fields` for computed/auto fields
- Add validation methods with `validate_<field>`
- Use `source` for nested fields
- Document serializers with docstrings

## DRF Views

Use ViewSets for standard CRUD, APIView for custom logic:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Item
from .serializers import ItemSerializer, ItemCreateSerializer, ItemListSerializer
from .permissions import IsOwnerOrAdmin

class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items.

    Provides standard CRUD operations plus custom actions.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Item.objects.select_related('owner').all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ItemListSerializer
        elif self.action == 'create':
            return ItemCreateSerializer
        return ItemSerializer

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(owner=user)

    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate an item."""
        item = self.get_object()
        item.pk = None
        item.name = f"{item.name} (Copy)"
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

**APIView Example:**
```python
from rest_framework.views import APIView

class ItemStatsView(APIView):
    """Get statistics about items."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return item statistics."""
        user = request.user
        items = Item.objects.filter(owner=user)

        stats = {
            'total': items.count(),
            'this_week': items.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count(),
        }

        return Response(stats)
```

**Rules:**
- Use ViewSets for standard CRUD
- Use APIView for custom logic
- Override `get_queryset()` for filtering
- Override `get_serializer_class()` for different serializers per action
- Use `@action` decorator for custom endpoints
- Include docstrings on all views and methods
- Use `perform_create/update/destroy` for side effects

## Authentication (djangorestframework-simplejwt)

**User Model:**
```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
import uuid

class UserManager(BaseUserManager):
    """Manager for User model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPERADMIN)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email authentication."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'
        SUPERADMIN = 'superadmin', 'SuperAdmin'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email
```

**JWT Settings (settings.py):**
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}
```

**Auth URLs:**
```python
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

## Custom Permissions

```python
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to only allow owners or admins to access object."""

    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.is_staff:
            return True

        # Check if object has owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False

class IsSuperAdmin(permissions.BasePermission):
    """Only superadmins can access."""

    def has_permission(self, request, view):
        return request.user.role == 'superadmin'
```

## URL Routing

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, ItemStatsView

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

app_name = 'items'

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', ItemStatsView.as_view(), name='stats'),
]
```

**Main URLs:**
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/items/', include('apps.items.urls')),
]
```

## Django Channels (WebSockets)

**ASGI Configuration:**
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

django_asgi_app = get_asgi_application()

from apps.websockets import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(routing.websocket_urlpatterns)
        )
    ),
})
```

**WebSocket Consumer:**
```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for chat."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Handle disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        """Handle incoming message."""
        message = content.get('message')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.email,
            }
        )

    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send_json({
            'message': event['message'],
            'user': event['user'],
        })
```

**WebSocket Routing:**
```python
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_id>/', consumers.ChatConsumer.as_asgi()),
]
```

## Django Management Commands

```python
from django.core.management.base import BaseCommand
from apps.authentication.models import User

class Command(BaseCommand):
    help = 'Seeds test users for all roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force seed users even in production',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Safety check for production
        if not settings.DEBUG and not force:
            self.stdout.write(
                self.style.WARNING('Skipping: Only runs in DEBUG=True mode')
            )
            return

        # Create test users
        users = [
            {
                'email': 'user@example.com',
                'username': 'testuser',
                'password': 'testpass123',
                'role': User.Role.USER,
            },
            {
                'email': 'admin@example.com',
                'username': 'testadmin',
                'password': 'adminpass123',
                'role': User.Role.ADMIN,
                'is_staff': True,
            },
        ]

        created = 0
        for user_data in users:
            email = user_data.pop('email')
            password = user_data.pop('password')

            user, created_now = User.objects.get_or_create(
                email=email,
                defaults=user_data
            )

            if created_now:
                user.set_password(password)
                user.save()
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {email}')
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f'→ Exists: {email}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSeeding complete: {created} created')
        )
```

## Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration SQL
python manage.py sqlmigrate app_name 0001

# Revert migration
python manage.py migrate app_name 0001
```

## Testing (pytest-django)

**conftest.py:**
```python
import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User

@pytest.fixture
def api_client():
    """Provide API client."""
    return APIClient()

@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )

@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_user(
        email='admin@example.com',
        username='admin',
        password='adminpass123',
        role=User.Role.ADMIN,
        is_staff=True
    )

@pytest.fixture
def auth_client(api_client, user):
    """Provide authenticated API client."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = user
    return api_client
```

**Test Example:**
```python
import pytest
from rest_framework import status
from apps.items.models import Item

@pytest.mark.django_db
class TestItemAPI:
    """Test Item API endpoints."""

    def test_list_items_unauthenticated(self, api_client):
        """Unauthenticated users cannot list items."""
        response = api_client.get('/api/items/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_items_authenticated(self, auth_client, user):
        """Authenticated users can list their items."""
        Item.objects.create(name='Test Item', owner=user)

        response = auth_client.get('/api/items/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_item(self, auth_client):
        """Users can create items."""
        data = {'name': 'New Item', 'description': 'Test'}

        response = auth_client.post('/api/items/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Item'
        assert Item.objects.count() == 1

    def test_create_item_validation(self, auth_client):
        """Validation errors are returned."""
        data = {'name': ''}  # Empty name should fail

        response = auth_client.post('/api/items/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
```

**Run Tests:**
```bash
# Run all tests
pytest

# Run specific test file
pytest apps/items/tests/test_views.py

# Run with coverage
pytest --cov=apps --cov-report=html

# Run in parallel
pytest -n auto
```

## Logging

```python
import logging

logger = logging.getLogger(__name__)

# In views
logger.info(f"User {user.email} created item {item.id}")
logger.error(f"Failed to create item: {str(e)}", exc_info=True)
logger.warning(f"Suspicious activity from {request.META['REMOTE_ADDR']}")
```

## Error Handling

```python
from rest_framework.exceptions import APIException
from rest_framework import status

class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable'
    default_code = 'service_unavailable'

# In views
from rest_framework.exceptions import ValidationError, NotFound

def my_view(request):
    if not some_condition:
        raise ValidationError({'field': 'Error message'})

    obj = get_object_or_404(Model, pk=pk)  # Returns 404 automatically
```

## Dependencies

**requirements.txt:**
```
Django>=4.2.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
django-cors-headers>=4.3.0
channels>=4.0.0
channels-redis>=4.1.0
daphne>=4.0.0
psycopg2-binary>=2.9.9
redis>=5.0.0
gunicorn>=21.2.0
pytest>=7.4.0
pytest-django>=4.5.2
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

## Key Reminders

- ✅ Always use Django ORM models (not SQLModel)
- ✅ Use DRF serializers for validation (not Pydantic)
- ✅ Use ViewSets for standard CRUD, APIView for custom logic
- ✅ Implement proper permissions on all views
- ✅ Use djangorestframework-simplejwt for JWT authentication
- ✅ Create Django management commands for admin tasks
- ✅ Write tests with pytest-django
- ✅ Use Django Channels for WebSocket support
- ✅ Add docstrings to all classes and methods
- ✅ Use `select_related()` and `prefetch_related()` to avoid N+1 queries
- ✅ Always validate user input in serializers
- ✅ Use `get_object_or_404` for single object retrieval
- ✅ Override `get_queryset()` to filter by user/permissions
- ✅ Use transactions for multi-step database operations
- ✅ Log important events and errors
- ✅ Handle errors with appropriate HTTP status codes
