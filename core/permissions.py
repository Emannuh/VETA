"""
Permission and authentication utilities for VETA Connect
Handles role-based access control and authorization
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from functools import wraps
from enum import Enum


class UserRole(Enum):
    """User role definitions"""
    LEARNER = 'learner'
    TRAINER = 'trainer'
    ADMIN = 'admin'
    PARTNER = 'partner'
    MENTOR = 'mentor'


class PermissionManager:
    """Manages and validates user permissions"""
    
    ROLE_PERMISSIONS = {
        UserRole.LEARNER: {
            'view_projects': True,
            'create_project': True,
            'edit_own_project': True,
            'delete_own_project': True,
            'apply_opportunity': True,
            'request_mentor': True,
            'view_leaderboard': True,
            'view_profile': True,
            'edit_profile': True,
            'view_opportunities': True,
            'view_scholarships': True,
        },
        UserRole.TRAINER: {
            'view_projects': True,
            'evaluate_project': True,
            'award_badge': True,
            'recommend_opportunity': True,
            'view_all_profiles': True,
            'trainer_panel': True,
        },
        UserRole.ADMIN: {
            'view_all': True,
            'edit_all': True,
            'delete_all': True,
            'manage_users': True,
            'manage_content': True,
            'view_analytics': True,
        },
        UserRole.PARTNER: {
            'view_leaderboard': True,
            'post_opportunity': True,
            'browse_profiles': True,
            'contact_learners': True,
            'view_applications': True,
        },
        UserRole.MENTOR: {
            'view_profiles': True,
            'accept_mentee': True,
            'provide_guidance': True,
            'recommend_resources': True,
        }
    }
    
    @classmethod
    def has_permission(cls, user, permission: str) -> bool:
        """Check if user has specific permission"""
        if not user or not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Determine user role
        if hasattr(user, 'is_trainer') and user.is_trainer:
            role = UserRole.TRAINER
        elif hasattr(user, 'is_admin') and user.is_admin:
            role = UserRole.ADMIN
        else:
            role = UserRole.LEARNER
        
        permissions = cls.ROLE_PERMISSIONS.get(role, {})
        return permissions.get(permission, False)
    
    @classmethod
    def get_user_permissions(cls, user) -> set:
        """Get all permissions for a user"""
        if not user or not user.is_authenticated:
            return set()
        
        if user.is_superuser:
            return set()  # All permissions
        
        if hasattr(user, 'is_trainer') and user.is_trainer:
            role = UserRole.TRAINER
        elif hasattr(user, 'is_admin') and user.is_admin:
            role = UserRole.ADMIN
        else:
            role = UserRole.LEARNER
        
        return set(cls.ROLE_PERMISSIONS.get(role, {}).keys())


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not PermissionManager.has_permission(request.user, permission):
                raise PermissionDenied('You do not have permission to access this resource')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
                raise PermissionDenied('Authentication required')
            
            user_role = None
            if hasattr(request.user, 'is_trainer') and request.user.is_trainer:
                user_role = UserRole.TRAINER
            elif hasattr(request.user, 'is_admin') and request.user.is_admin:
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.LEARNER
            
            if user_role != role and not request.user.is_superuser:
                raise PermissionDenied(f'This resource requires {role.value} role')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class PermissionMixin(UserPassesTestMixin):
    """Mixin to enforce permissions on class-based views"""
    
    required_permission = None
    required_role = None
    
    def test_func(self):
        """Test if user has required permission"""
        if self.required_permission:
            return PermissionManager.has_permission(self.request.user, self.required_permission)
        
        if self.required_role:
            user_role = None
            if hasattr(self.request.user, 'is_trainer') and self.request.user.is_trainer:
                user_role = UserRole.TRAINER
            elif hasattr(self.request.user, 'is_admin') and self.request.user.is_admin:
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.LEARNER
            
            return user_role == self.required_role
        
        return self.request.user.is_authenticated
    
    def handle_no_permission(self):
        """Handle access denied"""
        raise PermissionDenied('You do not have permission to access this resource')


class ObjectPermissionManager:
    """Manages object-level permissions"""
    
    @staticmethod
    def user_owns_object(user, obj) -> bool:
        """Check if user owns object"""
        return hasattr(obj, 'user') and obj.user == user or \
               hasattr(obj, 'created_by') and obj.created_by == user
    
    @staticmethod
    def can_edit_object(user, obj) -> bool:
        """Check if user can edit object"""
        if user.is_superuser:
            return True
        
        if hasattr(user, 'is_trainer') and user.is_trainer:
            return True
        
        return ObjectPermissionManager.user_owns_object(user, obj)
    
    @staticmethod
    def can_delete_object(user, obj) -> bool:
        """Check if user can delete object"""
        if user.is_superuser:
            return True
        
        return ObjectPermissionManager.user_owns_object(user, obj)
