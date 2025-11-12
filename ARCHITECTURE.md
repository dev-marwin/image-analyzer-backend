# Backend Architecture

## Overview

The backend follows a **layered architecture** pattern with clear separation of concerns, making it maintainable, testable, and scalable.

## Directory Structure

```plaintext
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── core/                   # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py           # Application settings
│   │   └── security.py         # JWT verification utilities
│   │
│   ├── middleware/             # Request middleware
│   │   ├── __init__.py
│   │   └── auth.py             # Authentication dependencies
│   │
│   ├── api/                    # API layer (controllers)
│   │   ├── __init__.py
│   │   └── v1/                 # API version 1
│   │       ├── __init__.py
│   │       └── routes.py       # Route handlers
│   │
│   ├── schemas/                # Pydantic models (DTOs)
│   │   ├── __init__.py
│   │   └── image.py            # Image-related schemas
│   │
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py       # OpenAI integration
│   │   └── image_processing_service.py  # Image processing orchestration
│   │
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   └── image_repository.py # Database and storage operations
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── image_utils.py     # Image manipulation utilities
│
├── requirements.txt
├── check_config.py
└── .env
```

## Layer Responsibilities

### 1. **API Layer** (`app/api/`)

- **Purpose**: Handle HTTP requests and responses
- **Responsibilities**:
  - Route definitions
  - Request validation (via Pydantic schemas)
  - Response formatting
  - Authentication enforcement (via dependencies)
- **Example**: `app/api/v1/routes.py`

### 2. **Schemas Layer** (`app/schemas/`)

- **Purpose**: Define request/response data structures
- **Responsibilities**:
  - Input validation
  - Data serialization
  - API documentation (OpenAPI)
- **Example**: `app/schemas/image.py`

### 3. **Services Layer** (`app/services/`)

- **Purpose**: Implement business logic
- **Responsibilities**:
  - Orchestrate operations across repositories
  - Apply business rules
  - Coordinate external services (AI, etc.)
- **Examples**:
  - `ai_service.py` - OpenAI integration
  - `image_processing_service.py` - Image processing workflow

### 4. **Repositories Layer** (`app/repositories/`)

- **Purpose**: Abstract data access
- **Responsibilities**:
  - Database operations
  - Storage operations
  - Data persistence
- **Example**: `app/repositories/image_repository.py`

### 5. **Core Layer** (`app/core/`)

- **Purpose**: Application-wide configuration and utilities
- **Responsibilities**:
  - Configuration management
  - Security utilities (JWT verification)
  - Shared constants
- **Examples**:
  - `config.py` - Settings management
  - `security.py` - JWT verification

### 6. **Middleware Layer** (`app/middleware/`)

- **Purpose**: Request/response processing
- **Responsibilities**:
  - Authentication dependencies
  - Request validation
  - Error handling
- **Example**: `app/middleware/auth.py`

### 7. **Utils Layer** (`app/utils/`)

- **Purpose**: Pure utility functions
- **Responsibilities**:
  - Stateless helper functions
  - Image manipulation
  - Common algorithms
- **Example**: `app/utils/image_utils.py`

## Authentication Flow

```plaintext
1. Client sends request with Authorization: Bearer <token>
   ↓
2. FastAPI HTTPBearer extracts token
   ↓
3. get_current_user dependency calls jwt_verifier.verify_token()
   ↓
4. JWT is verified against Supabase JWKS or JWT secret
   ↓
5. User ID extracted from token payload
   ↓
6. Route handler receives authenticated user_id
   ↓
7. Business logic verifies ownership before processing
```

## Request Flow Example

**Processing an Image:**

```plaintext
POST /api/v1/images/process
  ↓
[Middleware] Extract & verify JWT token → get_current_user()
  ↓
[API Layer] routes.py::process_image()
  - Validate request schema
  - Verify image ownership
  ↓
[Service Layer] image_processing_service.process_image()
  - Orchestrate: download → thumbnail → colors → AI → save
  ↓
[Repository Layer] image_repository & storage_repository
  - Database operations
  - Storage operations
  ↓
[Service Layer] ai_service.analyze_image()
  - Call OpenAI API
  ↓
[Repository Layer] Save results
  ↓
Response: 202 Accepted
```

## Key Design Principles

### 1. **Separation of Concerns**

- Each layer has a single, well-defined responsibility
- Layers communicate through well-defined interfaces

### 2. **Dependency Injection**

- FastAPI's dependency system provides clean dependency injection
- Services and repositories are injected, not instantiated directly

### 3. **Authentication First**

- All protected endpoints require authentication
- User ID is extracted from JWT, not trusted from request body
- Ownership verification at service layer

### 4. **Error Handling**

- Exceptions bubble up through layers
- HTTP exceptions at API layer
- Business exceptions at service layer

### 5. **Testability**

- Each layer can be tested independently
- Dependencies can be mocked easily
- Pure functions in utils layer

## Security Features

1. **JWT Verification**: All protected endpoints verify Supabase JWT tokens
2. **Ownership Validation**: Users can only process their own images
3. **Service Role Key**: Backend uses service role key for database operations (bypasses RLS)
4. **Token Extraction**: User ID comes from verified token, not request body

## Environment Variables

Required in `.env`:

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for backend operations
- `SUPABASE_ANON_KEY` - (Optional) Anon key for reference
- `SUPABASE_JWT_SECRET` - (Optional) JWT secret for token verification
- `OPENAI_API_KEY` - OpenAI API key
- `SUPABASE_STORAGE_BUCKET` - Storage bucket name

## API Endpoints

### Public

- `GET /` - API information
- `GET /api/v1/health` - Health check

### Protected (Requires Authentication)

- `POST /api/v1/images/process` - Process image with AI

All protected endpoints require:

```plaintext
Authorization: Bearer <supabase_jwt_token>
```

## Future Enhancements

1. **Dependency Injection Container**: For more complex dependency management
2. **Unit Tests**: Add comprehensive test coverage
3. **Integration Tests**: Test full request flows
4. **Rate Limiting**: Add rate limiting middleware
5. **Caching**: Add caching layer for frequently accessed data
6. **Monitoring**: Add logging and metrics collection
7. **API Versioning**: Support multiple API versions
