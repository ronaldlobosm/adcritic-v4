from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app,
)
from flask_login import current_user, login_required
from app import db
from datetime import datetime
from app.models import Ad, AdTranslation, Category, Post, PostTranslation, PostCategory, PostComment, AdComment, User, SiteSettings, MediaFile, RoleContentAccess, BannedWord
from app.utils import save_upload_file
from app.email import send_admin_reassignment_email
from app.permissions import has_content_access, can_edit_content, can_approve_content, content_status_for_save
from app.countries import COUNTRIES, countries_sorted
from sqlalchemy.exc import SQLAlchemyError
import stripe
from app.routes.membership import _configure_stripe, _handle_subscription_deleted

admin = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------------------------------------------------------------------
# Bilingual UI strings
# ---------------------------------------------------------------------------

ADMIN_UI = {
    "es": {
        # Navigation
        "nav_content":      "Contenido",
        "nav_catalog":      "Catálogo",
        "nav_criticas":     "Críticas",
        "nav_new_critica":  "+ Nueva crítica",
        "nav_new_post":     "+ Nuevo post",
        "nav_new_comment":  "+ Agregar comentario",
        "nav_posts":        "Publicaciones",
        "nav_courses":      "Cursos",
        "nav_monetization": "Monetización",
        "nav_memberships":  "Membresías",
        "nav_advertising":  "Publicidad",
        "nav_site":         "Sitio",
        "nav_users":        "Usuarios",
        "nav_logout":       "Salir",
        "nav_view_site":    "← Ver sitio",
        "nav_soon":         "(pronto)",
        # Dashboard
        "page_dashboard":   "Panel",
        "stat_entries":     "Entradas en catálogo",
        "stat_users":       "Usuarios registrados",
        "btn_new_entry":    "+ Nueva entrada",
        "btn_view_users":   "Ver usuarios",
        # Catalog list
        "page_catalog":     "Catálogo",
        "th_title":         "Título (ES)",
        "th_brand":         "Marca",
        "th_country":       "País",
        "th_year":          "Año",
        "th_category":      "Categoría",
        "th_actions":       "Acciones",
        "btn_edit":         "Editar",
        "btn_delete":       "Eliminar",
        "confirm_delete":   "¿Eliminar esta entrada? No se puede deshacer.",
        "empty_catalog":    "No hay entradas en el catálogo todavía.",
        # Catalog form
        "page_new_entry":   "Nueva entrada",
        "page_edit_entry":  "Editar entrada",
        "section_general":  "Datos generales",
        "section_es":       "Contenido en Español",
        "section_en":       "Content in English",
        "label_brand":      "Marca",
        "label_slug":       "Slug",
        "hint_slug_edit":   "(cambiar el slug rompe URLs existentes)",
        "hint_slug_pattern":"Solo letras minúsculas, números y guiones",
        "label_country":    "País",
        "label_year":       "Año",
        "label_category":   "Categoría",
        "label_youtube":    "YouTube ID",
        "hint_youtube":     "ej. dQw4w9WgXcQ (solo el ID, no la URL completa)",
        "label_title_es":   "Título (ES)",
        "label_analysis_es":"Análisis (ES)",
        "hint_html":        "Se acepta HTML básico (<p>, <em>, <strong>)",
        "label_title_en":   "Title (EN)",
        "label_analysis_en":"Analysis (EN)",
        "hint_html_en":     "Basic HTML accepted (<p>, <em>, <strong>)",
        "btn_save":         "Guardar cambios",
        "btn_create_entry": "Crear entrada",
        "btn_cancel":       "Cancelar",
        # Users list
        "page_users":       "Usuarios",
        "btn_new_user":     "+ Nuevo usuario",
        "th_email":         "Email",
        "th_role":          "Rol",
        "th_active":        "Activo",
        "th_registered":    "Registrado",
        "label_you":        "tú",
        "active_yes":       "Sí",
        "active_no":        "No",
        # User form
        "page_new_user":    "Nuevo usuario",
        "page_edit_user":   "Editar usuario",
        "label_email":      "Correo electrónico",
        "label_password":   "Contraseña",
        "label_new_password":"Nueva contraseña",
        "hint_password_edit":"Dejar vacío para no cambiar",
        "label_role":       "Rol",
        "label_active":     "Cuenta activa",
        "btn_create_user":  "Crear usuario",
        # Roles
        "role_admin":       "Administrador",
        "role_approver":    "Aprobador",
        "role_editor":      "Editor",
        "role_advertiser":  "Anunciante",
        "role_gold":        "Gold",
        "role_free":        "Free",
        "label_content_access": "Secciones de contenido",
        "hint_content_access":  "Secciones que puede ver y gestionar este usuario",
        "access_catalog":   "Catálogo",
        "access_posts":     "Publicaciones",
        # Status labels
        "status_pending":   "Pendiente",
        "status_rejected":  "Rechazado",
        "th_status":        "Estado",
        "th_creator":       "Creado por",
        # Approval queue
        "nav_approval":     "Cola de aprobación",
        "page_approval":    "Cola de aprobación",
        "approval_ads":     "Anuncios pendientes",
        "approval_posts":   "Publicaciones pendientes",
        "approval_empty":   "No hay contenido pendiente de aprobación.",
        "btn_approve":      "Aprobar",
        "btn_reject":       "Rechazar",
        "label_rejection_note": "Motivo del rechazo",
        "hint_rejection_note":  "Visible para el editor que creó el contenido",
        "ok_approved":      "Contenido aprobado y publicado.",
        "ok_rejected":      "Contenido rechazado.",
        "err_no_approve_perm": "No tienes permiso para aprobar este contenido.",
        # Flash messages
        "err_missing":      "Completa todos los campos obligatorios.",
        "err_year":         "El año debe ser un número.",
        "err_slug":         "Ese slug ya está en uso por otra entrada.",
        "err_email_taken":  "Ese email ya está registrado.",
        "err_invalid_role": "Rol inválido.",
        "err_last_admin":   "No puedes desactivar o cambiar el rol al único administrador.",
        "err_no_permission":"Solo los administradores pueden modificar usuarios.",
        "ok_entry_created":   "Entrada creada.",
        "ok_entry_updated":   "Entrada actualizada.",
        "ok_entry_deleted":   "Entrada eliminada.",
        "ok_user_created":      "Usuario creado.",
        "ok_user_updated":      "Usuario actualizado.",
        "ok_user_deleted":      "Usuario eliminado.",
        "confirm_delete_user":  "¿Eliminar este usuario permanentemente? No se puede deshacer.",
        "btn_cancel_subscription": "Cancelar suscripción de Stripe",
        "confirm_cancel_subscription": "¿Cancelar la suscripción de Stripe de este usuario? Pasará a plan Gratuito de inmediato. No se puede deshacer.",
        "label_subscription": "Suscripción",
        # Categories
        "nav_categories":     "Categorías de crítica",
        "page_categories":    "Categorías",
        "btn_new_category":   "+ Nueva categoría",
        "page_new_category":  "Nueva categoría",
        "page_edit_category": "Editar categoría",
        "label_name_es":      "Nombre en español",
        "label_name_en":      "Nombre en inglés",
        "th_name_es":         "Nombre ES",
        "th_name_en":         "Nombre EN",
        "th_entries":         "Entradas",
        "confirm_delete_cat": "¿Eliminar esta categoría? Las entradas no se borran.",
        "empty_categories":   "No hay categorías todavía.",
        "btn_create_category":"Crear categoría",
        "ok_cat_created":     "Categoría creada.",
        "ok_cat_updated":     "Categoría actualizada.",
        "ok_cat_deleted":     "Categoría eliminada.",
        "err_cat_name_taken": "Ya existe una categoría con ese nombre.",
        # Catalog form updated fields
        "label_categories":   "Categorías",
        "label_country":      "País",
        "hint_categories":    "Selecciona una o varias",
        # Posts
        "nav_posts":              "Publicaciones",
        "nav_post_categories":    "Categorías de post",
        "page_posts":             "Publicaciones",
        "btn_new_post":           "+ Nueva publicación",
        "page_new_post":          "Nueva publicación",
        "page_edit_post":         "Editar publicación",
        "th_post_title":          "Título",
        "th_author":              "Autor",
        "th_premium":             "Gold",
        "th_status":              "Estado",
        "status_published":       "Publicado",
        "status_draft":           "Borrador",
        "label_cover_url":        "URL de imagen de portada",
        "hint_cover_url":         "URL directa a la imagen (1200×630 recomendado)",
        "label_is_premium":       "Exclusivo para Gold",
        "label_is_featured":      "¿Destacada?",
        "hint_featured":          "Puede aparecer aleatoriamente en la portada.",
        "ok_featured_updated":    "Estado destacado actualizado.",
        "label_critique_cover":   "Imagen de portada para las críticas Gold",
        "hint_critique_cover":    "Si se define, reemplaza el video del anuncio como cabecera en TODAS las críticas Gold de este anuncio. Solo se cambia desde aquí. Tamaño recomendado: 1920×800px.",
        "label_published_at":     "Fecha de publicación",
        "hint_published_at":      "Dejar vacío para guardar como borrador",
        "label_post_categories":  "Categorías de la noticia",
        "label_excerpt_es":       "Resumen (ES)",
        "label_excerpt_en":       "Excerpt (EN)",
        "label_body_es":          "Cuerpo (ES)",
        "label_body_en":          "Body (EN)",
        "hint_excerpt":           "2-3 oraciones para la card de vista de lista",
        "confirm_delete_post":    "¿Eliminar esta publicación? No se puede deshacer.",
        "empty_posts":            "No hay publicaciones todavía.",
        "btn_create_post":        "Crear publicación",
        "ok_post_created":        "Publicación creada.",
        "ok_post_updated":        "Publicación actualizada.",
        "ok_post_deleted":        "Publicación eliminada.",
        "err_post_slug":          "Ese slug ya está en uso por otra publicación.",
        # Post categories
        "page_post_categories":      "Categorías de noticias",
        "btn_new_post_category":     "+ Nueva categoría",
        "page_new_post_category":    "Nueva categoría de noticias",
        "page_edit_post_category":   "Editar categoría de noticias",
        "confirm_delete_post_cat":   "¿Eliminar esta categoría? Las publicaciones no se borran.",
        "empty_post_categories":     "No hay categorías de noticias todavía.",
        "btn_create_post_category":  "Crear categoría",
        "ok_post_cat_created":       "Categoría de noticias creada.",
        "ok_post_cat_updated":       "Categoría de noticias actualizada.",
        "ok_post_cat_deleted":       "Categoría de noticias eliminada.",
        "err_post_cat_name_taken":   "Ya existe una categoría de noticias con ese nombre.",
        # SEO
        "section_seo":           "SEO",
        "label_meta_title":      "Meta título",
        "hint_meta_title":       "Si está vacío, se usa el título del contenido",
        "label_meta_desc":       "Meta descripción",
        "hint_meta_desc":        "Máx. 160 caracteres — si está vacío se usa el excerpt/análisis",
        # Site settings
        "nav_seo":               "SEO",
        "page_seo_settings":     "Configuración SEO",
        "label_site_name":       "Nombre del sitio",
        "label_description_es":  "Descripción del sitio (ES)",
        "label_description_en":  "Descripción del sitio (EN)",
        "label_site_url":        "URL del sitio",
        "hint_site_url":         "ej. https://adcritic.com — sin barra al final",
        "ok_settings_saved":     "Configuración guardada.",
        # Media
        "nav_media":             "Gestor de archivos",
        "page_media":            "Gestor de archivos",
        "btn_upload_file":       "Subir archivo",
        "btn_select_library":    "Seleccionar de biblioteca",
        "btn_upload_new":        "Subir nueva imagen",
        "th_file":               "Archivo",
        "th_type":               "Tipo",
        "th_size":               "Tamaño",
        "th_uploader":           "Subido por",
        "th_date":               "Fecha",
        "confirm_delete_file":   "¿Eliminar este archivo? No se puede deshacer.",
        "empty_media":           "No hay archivos subidos todavía.",
        "label_video_source":    "Fuente de video",
        "video_source_none":     "— Sin video —",
        "video_source_youtube":  "YouTube",
        "video_source_vimeo":    "Vimeo",
        "video_source_upload":   "Archivo subido",
        "label_video_id":        "ID de video",
        "hint_youtube_id":       "ej. dQw4w9WgXcQ (solo el ID)",
        "hint_vimeo_id":         "ej. 148751763 (solo el ID)",
        "label_subtitle_es":     "Subtítulos ES (.vtt)",
        "label_subtitle_en":     "Subtítulos EN (.vtt)",
        "hint_subtitle":         "Opcional — archivo WebVTT para el reproductor",
        # Publish / review actions
        "btn_publish":           "Publicar",
        "btn_unpublish":         "Despublicar",
        "btn_draft":             "Regresar a borrador",
        "btn_review":            "Revisar",
        "btn_approve_publish":   "Aprobar y publicar",
        "ok_published":          "Contenido publicado.",
        "ok_unpublished":        "Contenido despublicado.",
        "ok_to_draft":           "Contenido regresado a borrador.",
        "label_review_actions":  "Acciones de revisión",
        # Comment moderation
        "nav_comments":        "Comentarios",
        "page_comments":       "Moderación de comentarios",
        "tab_all":             "Todos",
        "tab_approved":        "Aprobados",
        "tab_pending":         "Pendientes",
        "tab_spam":            "Spam",
        "th_comment":          "Comentario",
        "th_post_link":        "Publicación",
        "btn_approve_comment": "Aprobar",
        "btn_pend_comment":    "Pendiente",
        "btn_spam_comment":    "Spam",
        "bulk_action_label":   "Acción masiva:",
        "bulk_apply":          "Aplicar",
        "bulk_approve":        "Aprobar seleccionados",
        "bulk_pend":           "Poner en pendiente",
        "bulk_spam":           "Marcar como spam",
        "bulk_delete":         "Eliminar seleccionados",
        "empty_comments":      "No hay comentarios en esta categoría.",
        "ok_comment_updated":  "Comentario actualizado.",
        "ok_comments_updated": "{n} comentarios actualizados.",
        "ok_comment_deleted":  "Comentario eliminado.",
        "status_approved":     "Aprobado",
        "status_spam":         "Spam",
        "confirm_delete_comment": "¿Eliminar este comentario permanentemente?",
        # Banned words
        "nav_banned_words":    "Palabras filtradas",
        "page_banned_words":   "Palabras filtradas",
        "th_word":             "Palabra",
        "th_language":         "Idioma",
        "label_word":          "Palabra",
        "label_word_lang":     "Idioma",
        "lang_all":            "Todas",
        "lang_es":             "Español",
        "lang_en":             "Inglés",
        "confirm_delete_word": "¿Eliminar esta palabra de la lista?",
        "empty_banned_words":  "No hay palabras filtradas todavía.",
        "btn_add_word":        "+ Agregar palabra",
        "ok_word_added":       "Palabra agregada.",
        "ok_word_deleted":     "Palabra eliminada.",
        "err_word_exists":     "Esa palabra ya está en la lista.",
        "err_word_required":   "La palabra no puede estar vacía.",
    },
    "en": {
        "nav_content":      "Content",
        "nav_catalog":      "Catalog",
        "nav_criticas":     "Critiques",
        "nav_new_critica":  "+ New critique",
        "nav_new_post":     "+ New post",
        "nav_new_comment":  "+ Add comment",
        "nav_posts":        "Posts",
        "nav_courses":      "Courses",
        "nav_monetization": "Monetization",
        "nav_memberships":  "Memberships",
        "nav_advertising":  "Advertising",
        "nav_site":         "Site",
        "nav_users":        "Users",
        "nav_logout":       "Sign out",
        "nav_view_site":    "← View site",
        "nav_soon":         "(soon)",
        "page_dashboard":   "Dashboard",
        "stat_entries":     "Catalog entries",
        "stat_users":       "Registered users",
        "btn_new_entry":    "+ New entry",
        "btn_view_users":   "View users",
        "page_catalog":     "Catalog",
        "th_title":         "Title (ES)",
        "th_brand":         "Brand",
        "th_country":       "Country",
        "th_year":          "Year",
        "th_category":      "Category",
        "th_actions":       "Actions",
        "btn_edit":         "Edit",
        "btn_delete":       "Delete",
        "confirm_delete":   "Delete this entry? This cannot be undone.",
        "empty_catalog":    "No catalog entries yet.",
        "page_new_entry":   "New entry",
        "page_edit_entry":  "Edit entry",
        "section_general":  "General info",
        "section_es":       "Contenido en Español",
        "section_en":       "Content in English",
        "label_brand":      "Brand",
        "label_slug":       "Slug",
        "hint_slug_edit":   "(changing the slug breaks existing URLs)",
        "hint_slug_pattern":"Lowercase letters, numbers and hyphens only",
        "label_country":    "Country",
        "label_year":       "Year",
        "label_category":   "Category",
        "label_youtube":    "YouTube ID",
        "hint_youtube":     "e.g. dQw4w9WgXcQ (ID only, not the full URL)",
        "label_title_es":   "Título (ES)",
        "label_analysis_es":"Análisis (ES)",
        "hint_html":        "Basic HTML accepted (<p>, <em>, <strong>)",
        "label_title_en":   "Title (EN)",
        "label_analysis_en":"Analysis (EN)",
        "hint_html_en":     "Basic HTML accepted (<p>, <em>, <strong>)",
        "btn_save":         "Save changes",
        "btn_create_entry": "Create entry",
        "btn_cancel":       "Cancel",
        "page_users":       "Users",
        "btn_new_user":     "+ New user",
        "th_email":         "Email",
        "th_role":          "Role",
        "th_active":        "Active",
        "th_registered":    "Registered",
        "label_you":        "you",
        "active_yes":       "Yes",
        "active_no":        "No",
        "page_new_user":    "New user",
        "page_edit_user":   "Edit user",
        "label_email":      "Email address",
        "label_password":   "Password",
        "label_new_password":"New password",
        "hint_password_edit":"Leave blank to keep current password",
        "label_role":       "Role",
        "label_active":     "Account active",
        "btn_create_user":  "Create user",
        # Roles
        "role_admin":       "Administrator",
        "role_approver":    "Approver",
        "role_editor":      "Editor",
        "role_advertiser":  "Advertiser",
        "role_gold":        "Gold",
        "role_free":        "Free",
        "label_content_access": "Content sections",
        "hint_content_access":  "Sections this user can view and manage",
        "access_catalog":   "Catalog",
        "access_posts":     "Posts",
        # Status labels
        "status_pending":   "Pending",
        "status_rejected":  "Rejected",
        "th_status":        "Status",
        "th_creator":       "Created by",
        # Approval queue
        "nav_approval":     "Approval queue",
        "page_approval":    "Approval queue",
        "approval_ads":     "Pending ads",
        "approval_posts":   "Pending posts",
        "approval_empty":   "No content pending approval.",
        "btn_approve":      "Approve",
        "btn_reject":       "Reject",
        "label_rejection_note": "Rejection reason",
        "hint_rejection_note":  "Visible to the editor who created the content",
        "ok_approved":      "Content approved and published.",
        "ok_rejected":      "Content rejected.",
        "err_no_approve_perm": "You don't have permission to approve this content.",
        # Flash messages
        "err_missing":      "Please fill in all required fields.",
        "err_year":         "Year must be a number.",
        "err_slug":         "That slug is already in use by another entry.",
        "err_email_taken":  "That email is already registered.",
        "err_invalid_role": "Invalid role.",
        "err_last_admin":   "You cannot deactivate or change the role of the only administrator.",
        "err_no_permission":"Only administrators can modify users.",
        "ok_entry_created":   "Entry created.",
        "ok_entry_updated":   "Entry updated.",
        "ok_entry_deleted":   "Entry deleted.",
        "ok_user_created":      "User created.",
        "ok_user_updated":      "User updated.",
        "ok_user_deleted":      "User deleted.",
        "confirm_delete_user":  "Delete this user permanently? This cannot be undone.",
        "btn_cancel_subscription": "Cancel Stripe subscription",
        "confirm_cancel_subscription": "Cancel this user's Stripe subscription? They will move to the Free plan immediately. This cannot be undone.",
        "label_subscription": "Subscription",
        # Categories
        "nav_categories":     "Critique categories",
        "page_categories":    "Categories",
        "btn_new_category":   "+ New category",
        "page_new_category":  "New category",
        "page_edit_category": "Edit category",
        "label_name_es":      "Name in Spanish",
        "label_name_en":      "Name in English",
        "th_name_es":         "Name ES",
        "th_name_en":         "Name EN",
        "th_entries":         "Entries",
        "confirm_delete_cat": "Delete this category? Entries will not be deleted.",
        "empty_categories":   "No categories yet.",
        "btn_create_category":"Create category",
        "ok_cat_created":     "Category created.",
        "ok_cat_updated":     "Category updated.",
        "ok_cat_deleted":     "Category deleted.",
        "err_cat_name_taken": "A category with that name already exists.",
        # Catalog form updated fields
        "label_categories":   "Categories",
        "label_country":      "Country",
        "hint_categories":    "Select one or more",
        # Posts
        "nav_posts":              "Posts",
        "nav_post_categories":    "Post categories",
        "page_posts":             "Posts",
        "btn_new_post":           "+ New post",
        "page_new_post":          "New post",
        "page_edit_post":         "Edit post",
        "th_post_title":          "Title",
        "th_author":              "Author",
        "th_premium":             "Gold",
        "th_status":              "Status",
        "status_published":       "Published",
        "status_draft":           "Draft",
        "label_cover_url":        "Cover image URL",
        "hint_cover_url":         "Direct image URL (1200×630 recommended)",
        "label_is_premium":       "Gold exclusive",
        "label_is_featured":      "Featured?",
        "hint_featured":          "May appear randomly on the homepage.",
        "ok_featured_updated":    "Featured status updated.",
        "label_critique_cover":   "Cover image for Gold critiques",
        "hint_critique_cover":    "If set, replaces the ad's video as the header on EVERY Gold critique for this ad. Only changed here. Recommended size: 1920×800px.",
        "label_published_at":     "Publication date",
        "hint_published_at":      "Leave empty to save as draft",
        "label_post_categories":  "Post categories",
        "label_excerpt_es":       "Resumen (ES)",
        "label_excerpt_en":       "Excerpt (EN)",
        "label_body_es":          "Cuerpo (ES)",
        "label_body_en":          "Body (EN)",
        "hint_excerpt":           "2-3 sentences for the list card",
        "confirm_delete_post":    "Delete this post? Cannot be undone.",
        "empty_posts":            "No posts yet.",
        "btn_create_post":        "Create post",
        "ok_post_created":        "Post created.",
        "ok_post_updated":        "Post updated.",
        "ok_post_deleted":        "Post deleted.",
        "err_post_slug":          "That slug is already in use by another post.",
        # Post categories
        "page_post_categories":      "Post categories",
        "btn_new_post_category":     "+ New category",
        "page_new_post_category":    "New post category",
        "page_edit_post_category":   "Edit post category",
        "confirm_delete_post_cat":   "Delete this category? Posts will not be deleted.",
        "empty_post_categories":     "No post categories yet.",
        "btn_create_post_category":  "Create category",
        "ok_post_cat_created":       "Post category created.",
        "ok_post_cat_updated":       "Post category updated.",
        "ok_post_cat_deleted":       "Post category deleted.",
        "err_post_cat_name_taken":   "A post category with that name already exists.",
        # SEO
        "section_seo":           "SEO",
        "label_meta_title":      "Meta title",
        "hint_meta_title":       "Leave blank to use the content title",
        "label_meta_desc":       "Meta description",
        "hint_meta_desc":        "Max 160 chars — leave blank to use the excerpt/analysis",
        # Site settings
        "nav_seo":               "SEO",
        "page_seo_settings":     "SEO Settings",
        "label_site_name":       "Site name",
        "label_description_es":  "Site description (ES)",
        "label_description_en":  "Site description (EN)",
        "label_site_url":        "Site URL",
        "hint_site_url":         "e.g. https://adcritic.com — no trailing slash",
        "ok_settings_saved":     "Settings saved.",
        # Media
        "nav_media":             "Media library",
        "page_media":            "Media library",
        "btn_upload_file":       "Upload file",
        "btn_select_library":    "Select from library",
        "btn_upload_new":        "Upload new image",
        "th_file":               "File",
        "th_type":               "Type",
        "th_size":               "Size",
        "th_uploader":           "Uploaded by",
        "th_date":               "Date",
        "confirm_delete_file":   "Delete this file? Cannot be undone.",
        "empty_media":           "No files uploaded yet.",
        "label_video_source":    "Video source",
        "video_source_none":     "— No video —",
        "video_source_youtube":  "YouTube",
        "video_source_vimeo":    "Vimeo",
        "video_source_upload":   "Uploaded file",
        "label_video_id":        "Video ID",
        "hint_youtube_id":       "e.g. dQw4w9WgXcQ (ID only)",
        "hint_vimeo_id":         "e.g. 148751763 (ID only)",
        "label_subtitle_es":     "Subtitles ES (.vtt)",
        "label_subtitle_en":     "Subtitles EN (.vtt)",
        "hint_subtitle":         "Optional — WebVTT file for the player",
        # Publish / review actions
        "btn_publish":           "Publish",
        "btn_unpublish":         "Unpublish",
        "btn_draft":             "Back to draft",
        "btn_review":            "Review",
        "btn_approve_publish":   "Approve & publish",
        "ok_published":          "Content published.",
        "ok_unpublished":        "Content unpublished.",
        "ok_to_draft":           "Content moved to draft.",
        "label_review_actions":  "Review actions",
        # Comment moderation
        "nav_comments":        "Comments",
        "page_comments":       "Comment moderation",
        "tab_all":             "All",
        "tab_approved":        "Approved",
        "tab_pending":         "Pending",
        "tab_spam":            "Spam",
        "th_comment":          "Comment",
        "th_post_link":        "Post",
        "btn_approve_comment": "Approve",
        "btn_pend_comment":    "Pending",
        "btn_spam_comment":    "Spam",
        "bulk_action_label":   "Bulk action:",
        "bulk_apply":          "Apply",
        "bulk_approve":        "Approve selected",
        "bulk_pend":           "Mark as pending",
        "bulk_spam":           "Mark as spam",
        "bulk_delete":         "Delete selected",
        "empty_comments":      "No comments in this category.",
        "ok_comment_updated":  "Comment updated.",
        "ok_comments_updated": "{n} comments updated.",
        "ok_comment_deleted":  "Comment deleted.",
        "status_approved":     "Approved",
        "status_spam":         "Spam",
        "confirm_delete_comment": "Permanently delete this comment?",
        # Banned words
        "nav_banned_words":    "Filter words",
        "page_banned_words":   "Filter words",
        "th_word":             "Word",
        "th_language":         "Language",
        "label_word":          "Word",
        "label_word_lang":     "Language",
        "lang_all":            "All",
        "lang_es":             "Spanish",
        "lang_en":             "English",
        "confirm_delete_word": "Remove this word from the list?",
        "empty_banned_words":  "No filter words yet.",
        "btn_add_word":        "+ Add word",
        "ok_word_added":       "Word added.",
        "ok_word_deleted":     "Word deleted.",
        "err_word_exists":     "That word is already in the list.",
        "err_word_required":   "Word cannot be empty.",
    },
}


def get_admin_lang():
    return session.get("admin_lang", "es")


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder al panel.", "info")
            return redirect(url_for("auth.login_es"))
        if not current_user.is_staff:
            flash("No tienes permiso para acceder a esta área.", "error")
            return redirect(url_for("main.gallery_es"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Language toggle
# ---------------------------------------------------------------------------

@admin.route("/lang/<lang>")
@admin_required
def set_lang(lang):
    if lang in ("es", "en"):
        session["admin_lang"] = lang
    return redirect(request.referrer or url_for("admin.dashboard"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin.route("/")
@admin_required
def dashboard():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    return render_template(
        "admin/dashboard.html",
        lang=lang, ui=ui,
        active="dashboard",
        ad_count=Ad.query.count(),
        user_count=User.query.count(),
    )


# ---------------------------------------------------------------------------
# Catalog list
# ---------------------------------------------------------------------------

@admin.route("/catalogo/")
@admin_required
def catalog_list():
    if not has_content_access(current_user, "catalog"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    ads = Ad.query.order_by(Ad.year.desc(), Ad.id.desc()).all()
    return render_template(
        "admin/catalog.html", lang=lang, ui=ui, active="catalog",
        ads=ads, countries=COUNTRIES,
    )


# ---------------------------------------------------------------------------
# Catalog create
# ---------------------------------------------------------------------------

@admin.route("/catalogo/nuevo", methods=["GET", "POST"])
@admin_required
def catalog_create():
    if not can_edit_content(current_user, "catalog"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    all_categories = Category.query.order_by(Category.name_es).all()
    if request.method == "POST":
        if _save_ad(None, ui) is None:
            flash(ui["ok_entry_created"], "success")
            return redirect(url_for("admin.catalog_list"))
    return render_template(
        "admin/catalog_form.html", lang=lang, ui=ui, active="catalog",
        ad=None, action="create",
        all_categories=all_categories,
        countries_list=countries_sorted(lang),
        is_readonly=False,
        can_approve=False,
    )


# ---------------------------------------------------------------------------
# Catalog edit
# ---------------------------------------------------------------------------

@admin.route("/catalogo/<int:ad_id>/editar", methods=["GET", "POST"])
@admin_required
def catalog_edit(ad_id):
    if not has_content_access(current_user, "catalog"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    ad = Ad.query.get_or_404(ad_id)
    all_categories = Category.query.order_by(Category.name_es).all()
    is_readonly = (current_user.role == "approver")
    if request.method == "POST":
        if is_readonly:
            from flask import abort; abort(403)
        if _save_ad(ad, ui) is None:
            flash(ui["ok_entry_updated"], "success")
            return redirect(url_for("admin.catalog_list"))
    can_approve = can_approve_content(current_user, "catalog")
    return render_template(
        "admin/catalog_form.html", lang=lang, ui=ui, active="catalog",
        ad=ad, action="edit",
        all_categories=all_categories,
        countries_list=countries_sorted(lang),
        is_readonly=is_readonly,
        can_approve=can_approve,
    )


@admin.route("/catalogo/<int:ad_id>/destacado", methods=["POST"])
@admin_required
def catalog_featured(ad_id):
    if not can_approve_content(current_user, "catalog"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    ad = Ad.query.get_or_404(ad_id)
    ad.is_featured = request.form.get("is_featured") == "1"
    db.session.commit()
    flash(ui["ok_featured_updated"], "success")
    return redirect(url_for("admin.catalog_edit", ad_id=ad.id))


# ---------------------------------------------------------------------------
# Catalog delete
# ---------------------------------------------------------------------------

@admin.route("/catalogo/<int:ad_id>/eliminar", methods=["POST"])
@admin_required
def catalog_delete(ad_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    ad = Ad.query.get_or_404(ad_id)
    db.session.delete(ad)
    db.session.commit()
    flash(ui["ok_entry_deleted"], "success")
    return redirect(url_for("admin.catalog_list"))


# ---------------------------------------------------------------------------
# Users list
# ---------------------------------------------------------------------------

@admin.route("/usuarios/")
@admin_required
def users_list():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", lang=lang, ui=ui, active="users", users=users, roles=User.ROLES)


# ---------------------------------------------------------------------------
# User create
# ---------------------------------------------------------------------------

@admin.route("/usuarios/nuevo", methods=["GET", "POST"])
@admin_required
def user_create():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if current_user.role != "admin":
        flash(ui["err_no_permission"], "error")
        return redirect(url_for("admin.users_list"))

    if request.method == "POST":
        if _save_user(None, ui) is None:
            flash(ui["ok_user_created"], "success")
            return redirect(url_for("admin.users_list"))

    return render_template("admin/user_form.html", lang=lang, ui=ui, active="users",
                           user=None, action="create", user_access=set())


# ---------------------------------------------------------------------------
# User edit
# ---------------------------------------------------------------------------

@admin.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@admin_required
def user_edit(user_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if current_user.role != "admin":
        flash(ui["err_no_permission"], "error")
        return redirect(url_for("admin.users_list"))

    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        if _save_user(user, ui) is None:
            flash(ui["ok_user_updated"], "success")
            return redirect(url_for("admin.users_list"))

    user_access = {a.content_type for a in user.content_access.all()}
    return render_template("admin/user_form.html", lang=lang, ui=ui, active="users",
                           user=user, action="edit", user_access=user_access)


# ---------------------------------------------------------------------------
# User delete
# ---------------------------------------------------------------------------

@admin.route("/usuarios/<int:user_id>/eliminar", methods=["POST"])
@admin_required
def user_delete(user_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if current_user.role != "admin":
        flash(ui["err_no_permission"], "error")
        return redirect(url_for("admin.users_list"))

    user = User.query.get_or_404(user_id)

    # Prevent self-deletion
    if user.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta." if lang == "es"
              else "You cannot delete your own account.", "error")
        return redirect(url_for("admin.users_list"))

    owner = User.query.filter_by(email="admin@adcritic.com").first() or current_user
    deleted_user_email = user.email
    posts_count = Post.query.filter_by(author_id=user.id).count()
    ads_count = Ad.query.filter_by(created_by_id=user.id).count()
    try:
        PostComment.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        AdComment.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        RoleContentAccess.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        Post.query.filter_by(author_id=user.id).update(
            {
                "author_id": owner.id,
                "status": "draft",
                "published_at": None,
                "rejection_note": "Reasignado a admin tras eliminar usuario.",
            },
            synchronize_session=False,
        )
        Ad.query.filter_by(created_by_id=user.id).update(
            {
                "created_by_id": owner.id,
                "status": "draft",
                "published_at": None,
                "rejection_note": "Reasignado a admin tras eliminar usuario.",
            },
            synchronize_session=False,
        )
        MediaFile.query.filter_by(uploaded_by=user.id).update(
            {"uploaded_by": owner.id},
            synchronize_session=False,
        )

        db.session.delete(user)
        db.session.commit()
        if posts_count or ads_count:
            send_admin_reassignment_email(
                owner,
                deleted_user_email,
                posts_count=posts_count,
                ads_count=ads_count,
            )
        flash(ui["ok_user_deleted"], "success")
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error("User delete failed for %s: %s", user.email, exc)
        flash("No se pudo eliminar el usuario." if lang == "es"
              else "Could not delete user.", "error")
    return redirect(url_for("admin.users_list"))


# ---------------------------------------------------------------------------
# User: cancel Stripe subscription
# ---------------------------------------------------------------------------

@admin.route("/usuarios/<int:user_id>/cancelar-suscripcion", methods=["POST"])
@admin_required
def user_cancel_subscription(user_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if current_user.role != "admin":
        flash(ui["err_no_permission"], "error")
        return redirect(url_for("admin.users_list"))

    user = User.query.get_or_404(user_id)

    if not user.stripe_subscription_id:
        flash(
            "Este usuario no tiene una suscripción de Stripe activa." if lang == "es"
            else "This user has no active Stripe subscription.", "error",
        )
        return redirect(url_for("admin.user_edit", user_id=user.id))

    _configure_stripe()
    try:
        subscription = stripe.Subscription.delete(user.stripe_subscription_id)
    except stripe.StripeError as exc:
        current_app.logger.error(
            f"Admin subscription cancel failed for user {user.id}: {exc}"
        )
        flash(
            "No se pudo cancelar la suscripción en Stripe." if lang == "es"
            else "Could not cancel the Stripe subscription.", "error",
        )
        return redirect(url_for("admin.user_edit", user_id=user.id))

    # Reuse the same downgrade logic the webhook uses, so both paths stay in sync.
    _handle_subscription_deleted(subscription)

    flash(
        "Suscripción cancelada. El usuario ha pasado a plan Gratuito." if lang == "es"
        else "Subscription cancelled. The user is now on the Free plan.", "success",
    )
    return redirect(url_for("admin.user_edit", user_id=user.id))


# ---------------------------------------------------------------------------
# Shared form handlers
# ---------------------------------------------------------------------------

def _save_ad(existing_ad, ui):
    f = request.form
    slug               = f.get("slug", "").strip()
    brand              = f.get("brand", "").strip()
    country            = f.get("country", "").strip()
    year               = f.get("year", "").strip()
    video_source_type  = f.get("video_source_type", "").strip() or None
    video_source_value = f.get("video_source_value", "").strip() or None
    title_es           = f.get("title_es", "").strip()
    analysis_es        = f.get("analysis_text_es", "").strip()
    title_en           = f.get("title_en", "").strip()
    analysis_en        = f.get("analysis_text_en", "").strip()
    meta_title_es      = f.get("meta_title_es", "").strip() or None
    meta_desc_es       = f.get("meta_description_es", "").strip() or None
    meta_title_en      = f.get("meta_title_en", "").strip() or None
    meta_desc_en       = f.get("meta_description_en", "").strip() or None
    is_premium         = f.get("is_premium") == "1"
    is_featured        = f.get("is_featured") == "1"
    critique_cover_image_url = f.get("critique_cover_image_url", "").strip() or None
    published_at_raw   = f.get("published_at", "").strip()
    form_action        = f.get("form_action", "").strip()  # 'publish' | 'draft' | 'review'
    raw_cat_ids        = f.getlist("category_ids")
    category_ids       = [int(i) for i in raw_cat_ids if i.isdigit()]

    if not all([slug, brand, country, year, title_es, title_en]):
        flash(ui["err_missing"], "error")
        return "missing"

    if not year.isdigit():
        flash(ui["err_year"], "error")
        return "year"

    conflict = Ad.query.filter_by(slug=slug).first()
    if conflict and (existing_ad is None or conflict.id != existing_ad.id):
        flash(ui["err_slug"], "error")
        return "slug"

    # Subtitle file uploads
    sub_es = _handle_subtitle(request.files.get("subtitle_es_file"),
                               existing_ad.subtitle_es if existing_ad else None)
    sub_en = _handle_subtitle(request.files.get("subtitle_en_file"),
                               existing_ad.subtitle_en if existing_ad else None)

    # Video uploaded file
    if video_source_type == "upload":
        vid_file = request.files.get("video_file")
        if vid_file and vid_file.filename:
            mf, err = save_upload_file(vid_file, allowed_types={"video"})
            if mf:
                video_source_value = mf.url

    # Critique cover image (quick-upload from form)
    cover_file = request.files.get("critique_cover_image_file")
    if cover_file and cover_file.filename:
        mf, err = save_upload_file(cover_file, allowed_types={"image"})
        if mf:
            critique_cover_image_url = mf.url

    # For backward compat: keep youtube_id in sync
    legacy_youtube = video_source_value if video_source_type == "youtube" else (
        existing_ad.youtube_id if existing_ad else ""
    )

    # Parse publish date
    published_at = None
    if published_at_raw:
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                published_at = datetime.strptime(published_at_raw, fmt)
                break
            except ValueError:
                pass

    # Determine status from sidebar action button
    if form_action == "publish" and current_user.role in ("admin", "approver"):
        new_status = "published"
        if not published_at:
            published_at = datetime.utcnow()
    elif form_action == "draft":
        new_status = "draft"
    elif form_action == "review":
        new_status = "pending"
    else:
        new_status = content_status_for_save(current_user)

    selected_categories = Category.query.filter(Category.id.in_(category_ids)).all()

    if existing_ad is None:
        ad = Ad(slug=slug, brand=brand, country=country, year=int(year),
                youtube_id=legacy_youtube or "",
                video_source_type=video_source_type,
                video_source_value=video_source_value,
                subtitle_es=sub_es, subtitle_en=sub_en,
                is_premium=is_premium,
                is_featured=is_featured,
                critique_cover_image_url=critique_cover_image_url,
                published_at=published_at,
                status=new_status,
                created_by_id=current_user.id)
        db.session.add(ad)
        db.session.flush()
    else:
        ad = existing_ad
        ad.slug, ad.brand, ad.country = slug, brand, country
        ad.year = int(year)
        ad.youtube_id = legacy_youtube or ad.youtube_id or ""
        ad.video_source_type  = video_source_type
        ad.video_source_value = video_source_value
        ad.subtitle_es = sub_es
        ad.subtitle_en = sub_en
        ad.is_premium = is_premium
        ad.is_featured = is_featured
        ad.critique_cover_image_url = critique_cover_image_url
        ad.published_at = published_at
        ad.status = new_status

    ad.categories = selected_categories

    for lng, title, analysis, mt, md in [
        ("es", title_es, analysis_es, meta_title_es, meta_desc_es),
        ("en", title_en, analysis_en, meta_title_en, meta_desc_en),
    ]:
        t = ad.translations.filter_by(language=lng).first()
        if t is None:
            db.session.add(AdTranslation(
                ad_id=ad.id, language=lng, title=title, analysis_text=analysis,
                meta_title=mt, meta_description=md,
            ))
        else:
            t.title, t.analysis_text = title, analysis
            t.meta_title, t.meta_description = mt, md

    db.session.commit()
    return None


def _handle_subtitle(file_storage, existing_filename):
    """Upload subtitle if provided, else return existing filename."""
    if file_storage and file_storage.filename:
        mf, err = save_upload_file(file_storage, allowed_types={"subtitle"})
        if mf:
            return mf.filename
    return existing_filename


# ---------------------------------------------------------------------------
# Categories list
# ---------------------------------------------------------------------------

@admin.route("/categorias/")
@admin_required
def categories_list():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    categories = Category.query.order_by(Category.name_es).all()
    return render_template(
        "admin/categories.html", lang=lang, ui=ui,
        active="categories", categories=categories,
    )


@admin.route("/categorias/nueva", methods=["GET", "POST"])
@admin_required
def category_create():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if request.method == "POST":
        if _save_category(None, ui) is None:
            flash(ui["ok_cat_created"], "success")
            return redirect(url_for("admin.categories_list"))
    return render_template(
        "admin/category_form.html", lang=lang, ui=ui,
        active="categories", category=None, action="create",
    )


@admin.route("/categorias/<int:cat_id>/editar", methods=["GET", "POST"])
@admin_required
def category_edit(cat_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    category = Category.query.get_or_404(cat_id)
    if request.method == "POST":
        if _save_category(category, ui) is None:
            flash(ui["ok_cat_updated"], "success")
            return redirect(url_for("admin.categories_list"))
    return render_template(
        "admin/category_form.html", lang=lang, ui=ui,
        active="categories", category=category, action="edit",
    )


@admin.route("/categorias/<int:cat_id>/eliminar", methods=["POST"])
@admin_required
def category_delete(cat_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    category = Category.query.get_or_404(cat_id)
    db.session.delete(category)
    db.session.commit()
    flash(ui["ok_cat_deleted"], "success")
    return redirect(url_for("admin.categories_list"))


def _save_category(existing, ui):
    name_es = request.form.get("name_es", "").strip()
    name_en = request.form.get("name_en", "").strip()

    if not name_es or not name_en:
        flash(ui["err_missing"], "error")
        return "missing"

    conflict_es = Category.query.filter_by(name_es=name_es).first()
    if conflict_es and (existing is None or conflict_es.id != existing.id):
        flash(ui["err_cat_name_taken"], "error")
        return "taken"

    if existing is None:
        db.session.add(Category(name_es=name_es, name_en=name_en))
    else:
        existing.name_es = name_es
        existing.name_en = name_en

    db.session.commit()
    return None


# ---------------------------------------------------------------------------
# Posts list
# ---------------------------------------------------------------------------

@admin.route("/publicaciones/bulk", methods=["POST"])
@admin_required
def posts_bulk():
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    action = request.form.get("action", "")
    ids = request.form.getlist("post_ids")
    if not ids or not action:
        flash("Selecciona al menos un post y una acción." if lang == "es" else "Select at least one post and an action.", "error")
        return redirect(url_for("admin.posts_list"))
    posts = Post.query.filter(Post.id.in_([int(i) for i in ids if i.isdigit()])).all()
    if action == "unpublish":
        for p in posts:
            p.status = "draft"
    elif action == "gold":
        for p in posts:
            p.is_premium = True
    elif action == "ungold":
        for p in posts:
            p.is_premium = False
    elif action == "delete":
        for p in posts:
            db.session.delete(p)
    else:
        flash("Acción desconocida." if lang == "es" else "Unknown action.", "error")
        return redirect(url_for("admin.posts_list"))
    db.session.commit()
    flash(f"{len(posts)} post(s) actualizados." if lang == "es" else f"{len(posts)} post(s) updated.", "success")
    return redirect(url_for("admin.posts_list"))


@admin.route("/publicaciones/")
@admin_required
def posts_list():
    if not has_content_access(current_user, "posts"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template(
        "admin/posts.html", lang=lang, ui=ui, active="posts", posts=posts,
    )


@admin.route("/publicaciones/nueva", methods=["GET", "POST"])
@admin_required
def post_create():
    if not can_edit_content(current_user, "posts"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    all_post_categories = PostCategory.query.order_by(PostCategory.name_es).all()
    if request.method == "POST":
        if _save_post(None, ui) is None:
            flash(ui["ok_post_created"], "success")
            return redirect(url_for("admin.posts_list"))
    return render_template(
        "admin/post_form.html", lang=lang, ui=ui, active="posts",
        post=None, action="create", all_post_categories=all_post_categories,
        is_readonly=False,
        can_approve=False,
    )


@admin.route("/publicaciones/<int:post_id>/editar", methods=["GET", "POST"])
@admin_required
def post_edit(post_id):
    if not has_content_access(current_user, "posts"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    post = Post.query.get_or_404(post_id)
    all_post_categories = PostCategory.query.order_by(PostCategory.name_es).all()
    is_readonly = (current_user.role == "approver")
    if request.method == "POST":
        if is_readonly:
            from flask import abort; abort(403)
        if _save_post(post, ui) is None:
            flash(ui["ok_post_updated"], "success")
            return redirect(url_for("admin.posts_list"))
    can_approve = can_approve_content(current_user, "posts")
    return render_template(
        "admin/post_form.html", lang=lang, ui=ui, active="posts",
        post=post, action="edit", all_post_categories=all_post_categories,
        is_readonly=is_readonly,
        can_approve=can_approve,
    )


@admin.route("/publicaciones/<int:post_id>/eliminar", methods=["POST"])
@admin_required
def post_delete(post_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash(ui["ok_post_deleted"], "success")
    return redirect(url_for("admin.posts_list"))


def _save_post(existing_post, ui):
    f = request.form
    slug               = f.get("slug", "").strip()
    cover_image_url    = f.get("cover_image_url", "").strip() or None
    is_premium         = f.get("is_premium") == "1"
    published_at_raw   = f.get("published_at", "").strip()
    video_source_type  = f.get("video_source_type", "").strip() or None
    video_source_value = f.get("video_source_value", "").strip() or None
    title_es           = f.get("title_es", "").strip()
    excerpt_es         = f.get("excerpt_es", "").strip()
    body_es            = f.get("body_es", "").strip()
    title_en           = f.get("title_en", "").strip()
    excerpt_en         = f.get("excerpt_en", "").strip()
    body_en            = f.get("body_en", "").strip()
    meta_title_es      = f.get("meta_title_es", "").strip() or None
    meta_desc_es       = f.get("meta_description_es", "").strip() or None
    meta_title_en      = f.get("meta_title_en", "").strip() or None
    meta_desc_en       = f.get("meta_description_en", "").strip() or None
    raw_cat_ids        = f.getlist("post_category_ids")
    category_ids       = [int(i) for i in raw_cat_ids if i.isdigit()]

    if not all([slug, title_es, excerpt_es, body_es, title_en, excerpt_en, body_en]):
        flash(ui["err_missing"], "error")
        return "missing"

    conflict = Post.query.filter_by(slug=slug).first()
    if conflict and (existing_post is None or conflict.id != existing_post.id):
        flash(ui["err_post_slug"], "error")
        return "slug"

    published_at = None
    if published_at_raw:
        try:
            published_at = datetime.strptime(published_at_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            try:
                published_at = datetime.strptime(published_at_raw, "%Y-%m-%d")
            except ValueError:
                pass

    # Subtitle file uploads
    sub_es = _handle_subtitle(request.files.get("subtitle_es_file"),
                               existing_post.subtitle_es if existing_post else None)
    sub_en = _handle_subtitle(request.files.get("subtitle_en_file"),
                               existing_post.subtitle_en if existing_post else None)

    # Uploaded video file
    if video_source_type == "upload":
        vid_file = request.files.get("video_file")
        if vid_file and vid_file.filename:
            mf, err = save_upload_file(vid_file, allowed_types={"video"})
            if mf:
                video_source_value = mf.url

    # Cover image upload (quick-upload from form)
    cover_file = request.files.get("cover_image_file")
    if cover_file and cover_file.filename:
        mf, err = save_upload_file(cover_file, allowed_types={"image"})
        if mf:
            cover_image_url = mf.url

    selected_categories = PostCategory.query.filter(PostCategory.id.in_(category_ids)).all()

    new_status = content_status_for_save(current_user)

    if existing_post is None:
        post = Post(
            slug=slug,
            author_id=current_user.id,
            cover_image_url=cover_image_url,
            video_source_type=video_source_type,
            video_source_value=video_source_value,
            subtitle_es=sub_es, subtitle_en=sub_en,
            is_premium=is_premium,
            published_at=published_at,
            status=new_status,
        )
        db.session.add(post)
        db.session.flush()
    else:
        post = existing_post
        post.slug = slug
        post.cover_image_url = cover_image_url
        post.video_source_type  = video_source_type
        post.video_source_value = video_source_value
        post.subtitle_es = sub_es
        post.subtitle_en = sub_en
        post.is_premium = is_premium
        post.published_at = published_at
        if current_user.role != "admin":
            post.status = new_status

    post.categories = selected_categories

    for lng, title, excerpt, body, mt, md in [
        ("es", title_es, excerpt_es, body_es, meta_title_es, meta_desc_es),
        ("en", title_en, excerpt_en, body_en, meta_title_en, meta_desc_en),
    ]:
        t = post.translations.filter_by(language=lng).first()
        if t is None:
            db.session.add(PostTranslation(
                post_id=post.id, language=lng,
                title=title, excerpt=excerpt, body=body,
                meta_title=mt, meta_description=md,
            ))
        else:
            t.title, t.excerpt, t.body = title, excerpt, body
            t.meta_title, t.meta_description = mt, md

    db.session.commit()
    return None


# ---------------------------------------------------------------------------
# Post categories
# ---------------------------------------------------------------------------

@admin.route("/publicaciones/categorias/")
@admin_required
def post_categories_list():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    categories = PostCategory.query.order_by(PostCategory.name_es).all()
    return render_template(
        "admin/post_categories.html", lang=lang, ui=ui,
        active="post_categories", categories=categories,
    )


@admin.route("/publicaciones/categorias/nueva", methods=["GET", "POST"])
@admin_required
def post_category_create():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    if request.method == "POST":
        if _save_post_category(None, ui) is None:
            flash(ui["ok_post_cat_created"], "success")
            return redirect(url_for("admin.post_categories_list"))
    return render_template(
        "admin/post_category_form.html", lang=lang, ui=ui,
        active="post_categories", category=None, action="create",
    )


@admin.route("/publicaciones/categorias/<int:cat_id>/editar", methods=["GET", "POST"])
@admin_required
def post_category_edit(cat_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    category = PostCategory.query.get_or_404(cat_id)
    if request.method == "POST":
        if _save_post_category(category, ui) is None:
            flash(ui["ok_post_cat_updated"], "success")
            return redirect(url_for("admin.post_categories_list"))
    return render_template(
        "admin/post_category_form.html", lang=lang, ui=ui,
        active="post_categories", category=category, action="edit",
    )


@admin.route("/publicaciones/categorias/<int:cat_id>/eliminar", methods=["POST"])
@admin_required
def post_category_delete(cat_id):
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    category = PostCategory.query.get_or_404(cat_id)
    db.session.delete(category)
    db.session.commit()
    flash(ui["ok_post_cat_deleted"], "success")
    return redirect(url_for("admin.post_categories_list"))


def _save_post_category(existing, ui):
    name_es = request.form.get("name_es", "").strip()
    name_en = request.form.get("name_en", "").strip()

    if not name_es or not name_en:
        flash(ui["err_missing"], "error")
        return "missing"

    conflict = PostCategory.query.filter_by(name_es=name_es).first()
    if conflict and (existing is None or conflict.id != existing.id):
        flash(ui["err_post_cat_name_taken"], "error")
        return "taken"

    if existing is None:
        db.session.add(PostCategory(name_es=name_es, name_en=name_en))
    else:
        existing.name_es = name_es
        existing.name_en = name_en

    db.session.commit()
    return None


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------

@admin.route("/aprobacion/")
@admin_required
def approval_queue():
    if current_user.role not in ("admin", "approver"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui   = ADMIN_UI[lang]

    pending_ads   = []
    pending_posts = []
    if has_content_access(current_user, "catalog"):
        pending_ads   = Ad.query.filter_by(status="pending").order_by(Ad.created_at.desc()).all()
    if has_content_access(current_user, "posts"):
        pending_posts = Post.query.filter_by(status="pending").order_by(Post.created_at.desc()).all()

    return render_template(
        "admin/approval.html", lang=lang, ui=ui, active="approval",
        pending_ads=pending_ads, pending_posts=pending_posts,
        countries=COUNTRIES,
    )


@admin.route("/aprobacion/anuncio/<int:ad_id>/aprobar", methods=["POST"])
@admin_required
def approve_ad(ad_id):
    if not can_approve_content(current_user, "catalog"):
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.status         = "published"
    ad.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_approved"], "success")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/aprobacion/anuncio/<int:ad_id>/rechazar", methods=["POST"])
@admin_required
def reject_ad(ad_id):
    if not can_approve_content(current_user, "catalog"):
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.status         = "rejected"
    ad.rejection_note = request.form.get("rejection_note", "").strip() or None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_rejected"], "warning")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/aprobacion/publicacion/<int:post_id>/aprobar", methods=["POST"])
@admin_required
def approve_post(post_id):
    if not can_approve_content(current_user, "posts"):
        from flask import abort; abort(403)
    post = Post.query.get_or_404(post_id)
    post.status         = "published"
    post.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_approved"], "success")
    return redirect(url_for("admin.posts_list"))


@admin.route("/aprobacion/publicacion/<int:post_id>/rechazar", methods=["POST"])
@admin_required
def reject_post(post_id):
    if not can_approve_content(current_user, "posts"):
        from flask import abort; abort(403)
    post = Post.query.get_or_404(post_id)
    post.status         = "rejected"
    post.rejection_note = request.form.get("rejection_note", "").strip() or None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_rejected"], "warning")
    return redirect(url_for("admin.posts_list"))


# ---------------------------------------------------------------------------
# Publish / Unpublish (admin only — quick actions from list view)
# ---------------------------------------------------------------------------

@admin.route("/catalogo/<int:ad_id>/featured", methods=["POST"])
@admin_required
def catalog_toggle_featured(ad_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.is_featured = not ad.is_featured
    db.session.commit()
    return redirect(url_for("admin.catalog_list"))


@admin.route("/catalogo/bulk", methods=["POST"])
@admin_required
def catalog_bulk():
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    action = request.form.get("action", "")
    ids = request.form.getlist("ad_ids")
    if not ids or not action:
        flash("Selecciona al menos una crítica y una acción.", "error")
        return redirect(url_for("admin.catalog_list"))
    ads = Ad.query.filter(Ad.id.in_([int(i) for i in ids if i.isdigit()])).all()
    if action == "unpublish":
        for a in ads: a.status = "draft"
    elif action == "feature":
        for a in ads: a.is_featured = True
    elif action == "unfeature":
        for a in ads: a.is_featured = False
    elif action == "delete":
        for a in ads: db.session.delete(a)
    db.session.commit()
    flash(f"{len(ads)} crítica(s) actualizadas.", "success")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/catalogo/<int:ad_id>/publicar", methods=["POST"])
@admin_required
def catalog_publish(ad_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.status         = "published"
    ad.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_published"], "success")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/catalogo/<int:ad_id>/despublicar", methods=["POST"])
@admin_required
def catalog_unpublish(ad_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.status = "draft"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_unpublished"], "info")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/publicaciones/<int:post_id>/publicar", methods=["POST"])
@admin_required
def post_publish(post_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    post = Post.query.get_or_404(post_id)
    post.status         = "published"
    post.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_published"], "success")
    return redirect(url_for("admin.posts_list"))


@admin.route("/publicaciones/<int:post_id>/despublicar", methods=["POST"])
@admin_required
def post_unpublish(post_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    post = Post.query.get_or_404(post_id)
    post.status = "draft"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_unpublished"], "info")
    return redirect(url_for("admin.posts_list"))


# ---------------------------------------------------------------------------
# Set to draft (admin + approver — from detail form)
# ---------------------------------------------------------------------------

@admin.route("/catalogo/<int:ad_id>/borrador", methods=["POST"])
@admin_required
def ad_to_draft(ad_id):
    if not can_approve_content(current_user, "catalog"):
        from flask import abort; abort(403)
    ad = Ad.query.get_or_404(ad_id)
    ad.status         = "draft"
    ad.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_to_draft"], "info")
    return redirect(url_for("admin.catalog_list"))


@admin.route("/publicaciones/<int:post_id>/borrador", methods=["POST"])
@admin_required
def post_to_draft(post_id):
    if not can_approve_content(current_user, "posts"):
        from flask import abort; abort(403)
    post = Post.query.get_or_404(post_id)
    post.status         = "draft"
    post.rejection_note = None
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_to_draft"], "info")
    return redirect(url_for("admin.posts_list"))


# ---------------------------------------------------------------------------
# Comment moderation
# ---------------------------------------------------------------------------

def _post_comment_query():
    """Returns a base PostComment query filtered by current_user's permissions."""
    q = PostComment.query.join(Post, PostComment.post_id == Post.id)
    if current_user.role == "admin":
        return q
    elif current_user.role == "editor":
        return q.filter(Post.author_id == current_user.id)
    elif current_user.role == "approver":
        if has_content_access(current_user, "posts"):
            return q
    return q.filter(db.text("1=0"))


def _ad_comment_query():
    """Returns a base AdComment query filtered by current_user's permissions."""
    q = AdComment.query.join(Ad, AdComment.ad_id == Ad.id)
    if current_user.role == "admin":
        return q
    elif current_user.role == "editor":
        return q.filter(Ad.created_by_id == current_user.id)
    elif current_user.role == "approver":
        if has_content_access(current_user, "catalog"):
            return q
    return q.filter(db.text("1=0"))


@admin.route("/comentarios/nuevo", methods=["GET", "POST"])
@admin_required
def comment_create():
    if current_user.role != "admin":
        from flask import abort; abort(403)
    flash("Crear comentario manualmente — próximamente.", "info")
    return redirect(url_for("admin.comments_list"))


@admin.route("/comentarios/")
@admin_required
def comments_list():
    if current_user.role not in ("admin", "editor", "approver"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]

    status_filter = request.args.get("status", "all")
    source_filter = request.args.get("source", "all")  # "all" | "post" | "ad"

    # Base queries (permission-filtered)
    pq_base = _post_comment_query()
    aq_base = _ad_comment_query()

    # Counts use status-only filter (ignoring source, so tab counts are source-aware)
    def _status_counts(pq, aq):
        return {
            "all":      pq.count() + aq.count(),
            "approved": pq.filter_by(status="approved").count() + aq.filter_by(status="approved").count(),
            "pending":  pq.filter_by(status="pending").count()  + aq.filter_by(status="pending").count(),
            "spam":     pq.filter_by(status="spam").count()     + aq.filter_by(status="spam").count(),
        }

    # Apply source filter to determine what base queries the counts use
    if source_filter == "post":
        counts = _status_counts(pq_base, pq_base.filter(db.text("1=0")))
    elif source_filter == "ad":
        counts = _status_counts(pq_base.filter(db.text("1=0")), aq_base)
    else:
        counts = _status_counts(pq_base, aq_base)

    # Apply both filters to the listing queries
    pq = _post_comment_query()
    aq = _ad_comment_query()
    if status_filter != "all":
        pq = pq.filter_by(status=status_filter)
        aq = aq.filter_by(status=status_filter)

    if source_filter == "post":
        post_comments = pq.order_by(PostComment.created_at.desc()).all()
        ad_comments   = []
    elif source_filter == "ad":
        post_comments = []
        ad_comments   = aq.order_by(AdComment.created_at.desc()).all()
    else:
        post_comments = pq.order_by(PostComment.created_at.desc()).all()
        ad_comments   = aq.order_by(AdComment.created_at.desc()).all()

    for c in post_comments:
        c._ctype = "post"
    for c in ad_comments:
        c._ctype = "ad"

    comments = sorted(
        post_comments + ad_comments,
        key=lambda c: c.created_at,
        reverse=True,
    )

    return render_template(
        "admin/comments.html", lang=lang, ui=ui, active="comments",
        comments=comments, counts=counts,
        status_filter=status_filter, source_filter=source_filter,
    )


def _get_moderable_comment(comment_id):
    """Load PostComment and verify current_user can moderate it (403 if not)."""
    comment = PostComment.query.get_or_404(comment_id)
    if current_user.role == "admin":
        return comment
    if current_user.role == "editor":
        if comment.post.author_id != current_user.id:
            from flask import abort; abort(403)
    elif current_user.role == "approver":
        if not has_content_access(current_user, "posts"):
            from flask import abort; abort(403)
    else:
        from flask import abort; abort(403)
    return comment


def _get_moderable_ad_comment(comment_id):
    """Load AdComment and verify current_user can moderate it (403 if not)."""
    comment = AdComment.query.get_or_404(comment_id)
    if current_user.role == "admin":
        return comment
    if current_user.role == "editor":
        if comment.ad.created_by_id != current_user.id:
            from flask import abort; abort(403)
    elif current_user.role == "approver":
        if not has_content_access(current_user, "catalog"):
            from flask import abort; abort(403)
    else:
        from flask import abort; abort(403)
    return comment


# ── PostComment per-row actions ──────────────────────────────────────────────

@admin.route("/comentarios/<int:comment_id>/aprobar", methods=["POST"])
@admin_required
def comment_approve(comment_id):
    comment = _get_moderable_comment(comment_id)
    comment.status = "approved"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/<int:comment_id>/pendiente", methods=["POST"])
@admin_required
def comment_pend(comment_id):
    comment = _get_moderable_comment(comment_id)
    comment.status = "pending"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/<int:comment_id>/spam", methods=["POST"])
@admin_required
def comment_spam(comment_id):
    comment = _get_moderable_comment(comment_id)
    comment.status = "spam"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/<int:comment_id>/eliminar", methods=["POST"])
@admin_required
def comment_delete_admin(comment_id):
    comment = _get_moderable_comment(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_deleted"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


# ── AdComment per-row actions ────────────────────────────────────────────────

@admin.route("/comentarios/ad/<int:comment_id>/aprobar", methods=["POST"])
@admin_required
def comment_approve_ad(comment_id):
    comment = _get_moderable_ad_comment(comment_id)
    comment.status = "approved"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/ad/<int:comment_id>/pendiente", methods=["POST"])
@admin_required
def comment_pend_ad(comment_id):
    comment = _get_moderable_ad_comment(comment_id)
    comment.status = "pending"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/ad/<int:comment_id>/spam", methods=["POST"])
@admin_required
def comment_spam_ad(comment_id):
    comment = _get_moderable_ad_comment(comment_id)
    comment.status = "spam"
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_updated"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


@admin.route("/comentarios/ad/<int:comment_id>/eliminar", methods=["POST"])
@admin_required
def comment_delete_admin_ad(comment_id):
    comment = _get_moderable_ad_comment(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash(ADMIN_UI[get_admin_lang()]["ok_comment_deleted"], "success")
    return redirect(url_for("admin.comments_list", status=request.form.get("back_status", "all")))


# ── Bulk action (both types) ─────────────────────────────────────────────────

@admin.route("/comentarios/accion-masiva", methods=["POST"])
@admin_required
def comments_bulk_action():
    if current_user.role not in ("admin", "editor", "approver"):
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    action = request.form.get("action", "")
    raw_ids = request.form.getlist("comment_ids")

    if not raw_ids or action not in ("approve", "pending", "spam", "delete"):
        return redirect(url_for("admin.comments_list"))

    # Split prefixed IDs: p_{id} → PostComment, a_{id} → AdComment
    post_ids = [int(v[2:]) for v in raw_ids if v.startswith("p_") and v[2:].isdigit()]
    ad_ids   = [int(v[2:]) for v in raw_ids if v.startswith("a_") and v[2:].isdigit()]

    total = 0

    post_comments = PostComment.query.filter(PostComment.id.in_(post_ids)).all() if post_ids else []
    for c in post_comments:
        if current_user.role == "editor" and c.post.author_id != current_user.id:
            continue
        if current_user.role == "approver" and not has_content_access(current_user, "posts"):
            continue
        if action == "approve":   c.status = "approved"
        elif action == "pending": c.status = "pending"
        elif action == "spam":    c.status = "spam"
        elif action == "delete":  db.session.delete(c)
        total += 1

    ad_comments = AdComment.query.filter(AdComment.id.in_(ad_ids)).all() if ad_ids else []
    for c in ad_comments:
        if current_user.role == "editor" and c.ad.created_by_id != current_user.id:
            continue
        if current_user.role == "approver" and not has_content_access(current_user, "catalog"):
            continue
        if action == "approve":   c.status = "approved"
        elif action == "pending": c.status = "pending"
        elif action == "spam":    c.status = "spam"
        elif action == "delete":  db.session.delete(c)
        total += 1

    db.session.commit()
    msg = ui["ok_comments_updated"].replace("{n}", str(total))
    flash(msg, "success")
    return redirect(url_for("admin.comments_list"))


# ---------------------------------------------------------------------------
# Banned words (admin only)
# ---------------------------------------------------------------------------

@admin.route("/palabras-filtradas/")
@admin_required
def banned_words_list():
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    words = BannedWord.query.order_by(BannedWord.word).all()
    return render_template(
        "admin/banned_words.html", lang=lang, ui=ui,
        active="banned_words", words=words,
    )


@admin.route("/palabras-filtradas/nueva", methods=["POST"])
@admin_required
def banned_word_create():
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    word = request.form.get("word", "").strip().lower()
    language = request.form.get("language", "all")
    if not word:
        flash(ui["err_word_required"], "error")
        return redirect(url_for("admin.banned_words_list"))
    if BannedWord.query.filter_by(word=word).first():
        flash(ui["err_word_exists"], "error")
        return redirect(url_for("admin.banned_words_list"))
    db.session.add(BannedWord(word=word, language=language))
    db.session.commit()
    flash(ui["ok_word_added"], "success")
    return redirect(url_for("admin.banned_words_list"))


@admin.route("/palabras-filtradas/<int:word_id>/eliminar", methods=["POST"])
@admin_required
def banned_word_delete(word_id):
    if current_user.role != "admin":
        from flask import abort; abort(403)
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    word = BannedWord.query.get_or_404(word_id)
    db.session.delete(word)
    db.session.commit()
    flash(ui["ok_word_deleted"], "success")
    return redirect(url_for("admin.banned_words_list"))


# ---------------------------------------------------------------------------
# Site settings
# ---------------------------------------------------------------------------

@admin.route("/seo/", methods=["GET", "POST"])
@admin_required
def seo_settings():
    lang = get_admin_lang()
    ui = ADMIN_UI[lang]
    settings = SiteSettings.get()

    if request.method == "POST":
        settings.site_name      = request.form.get("site_name", "").strip() or "AdCritic"
        settings.description_es = request.form.get("description_es", "").strip() or None
        settings.description_en = request.form.get("description_en", "").strip() or None
        settings.site_url       = request.form.get("site_url", "").strip().rstrip("/") or None
        db.session.commit()
        flash(ui["ok_settings_saved"], "success")
        return redirect(url_for("admin.seo_settings"))

    return render_template(
        "admin/site_settings.html", lang=lang, ui=ui, active="seo", settings=settings,
    )


def _save_user(existing_user, ui):
    f = request.form
    email     = f.get("email", "").strip().lower()
    password  = f.get("password", "").strip()
    role      = f.get("role", "free")
    is_active = f.get("is_active") == "1"

    if not email:
        flash(ui["err_missing"], "error")
        return "missing"

    if existing_user is None and not password:
        flash(ui["err_missing"], "error")
        return "missing"

    if role not in User.ROLES:
        flash(ui["err_invalid_role"], "error")
        return "role"

    # Prevent removing the last admin
    if existing_user is not None:
        losing_admin = existing_user.role == "admin" and (role != "admin" or not is_active)
        if losing_admin and User.query.filter_by(role="admin", is_active=True).count() <= 1:
            flash(ui["err_last_admin"], "error")
            return "last_admin"

    # Email uniqueness
    conflict = User.query.filter_by(email=email).first()
    if conflict and (existing_user is None or conflict.id != existing_user.id):
        flash(ui["err_email_taken"], "error")
        return "email"

    if existing_user is None:
        user = User(email=email, role=role, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()   # get user.id for content_access
    else:
        user = existing_user
        user.email    = email
        user.role     = role
        user.is_active = is_active
        if password:
            user.set_password(password)

    # Content access — rebuild for editor / approver
    RoleContentAccess.query.filter_by(user_id=user.id).delete()
    if role in ("editor", "approver"):
        for ct in ("catalog", "posts"):
            if f.get(f"access_{ct}") == "1":
                db.session.add(RoleContentAccess(user_id=user.id, content_type=ct))

    db.session.commit()
    return None
