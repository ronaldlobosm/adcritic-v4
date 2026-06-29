"""
Role-based access control for AdCritic.

Valid roles
-----------
admin      – full access to everything in the admin panel
approver   – can VIEW and APPROVE/REJECT pending content in their assigned sections
editor     – can CREATE/EDIT content in their assigned sections (saves go to 'pending')
advertiser – placeholder: sees only an empty Advertising section
gold       – public site subscriber, no admin access
free       – public site user, no admin access

Content-type keys used throughout: 'catalog', 'posts'
"""
from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

VALID_ROLES = ("admin", "approver", "editor", "advertiser", "gold", "free")
ADMIN_ROLES = ("admin", "approver", "editor", "advertiser")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def has_content_access(user, content_type):
    """
    True if user has *any* access to content of the given type.
    - admin     → always True
    - editor / approver → True if a RoleContentAccess row exists for (user, content_type)
    - everyone else → False
    """
    if not user.is_authenticated:
        return False
    if user.role == "admin":
        return True
    if user.role in ("editor", "approver"):
        from app.models import RoleContentAccess
        return RoleContentAccess.query.filter_by(
            user_id=user.id, content_type=content_type
        ).first() is not None
    return False


def can_edit_content(user, content_type):
    """True if user may create/edit content (admin or editor with access)."""
    if not user.is_authenticated:
        return False
    if user.role == "admin":
        return True
    if user.role == "editor":
        return has_content_access(user, content_type)
    return False


def can_approve_content(user, content_type):
    """True if user may approve/reject pending content (admin or approver with access)."""
    if not user.is_authenticated:
        return False
    if user.role == "admin":
        return True
    if user.role == "approver":
        return has_content_access(user, content_type)
    return False


def content_status_for_save(user):
    """
    Status to assign when user saves a piece of content:
    admin → 'published' (direct publish)
    editor → 'pending'  (needs approval)
    """
    return "published" if user.role == "admin" else "pending"
