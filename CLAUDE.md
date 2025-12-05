# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MaimDB is a unified database core library that provides multi-tenant SaaS architecture support with SQLite as the default database. It implements a complete data model system based on MaiMConfig design, supporting PostgreSQL, MySQL, and SQLite with automatic fallback.

## Key Architecture

### Model System
The codebase contains three tiers of models:

1. **V2 System Models** (core multi-tenant architecture):
   - `BaseModel`: Foundation model with timestamps
   - `Tenant`: Multi-tenant core with configuration (JSON), status management
   - `Agent`: AI assistant entities with tenant relationships
   - `ApiKey`: Access control with permissions and usage tracking

2. **Business Models** (general functionality):
   - `ChatHistory`: Chat conversation records
   - `ChatLogs`: Detailed chat logs with performance metrics
   - `FileUpload`: File upload management
   - `UserSession`: User session management
   - `SystemMetrics`: System performance monitoring

3. **Deprecated Models** (backward compatibility only)

### Database Architecture
- **SQLite by default**: No configuration required, creates `data/MaiBot.db`
- **Multi-database support**: PostgreSQL, MySQL with environment variables
- **Connection management**: Thread-safe connection pool with automatic fallback
- **Migrations**: Support for schema evolution and data migration

### Integration Points
- **MaiMConfig Integration**: Complete database model replacement for MaiMConfig
- **Async Support**: Wrapper classes for async operations in FastAPI contexts
- **Multi-tenant Isolation**: Built-in tenant isolation with ID-based routing

## Common Development Commands

### Database Operations
```bash
# Test SQLite startup (default behavior)
python scripts/simple_sqlite_test.py

# Test database connection
python scripts/test_database_connection.py

# Create V2 database tables
python scripts/create_v2_tables.py

# Demo V2 models
python scripts/demo_v2_models.py

# Migrate to V2 models (if upgrading from legacy)
python scripts/migrate_to_v2_models.py

# Comprehensive SQLite startup test
python scripts/test_sqlite_startup.py
```

### Environment Configuration
```bash
# Default: No configuration needed (SQLite)
# Optional: Set environment variables for other databases

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/maimbot"

# MySQL
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/maimbot"

# Explicit SQLite
export DATABASE_URL="sqlite:///data/custom.db"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Lint code
ruff check src/

# Format code
ruff format src/
```

## Development Workflow

### Adding New Models
1. Define model in appropriate category:
   - V2 system models: `src/core/models/system_v2.py`
   - Business models: `src/core/models/business.py`
2. Inherit from correct base class:
   - V2 models: `BaseModel`
   - Business models: `BusinessBaseModel`
3. Add to model list in `src/core/models/__init__.py`
4. Update database migration scripts if needed

### Model Usage Patterns

#### Multi-tenant Models (V2)
```python
from maim_db.src.core.models import Tenant, Agent, ApiKey, TenantType

# Create tenant
tenant = Tenant.create(
    tenant_name="Example Company",
    tenant_type=TenantType.ENTERPRISE.value,
    tenant_config='{"max_agents": 100}'
)

# Create agent with tenant relationship
agent = Agent.create(
    tenant_id=tenant.id,
    name="Support Assistant",
    config='{"persona": "professional support"}'
)

# Create API key with permissions
api_key = ApiKey.create(
    tenant_id=tenant.id,
    agent_id=agent.id,
    permissions='["chat", "config_read"]'
)
```

#### Business Models
```python
from maim_db.src.core.models import ChatHistory

# Business models are standalone with timestamp fields
chat = ChatHistory.create(
    session_id="session_123",
    user_message="Hello",
    agent_response="Hi there!"
)
```

### Database Migration Patterns
```python
from peewee import *
from maim_db.src.core import get_database

database = get_database()
migrator = database.migrator()

# Add new column
migrator.add_column('tenants', 'new_field', CharField(null=True))
migrator.run()
```

## Project Structure Insights

### Configuration System
- `src/core/config.py`: Database configuration with environment variable support
- `src/core/settings.py`: Pydantic-based settings (fallback if available)
- `src/core/database.py`: Database connection management with multi-database support

### Model Architecture
- `src/core/models/system_v2.py`: Multi-tenant core models with JSON configuration support
- `src/core/models/business.py`: General business functionality models
- `src/core/async_models.py`: Async wrappers for FastAPI integration

### Integration Layer
- Async model wrappers provide compatibility for MaiMConfig
- Database adapters handle different database types seamlessly
- Configuration inheritance supports both legacy and new patterns

## Important Implementation Details

### SQLite Default Behavior
- No configuration required for development
- Automatic directory and file creation (`data/MaiBot.db`)
- WAL mode enabled for performance
- Connection pooling and timeout management

### Multi-tenant ID Patterns
- Tenants: `tenant_xxxxxxxx`
- Agents: `agent_xxxxxxxx`
- API Keys: `key_xxxxxxxx`

### JSON Configuration Storage
- Tenant configurations in `tenant_config` field
- Agent personalities and parameters in `config` field
- API permissions in `permissions` field
- All stored as text fields with JSON parsing in application layer

### Database Fallback Strategy
1. Try explicit `DATABASE_URL` if set
2. Try PostgreSQL/MySQL based on environment variables
3. Default to SQLite automatically
4. Error handling with graceful degradation

## Testing Strategy

### Unit Tests
- Model creation and validation
- Database connection tests
- Configuration loading tests

### Integration Tests
- End-to-end database operations
- Multi-tenant isolation verification
- Database migration testing

### Database Tests
- Test all supported database types
- Verify fallback mechanisms
- Performance benchmarking

## Key Dependencies

- **peewee**: ORM layer with multi-database support
- **playhouse**: Additional Peewee utilities (connection pooling)
- **pytest**: Testing framework (dev dependency)
- **ruff**: Linting and formatting (dev dependency)

## Environment Variables

### Database Configuration
- `DATABASE_URL`: Complete database connection string (overrides others)
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`: Individual database params
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Legacy compatibility

### Connection Settings
- `DB_MAX_CONNECTIONS`: Maximum connection pool size (default: 20)
- `DB_CONNECTION_TIMEOUT`: Connection timeout in seconds (default: 30)
- `DB_TIMEZONE`: Database timezone setting (default: UTC)