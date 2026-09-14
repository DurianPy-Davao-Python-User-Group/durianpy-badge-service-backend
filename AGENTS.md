# Developer & AI Agent Guidelines

Welcome to the **DurianPy Badge System Backend**. This document establishes the architectural principles, global coding conventions, layer-by-layer modification workflows, dependency injection wiring rules, event logging standards, sensitive data masking rules, and testing requirements for human engineers and AI agents contributing to this codebase.

---

## 1. Architectural Architecture & Principles

This codebase strictly follows **Clean Architecture (Ports and Adapters)**:

```
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│           (FastAPI Routes, Schemas, DI Wiring)         │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Application Layer                   │
│     (Use Cases, Use Case Ports, DTOs, Outbound Ports)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                      Domain Layer                      │
│        (Domain Entities, Value Objects, Exceptions)    │
└────────────────────────────────────────────────────────┘
                            ▲
┌───────────────────────────┴────────────────────────────┐
│                  Infrastructure Layer                  │
│       (PynamoDB Repositories, S3/CloudFront Resolvers) │
└────────────────────────────────────────────────────────┘
```

### Core Rules:
1. **The Dependency Rule**: Inner layers (Domain, Application) MUST NEVER depend on outer layers (Infrastructure, Presentation).
2. **Infrastructure Decoupling**: Infrastructure knowledge (e.g. S3 URI formats, CloudFront URLs, PynamoDB internals, DynamoDB expressions) must never bleed into use cases or domain models.
   - Storage paths returned by repositories or domain entities are always relative to the bucket root (e.g. `designs/...`).
   - Resolving URLs is delegated to outbound ports (e.g., `MediaUrlResolverPort`).
3. **Use Case Ports**: All use cases must implement an explicit use case port inheriting from `UseCasePort` with `execute(*args, **kwargs)` as the public execution contract.

---

## 2. Global Conventions & Standards

### Double Underscore (`__`) Private Member Convention
All private attributes, private helper methods, and private class constants **MUST use double underscores (`__`)**:
- **Private instance attributes**: `self.__repository`, `self.__media_url_resolver`, `self.__cdn_base_url`
- **Private methods**: `def __to_domain(self, record: Model) -> DomainModel:`
- **Private class constants**: `__MEETUP_PK_PREFIX = 'MEETUP#'`, `__YEAR_GSI1PK_PREFIX = 'YEAR#'`

> **Note on Name Mangling**: In Python, `__attr` on `class Foo` becomes `_Foo__attr`. When writing reflection or inspecting objects in tests, reference the mangled name if accessing private helpers directly.

### Execution Logging Decorator Rule
- **`@log_execution` is applied ONLY to Use Cases**: Apply `@log_execution` decorator strictly to `execute()` methods of use case interactors in `src/application/use_cases/`.
- **Do NOT** apply `@log_execution` to infrastructure repositories, storage adapters, route handlers, or health check endpoints.

### Python Code Style
- **Python Version**: Python 3.12+
- **Linter & Formatter**: Ruff (`single` quotes, 120 character line length limit).
- **Docstrings**: PEP 257 compliant docstrings using **reStructuredText (reST / Sphinx)** format (`:param <name>: ...`, `:type <name>: ...`, `:returns: ...`, `:rtype: ...`, `:raises <Error>: ...`) on all public modules, classes, functions, and methods.
- **Type Annotations**: Comprehensive type annotations on all function signatures.

### Conventional Commits
All git commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- **Format**: `<type>(<optional scope>): <description>`
- **Common Types**:
  - `feat`: New user-facing feature or domain capability.
  - `fix`: Bug fix or error resolution.
  - `refactor`: Code change that neither fixes a bug nor adds a feature.
  - `test`: Adding or correcting automated tests.
  - `docs`: Documentation updates only.
  - `style`: Formatting, white-space, or linting adjustments without logic changes.
  - `chore`: Build tools, dependencies, or auxiliary configurations.
  - `ci`: CI/CD configuration files and automation scripts.
- **Rules**: Use lowercase, imperative mood in the description (e.g. `feat(catalog): add year filter to public badge discovery`), without ending punctuation. Enforced automatically by `commit-msg` git hooks.

---

## 3. Event Logging, State Tracking & Sensitive Data Masking

### Concise & Meaningful Log Messages
Log messages **MUST be concise and direct without losing the essence of the action being performed**:
- **Include Core Action Context**: Always include the action verb, target resource type, resource identifier, and decisive outcome (e.g. `Created badge design 'd-123' for meetup 'm-456'`).
- **Eliminate Verbosity & Fluff**: Avoid filler text or vague statements (e.g. avoid `Starting the process of attempting to fetch items...` $\rightarrow$ use `Fetching public catalog for year '2026'`).

### Logging Important State Changes
For operational observability and post-incident debugging, log significant business events and state mutations:
- **Database State Changes**: Record item creation, status updates, badge issuances, revocations, and transaction completions at `logger.info` level.
- **Degraded Operations / Fallbacks**: Record cache misses, fallback defaults, or retry events at `logger.warning` level.
- **Boundary Errors**: Record handled infrastructure failures at `logger.error` level before re-raising domain exceptions.

### Mandatory Sensitive Data Masking
When logging strings containing sensitive user data, PII (emails, names), API keys, tokens, or credential identifiers, you **MUST** use the `mask_string` utility from `src.core.logging`:

```python
from src.core.logging import logger, mask_string

# Example: Concise state change with masked attribution
logger.info(f"Created badge design '{design.design_id}' by user '{mask_string(created_by)}'")

# Example: Concise parameter debugging with masked token
logger.debug(
    f"Loaded secret '{secret_name}' with value '{mask_string(secret_val, visible_prefix=3, visible_suffix=3)}'"
)
```

`mask_string(value, visible_prefix=2, visible_suffix=2, mask_char='*')` preserves leading and trailing characters while obscuring sensitive middle contents (e.g., `user_admin_2026` $\rightarrow$ `us*************26`).

---

## 4. Domain Boundaries & Exception Handling

### Exception Hierarchy (`src/domain/exceptions/`)
- Base domain exceptions reside in `src/domain/exceptions/base_exceptions.py`:
  - `DomainError`: Root exception for all business domain errors.
  - `EntityNotFoundError`: Target domain entity was not found.
  - `EntityValidationError`: Domain entity validation or invariant violation.
  - `RepositoryError`: Boundary exception for database / persistence failures.
  - `StorageServiceError`: Boundary exception for object storage / CDN failures.
- Feature-specific exceptions inherit from domain base exceptions:
  - Security exceptions (`src/domain/exceptions/auth_exceptions.py`): `AuthError` (subclass of `DomainError`), `AuthenticationError` (401 invalid/expired token), `AuthorizationError` (403 insufficient permissions/roles/scopes).
  - Badge design exceptions (`src/domain/exceptions/badge_design_exceptions.py`): `BadgeDesignCreationError`, `BadgeDesignQueryError`, `MediaResolutionError`.

### Translation at Infrastructure Boundary
- Infrastructure adapters (PynamoDB repositories, Boto3 clients, Cognito token verifiers) must wrap low-level exceptions (e.g., `PynamoDBException`, `ClientError`, `BotoCoreError`, `PyJWTError`, `PyJWKClientError`) and re-raise explicit domain exceptions.
- Outer layers never see vendor-specific database, JWT, or cloud provider errors.

### Presentation Error Sanitization (`src/presentation/api/exception_handlers.py`)
- Registered global exception handlers convert domain exceptions to appropriate HTTP status codes:
  - `AuthenticationError` $\rightarrow$ `401 Unauthorized` (includes `WWW-Authenticate: Bearer` challenge header)
  - `AuthorizationError` $\rightarrow$ `403 Forbidden`
  - `EntityNotFoundError` $\rightarrow$ `404 Not Found`
  - `EntityValidationError` $\rightarrow$ `422 Unprocessable Entity`
  - `RepositoryError` / `StorageServiceError` $\rightarrow$ `500 Internal Server Error` (with sanitized error messages)
  - `DomainError` $\rightarrow$ `400 Bad Request`
- **Prevent Stack Trace Leaks**: The catch-all `Exception` handler logs tracebacks server-side only (`logger.error(..., exc_info=True)`) and returns a uniform JSON envelope:
  ```json
  {
    "error": {
      "code": "INTERNAL_SERVER_ERROR",
      "message": "An unexpected internal server error occurred."
    }
  }
  ```

---

## 5. Step-by-Step Feature Implementation Guide

When implementing a new feature or API endpoint, modify files in the following sequence:

```
1. Domain (Entities & Exceptions)
   └── src/domain/models/
   └── src/domain/exceptions/

2. Application Ports & DTOs
   └── src/application/dtos/
   └── src/application/ports/repositories/
   └── src/application/ports/security/
   └── src/application/ports/storage/
   └── src/application/ports/use_cases/

3. Application Use Cases
   └── src/application/use_cases/ (decorated with @log_execution)

4. Infrastructure Adapters
   └── src/infrastructure/db/models/
   └── src/infrastructure/db/pynamo_repositories/
   └── src/infrastructure/security/
   └── src/infrastructure/storage/

5. Presentation Layer & DI Wiring
   └── src/presentation/api/schemas/
   └── src/presentation/api/dependencies/ (DI providers)
   └── src/presentation/api/routes/ (Controllers)
   └── src/presentation/api/routes/main_controller.py (Router aggregation)

6. Unit Tests
   └── tests/unit/
```

---

## 6. Dependency Injection (DI) Wiring Guide

### 6.1 Application Use Case & Repository DI Wiring

FastAPI's dependency injection is used in `src/presentation/api/dependencies/` to bind port abstractions to concrete infrastructure adapters and instantiate use cases:

```python
# src/presentation/api/dependencies/badge_design_dependencies.py

from fastapi import Depends
from src.application.ports.repositories.badge_design_repository import BadgeDesignRepositoryPort
from src.application.ports.storage.media_url_resolver_port import MediaUrlResolverPort
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.application.use_cases.get_public_badge_designs_use_case import (
    GetPublicBadgeDesignsUseCase,
)
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)
from src.infrastructure.storage.cloudfront_media_url_resolver import (
    CloudFrontMediaUrlResolver,
)


def get_badge_design_repository() -> BadgeDesignRepositoryPort:
    return PynamoBadgeDesignRepository()


def get_media_url_resolver() -> MediaUrlResolverPort:
    return CloudFrontMediaUrlResolver()


def get_public_badge_designs_use_case(
    repository: BadgeDesignRepositoryPort = Depends(get_badge_design_repository),
    media_url_resolver: MediaUrlResolverPort = Depends(get_media_url_resolver),
) -> GetPublicBadgeDesignsUseCasePort:
    return GetPublicBadgeDesignsUseCase(
        badge_design_repository=repository,
        media_url_resolver=media_url_resolver,
    )
```

Controllers then depend **strictly on the use case port interface**:
```python
# src/presentation/api/routes/public_catalog_controller.py


@router.get('/designs', response_model=PublicCatalogResponseSchema)
def get_public_badge_designs(
    use_case: GetPublicBadgeDesignsUseCasePort = Depends(get_public_badge_designs_use_case),
) -> PublicCatalogResponseSchema:
    dtos = use_case.execute()
    return PublicCatalogResponseSchema(data=...)
```

### 6.2 Authentication & Authorization (RBAC) DI Wiring

Authentication follows Clean Architecture with `TokenVerifierPort` (`src/application/ports/security/`) implemented by `CognitoTokenVerifier` (`src/infrastructure/security/`).

FastAPI dependency injection providers in `src/presentation/api/dependencies/auth_dependencies.py` expose composable dependencies for securing routes:

| Dependency | Purpose | Injected Type / Return | Throws on Failure |
|---|---|---|---|
| `get_token_verifier()` | Resolves the concrete `TokenVerifierPort` adapter. | `TokenVerifierPort` | — |
| `get_current_user` | Validates Cognito Bearer access token signature against User Pool JWKS and claims (`token_use == 'access'`, `client_id`, `iss`). | `AuthenticatedUser` | `401 Unauthorized` |
| `require_admin` | Requires user to have administrator privileges (`admin`, `superadmin`, or `super_admin`). | `AuthenticatedUser` | `401 Unauthorized` / `403 Forbidden` |
| `require_superadmin` | Requires user to have superadmin privileges (`superadmin` or `super_admin`). | `AuthenticatedUser` | `401 Unauthorized` / `403 Forbidden` |
| `require_roles(*roles)` | Factory creating a dependency that enforces membership in at least one specified role or group. | `Callable[..., AuthenticatedUser]` | `401 Unauthorized` / `403 Forbidden` |
| `require_scopes(*scopes)` | Factory creating a dependency that enforces possession of all specified OAuth2 scopes. | `Callable[..., AuthenticatedUser]` | `401 Unauthorized` / `403 Forbidden` |

#### Securing Route Controllers

Controllers inject auth dependencies directly into route parameter signatures:

```python
# src/presentation/api/routes/example_controller.py

from fastapi import APIRouter, Depends
from src.domain.models.authenticated_user import AuthenticatedUser, UserRole
from src.presentation.api.dependencies.auth_dependencies import (
    get_current_user,
    require_admin,
    require_roles,
    require_scopes,
    require_superadmin,
)

router = APIRouter(tags=['Example'])


# 1. Any authenticated user (e.g. regular attendees, federated Google users)
@router.get('/profile')
def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    return {'user_id': current_user.user_id, 'username': current_user.username}


# 2. Admin-only endpoint
@router.post('/admin/badges')
def create_badge(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> dict[str, str]:
    return {'message': f'Admin action authorized for {current_user.username}'}


# 3. Superadmin-only endpoint
@router.delete('/admin/system-reset')
def reset_system(
    current_user: AuthenticatedUser = Depends(require_superadmin),
) -> dict[str, str]:
    return {'message': 'System reset authorized'}


# 4. Custom group / role check
@router.get('/speaker/portal')
def get_speaker_portal(
    current_user: AuthenticatedUser = Depends(require_roles('speaker', 'organizer')),
) -> dict[str, str]:
    return {'message': 'Welcome speaker'}


# 5. Specific OAuth2 scope check
@router.post('/designs/publish')
def publish_design(
    current_user: AuthenticatedUser = Depends(require_scopes('designs:write')),
) -> dict[str, str]:
    return {'message': 'Scope authorized'}
```

#### Mocking Authentication in Tests

When testing controllers via `TestClient(app)`, override `get_current_user`, `require_admin`, or `get_token_verifier` in `app.dependency_overrides`:

```python
from fastapi.testclient import TestClient
from src.domain.models.authenticated_user import AuthenticatedUser
from src.presentation.api.dependencies.auth_dependencies import get_current_user


def test_protected_route_with_mock_user(client: TestClient) -> None:
    mock_user = AuthenticatedUser(
        user_id='sub-test-123',
        username='test_admin',
        groups=['admin'],
        scopes=['openid'],
    )
    client.app.dependency_overrides[get_current_user] = lambda: mock_user

    response = client.get('/profile')
    assert response.status_code == 200
```

---

## 7. Testing Requirements

All contributions must include thorough automated unit tests located in `tests/unit/`:

| Component | Test Location | Guidelines |
|---|---|---|
| **Domain Models & Exceptions** | `tests/unit/domain/` | Test validation, domain rules, role/group logic, and exception properties. |
| **Use Cases** | `tests/unit/application/use_cases/` | Mock outbound repository & storage ports. Verify execution flow and DTO mappings. |
| **Repositories** | `tests/unit/infrastructure/db/` | Use `moto` (`mock_aws`) to test DynamoDB transactions and verify mapping to domain exceptions on failures. |
| **Security & Auth Adapters** | `tests/unit/infrastructure/security/`, `tests/unit/presentation/api/dependencies/` | Test JWT signature verification with RSA key pairs, claims validation (`token_use`, `client_id`, `sub`), role checks, and DI overrides. |
| **Storage Adapters** | `tests/unit/infrastructure/storage/` | Test URL construction, path normalization, and error handling. |
| **Controllers & Handlers** | `tests/unit/presentation/api/` | Use `TestClient(app)` to test routes, status codes, DI override capabilities, and stack trace suppression. |

Run test suite locally:
```bash
just run-unit-test
```
