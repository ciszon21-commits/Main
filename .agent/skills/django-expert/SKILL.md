---
name: django-expert
description: Expert guidance on Django Full-Stack development including DRF, Best Practices, Security, and Testing.
---

# Django Python Full-Stack Development Skill

Use this skill when developing, refactoring, or reviewing Django applications.

## venv
- Always in the venv folder, we ignore it in git, but it exists.

## Code Style and Structure
- Write concise, idiomatic Python code.
- Follow Django's coding style guide.
- Use functional views or class-based views appropriately.
- Prefer iteration and modularization.
- File structure: models, views, serializers, urls, forms, admin.

## Django Best Practices
- Use Django models with proper field types and validators.
- Implement custom managers and querysets for complex queries.
- Use Django's ORM effectively; avoid N+1 queries.
- Implement proper migrations with Alembic-style approach.

## Django REST Framework
- Use serializers for data validation and transformation.
- Implement viewsets and routers for RESTful APIs.
- Use proper authentication (Token, JWT, Session).
- Implement pagination for list endpoints.

## Models and Database
- Use Django ORM with select_related and prefetch_related.
- Index frequently queried fields.
- Use database constraints appropriately.
- Implement soft deletes when needed.

## Views and Templates
- Use class-based views for CRUD operations.
- Keep business logic in services, not views.
- Use Django template language efficiently.
- Implement proper context processors.

## Forms and Validation
- Use Django Forms for input validation.
- Implement custom validators when needed.
- Handle form errors gracefully.

## Security
- Use Django's built-in security features.
- Enable CSRF protection.
- Implement proper authentication and authorization.
- Use Django's password hashers.
- Sanitize user inputs.

## Admin Panel
- Customize Django admin appropriately.
- Implement list filters and search fields.
- Use admin actions for bulk operations.

## Testing
- Write tests using Django's TestCase.
- Test models, views, and forms.
- Use fixtures for test data.
- Mock external services.

## Performance
- Use caching (Redis, Memcached).
- Optimize database queries.
- Use database connection pooling.
- Implement pagination.
