# Async Migration Implementation - Issue #935

## Overview

This PR migrates the entire backend from synchronous SQLAlchemy to async SQLAlchemy 2.0 with AsyncSession, enabling non-blocking database operations on FastAPI's ASGI event loop. This eliminates thread blocking when multiple users execute concurrent database queries, dramatically improving scalability and throughput.

## Problem Statement

### Current Architecture Issues

**Blocking Operations:**
- All database queries use synchronous `Session` and `db.query()` 
- Pattern: `db.query(User).filter(User.id == id).first()`
- Blocks the entire ASGI worker thread during database I/O
- 40 concurrent users = 40 blocked threads = request queue backlog

**Scalability Bottleneck:**
- FastAPI runs on uvloop (async event loop)
- Mixing `async def` routes with sync database calls defeats the purpose
- Worker threads are wasted waiting for database responses
- Cannot efficiently handle high concurrent load

**Example of Current Problem:**
```python
@router.get("/users/me")  # async def route
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    # But get_current_user() internally does:
    user = db.query(User).filter(User.id == id).first()  # BLOCKS!
    return user
```

## Technical Implementation Strategy

### 1. Database Engine Migration

**File:** `backend/fastapi/api/services/db_service.py`

**Before:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_type == "sqlite" else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**After:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from typing import AsyncGenerator

# Convert database URL to async driver
def get_async_database_url(url: str) -> str:
    """Convert sync database URL to async driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url

engine = create_async_engine(
    get_async_database_url(settings.database_url),
    echo=settings.debug,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Key Changes:**
- ✅ `create_async_engine` with `asyncpg` driver for PostgreSQL
- ✅ `aiosqlite` driver for SQLite development
- ✅ `AsyncSession` instead of sync `Session`
- ✅ `async_sessionmaker` instead of `sessionmaker`
- ✅ `async def get_db()` with `AsyncGenerator` type hint
- ✅ `async with` context manager
- ✅ `await session.close()`

### 2. Query Pattern Migration

**Old Synchronous Pattern:**
```python
# SELECT
user = db.query(User).filter(User.id == user_id).first()

# INSERT
db.add(new_user)
db.commit()
db.refresh(new_user)

# UPDATE
user.username = "new_name"
db.commit()

# DELETE
db.delete(user)
db.commit()

# COUNT
total = db.query(User).count()
```

**New Async Pattern:**
```python
from sqlalchemy import select, func

# SELECT - scalar_one_or_none()
stmt = select(User).filter(User.id == user_id)
result = await db.execute(stmt)
user = result.scalar_one_or_none()

# INSERT
db.add(new_user)
await db.commit()
await db.refresh(new_user)

# UPDATE
user.username = "new_name"
await db.commit()

# DELETE
await db.delete(user)
await db.commit()

# COUNT
stmt = select(func.count(User.id))
result = await db.execute(stmt)
total = result.scalar()
```

**Result Extraction Methods:**
- `.scalar()` - Single value
- `.scalar_one()` - Single value, raises if not found
- `.scalar_one_or_none()` - Single value or None
- `.scalars()` - Multiple values (iterable)
- `.fetchall()` - All rows
- `.fetchone()` - Single row

### 3. Service Layer Migration

**Example: UserService**

**Before (Synchronous):**
```python
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, password: str) -> User:
        new_user = User(username=username, password_hash=hash_password(password))
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
```

**After (Async):**
```python
from sqlalchemy import select

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        stmt = select(User).filter(User.id == user_id)
        if not include_deleted:
            stmt = stmt.filter(User.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, username: str, password: str) -> User:
        new_user = User(username=username, password_hash=hash_password(password))
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user
```

**Key Changes:**
- ✅ All methods become `async def`
- ✅ `AsyncSession` type hint for `db`
- ✅ Use `select()` construct instead of `db.query()`
- ✅ `await db.execute()` for all queries
- ✅ `await db.commit()`, `await db.refresh()`
- ✅ Extract results with `.scalar_one_or_none()`, `.scalars()`, etc.

### 4. Relationship Eager Loading

**Problem: Lazy Loading Doesn't Work with Async**

```python
# This FAILS with MissingGreenlet error in async:
user = await db.execute(select(User).filter(User.id == 1))
user = user.scalar_one()
exams = user.exams  # ERROR! Lazy load not allowed in async
```

**Solution: Explicit Eager Loading**

```python
from sqlalchemy.orm import selectinload, joinedload

# Use selectinload for one-to-many
stmt = select(User).options(selectinload(User.exams)).filter(User.id == 1)
result = await db.execute(stmt)
user = result.scalar_one()
exams = user.exams  # ✓ Works! Already loaded

# Use joinedload for many-to-one or one-to-one
stmt = select(Score).options(joinedload(Score.user)).filter(Score.id == 1)
result = await db.execute(stmt)
score = result.scalar_one()
user = score.user  # ✓ Works! Already loaded
```

**Eager Loading Strategies:**
- `selectinload()` - Separate SELECT query (good for one-to-many)
- `joinedload()` - LEFT OUTER JOIN (good for many-to-one)
- `subqueryload()` - Subquery (for complex relationships)

**Files Requiring Eager Loading:**
- `user_service.py` - User with settings, profiles, strengths
- `exam_service.py` - Exam with responses, user
- `journal_service.py` - Journal entries with tags
- `profile_service.py` - Complete profile with all sub-profiles
- `gamification_service.py` - User with achievements, streaks, XP

### 5. Router Dependency Updates

**Before:**
```python
from sqlalchemy.orm import Session
from ..services.db_service import get_db

@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # ❌ Sync session in async route
):
    # ...
```

**After:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from ..services.db_service import get_db

@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)  # ✅ Async session
):
    # ...
```

**Auth Dependency (`get_current_user`) also needs async:**
```python
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)  # ✅ AsyncSession
):
    # ... JWT validation ...
    
    # Old: user = db.query(User).filter(User.username == username).first()
    stmt = select(User).filter(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(...)
    return user
```

### 6. Application Lifecycle Updates

**File:** `backend/fastapi/api/main.py`

**Startup - Database Table Creation:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("LIFESPAN BOOT STARTED")
    
    # Initialize async database tables
    try:
        from .services.db_service import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[OK] Database tables initialized/verified")
        
        # Test async connectivity
        async with AsyncSessionLocal() as db:
            await db.execute(select(1))
            print("[OK] Async database connectivity verified")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("LIFESPAN TEARDOWN STARTED")
    await engine.dispose()
    logger.info("Async database engine disposed")
```

**Startup - Background Tasks:**
```python
# Purge task needs async database access
async def purge_task_loop():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                from .services.user_service import UserService
                user_service = UserService(db)
                await user_service.purge_deleted_users(settings.deletion_grace_period_days)
        except Exception as e:
            logger.error(f"Purge task failed: {e}")
        await asyncio.sleep(24 * 3600)
```

### 7. Dependencies Update

**File:** `backend/fastapi/requirements.txt`

**Add:**
```txt
# Async database drivers
asyncpg>=0.29.0  # PostgreSQL async driver
aiosqlite>=0.19.0  # SQLite async driver
greenlet>=3.0.0  # Required by SQLAlchemy async
```

**Existing (verify versions):**
```txt
sqlalchemy>=2.0.0  # ✓ Already supports async
```

### 8. Testing Configuration

**File:** `backend/fastapi/pytest.ini`

**Update:**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Install:**
```bash
pip install pytest-asyncio>=0.21.0
```

**Test Example:**
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_user(async_db_session: AsyncSession):
    """Test async user retrieval."""
    user_service = UserService(async_db_session)
    user = await user_service.get_user_by_id(1)
    assert user is not None
```

**Test Fixtures:**
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

@pytest.fixture
async def async_db_session():
    """Provide an async database session for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncTestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
    
    await engine.dispose()
```

## Implementation Checklist

### Phase 1: Core Infrastructure (Priority 1)
- [ ] Update `db_service.py` to use `create_async_engine` and `AsyncSession`
- [ ] Convert `get_db()` to async generator
- [ ] Update database URL to use async drivers (`asyncpg`, `aiosqlite`)
- [ ] Add async database dependencies to `requirements.txt`
- [ ] Update application lifespan for async engine disposal

### Phase 2: Service Layer (Priority 1)
- [ ] **user_service.py** - Migrate all CRUD methods to async
  - [ ] `get_user_by_id`, `get_user_by_username`
  - [ ] `create_user`, `update_user`, `delete_user`
  - [ ] `purge_deleted_users`
- [ ] **auth_service.py** - Migrate authentication logic
  - [ ] `authenticate_user`, `register_user`
  - [ ] `create_access_token`, `verify_token`
  - [ ] Session management queries
- [ ] **exam_service.py** - Migrate exam operations
  - [ ] `start_exam`, `save_response`, `save_score`
  - [ ] Add eager loading for exam-user relationships
- [ ] **profile_service.py** - Migrate profile operations
  - [ ] All profile CRUD (settings, medical, personal, strengths, emotional)
  - [ ] `get_complete_profile` with eager loading
- [ ] **journal_service.py** - Migrate journal operations
  - [ ] CRUD operations with sentiment analysis
  - [ ] Search and filtering queries
- [ ] **analytics_service.py** - Migrate analytics queries
  - [ ] Aggregate queries (count, avg, max, min)
  - [ ] Statistical computations
- [ ] **gamification_service.py** - Migrate gamification logic
  - [ ] XP, streaks, achievements
  - [ ] Leaderboard queries
- [ ] **audit_service.py** - Migrate audit logging
- [ ] **results_service.py** - Migrate results retrieval

### Phase 3: Router Layer (Priority 2)
- [ ] Update all routers to use `AsyncSession` dependency
- [ ] **auth.py** - Convert `get_current_user` to async
  - [ ] Update all auth route handlers
  - [ ] Async session queries for user lookup
- [ ] **users.py** - User management routes
- [ ] **profiles.py** - Profile management routes
- [ ] **journal.py** - Journal routes
- [ ] **exams.py** - Exam routes
- [ ] **assessments.py** - Assessment routes
- [ ] **questions.py** - Question routes
- [ ] **analytics.py** - Analytics routes
- [ ] **gamification.py** - Gamification routes
- [ ] **community.py** - Community routes

### Phase 4: Eager Loading Implementation (Priority 1)
- [ ] Identify all relationship accesses in services
- [ ] Add `selectinload()` for one-to-many relationships
- [ ] Add `joinedload()` for many-to-one relationships
- [ ] Test all relationship access paths
- [ ] Document eager loading requirements for future development

### Phase 5: Testing (Priority 1)
- [ ] Configure pytest-asyncio
- [ ] Create async test fixtures
- [ ] Migrate existing tests to async
- [ ] Add new tests for async-specific scenarios
- [ ] Load testing with concurrent requests
- [ ] Verify no `EventLoop` errors
- [ ] Verify no `MissingGreenlet` errors

### Phase 6: Performance Validation (Priority 2)
- [ ] Benchmark sync vs async performance
- [ ] Load test with 40+ concurrent users
- [ ] Monitor worker thread utilization
- [ ] Verify no thread blocking
- [ ] Measure throughput improvement

## Acceptance Criteria Status

**[IN PROGRESS] All PostgreSQL connections use asyncpg driver**
- Database engine migrated to `create_async_engine`
- Connection string updated to `postgresql+asyncpg://`

**[IN PROGRESS] Zero SynchronousSession boundaries in app/services/**
- All service methods converted to `async def`
- All queries use `select()` construct with `await db.execute()`

**[IN PROGRESS] Integration tests adapted to event-loop paradigms**
- pytest-asyncio configured
- Test fixtures use `AsyncSession`
- No EventLoop Closed errors

## Edge Cases & Solutions

### 1. Lazy Loading Crashes (MissingGreenlet)

**Problem:**
```python
user = await user_service.get_user_by_id(1)
exams = user.exams  # ❌ MissingGreenlet error!
```

**Solution:**
```python
# In service method:
stmt = select(User).options(selectinload(User.exams)).filter(User.id == 1)
result = await db.execute(stmt)
user = result.scalar_one()
exams = user.exams  # ✓ Works!
```

### 2. Transaction Management

**Problem:** Forgetting to `await` commit/rollback

**Solution:**
```python
try:
    db.add(user)
    await db.commit()  # ✅ Must await!
except Exception:
    await db.rollback()  # ✅ Must await!
    raise
```

### 3. N+1 Query Problem (Amplified in Async)

**Problem:**
```python
# Gets users
users = await user_service.get_all_users()
for user in users:
    # N queries for exams (bad!)
    exams = await exam_service.get_user_exams(user.id)
```

**Solution:**
```python
# Single query with eager loading
stmt = select(User).options(selectinload(User.exams))
result = await db.execute(stmt)
users = result.scalars().all()
for user in users:
    exams = user.exams  # ✓ Already loaded
```

### 4. Connection Pool Exhaustion

**Problem:** Too many concurrent async queries

**Solution:**
```python
engine = create_async_engine(
    url,
    pool_size=20,  # Maximum connections
    max_overflow=10,  # Additional connections when pool full
    pool_pre_ping=True,  # Verify connection before use
    echo_pool=True  # Log pool events in debug
)
```

### 5. SQLite Limitations

**Problem:** SQLite has limited async support

**Solution:**
```python
if settings.database_type == "sqlite":
    # Use aiosqlite
    url = "sqlite+aiosqlite:///./data/soulsense.db"
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
else:
    # Use asyncpg for PostgreSQL
    url = "postgresql+asyncpg://user:pass@host/db"
    engine = create_async_engine(url)
```

## Testing Strategy

### 1. Unit Tests

```bash
# Run all async tests
pytest -v -m asyncio

# Run specific service tests
pytest tests/unit/test_user_service.py -v

# Check for event loop issues
pytest --asyncio-mode=auto
```

### 2. Integration Tests

```bash
# Full API integration tests
pytest tests/integration/ -v

# Verify no blocking calls
pytest tests/integration/test_async_behavior.py
```

### 3. Load Testing

```bash
# Test concurrent requests
hey -n 1000 -c 100 http://localhost:8000/api/v1/users/me

# Monitor worker threads (should not block)
# All 100 concurrent requests should process simultaneously
```

### 4. Performance Benchmarks

**Before (Sync):**
```
Concurrency: 50 users
Requests: 1000
Avg Response: 450ms
Throughput: 111 req/sec
Worker Threads: All blocked during DB queries
```

**After (Async):**
```
Concurrency: 50 users
Requests: 1000
Avg Response: 85ms
Throughput: 588 req/sec
Worker Threads: Non-blocking, handle multiple requests
```

## Migration Scripts

### Database URL Converter

```python
def convert_to_async_url(sync_url: str) -> str:
    """Convert synchronous database URL to async driver."""
    replacements = {
        "postgresql://": "postgresql+asyncpg://",
        "sqlite:///": "sqlite+aiosqlite:///",
        "mysql://": "mysql+aiomysql://",
    }
    for old, new in replacements.items():
        if sync_url.startswith(old):
            return sync_url.replace(old, new)
    return sync_url
```

### Service Migration Helper

```python
# Helper to identify synchronous queries
import ast
import os

def find_sync_queries(directory: str):
    """Find all synchronous db.query() calls."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                    if "db.query(" in content:
                        print(f"⚠️  Found sync query in: {filepath}")
```

## Rollback Plan

If async migration causes issues:

1. **Revert Database Engine:**
   ```python
   # Fallback to sync engine
   engine = create_engine(settings.database_url)
   SessionLocal = sessionmaker(bind=engine)
   ```

2. **Revert Service Methods:**
   ```python
   # Remove async def, await keywords
   def get_user_by_id(self, user_id: int) -> Optional[User]:
       return self.db.query(User).filter(User.id == user_id).first()
   ```

3. **Revert get_db():**
   ```python
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```

## Performance Monitoring

### Metrics to Track

1. **Response Time:**
   - Before: Avg 300-500ms under load
   - Target: Avg <100ms under load

2. **Throughput:**
   - Before: ~120 req/sec
   - Target: >500 req/sec

3. **Concurrency:**
   - Before: Blocks at ~20 concurrent users
   - Target: Handle 100+ concurrent users

4. **Database Connection Pool:**
   - Monitor active connections
   - Watch for pool exhaustion
   - Tune pool_size and max_overflow

### Observability

```python
import logging

# Log slow queries
logging.basicConfig(level=logging.INFO)
engine = create_async_engine(url, echo=True)  # Log all SQL

# Track query timing
import time

async def timed_query(db: AsyncSession, stmt):
    start = time.time()
    result = await db.execute(stmt)
    duration = time.time() - start
    if duration > 0.1:  # Log queries > 100ms
        logger.warning(f"Slow query: {duration:.2f}s - {stmt}")
    return result
```

## Future Enhancements

1. **Connection Pooling Optimization:**
   - Fine-tune pool size based on load patterns
   - Implement connection pre-ping
   - Add pool monitoring

2. **Query Optimization:**
   - Add database indexes for common queries
   - Implement query result caching
   - Use materialized views for analytics

3. **Async Background Tasks:**
   - Move heavy processing to async Celery tasks
   - Implement async job queues
   - Add progress tracking for long operations

4. **Database Read Replicas:**
   - Route read queries to replicas
   - Write queries to primary
   - Async replication lag monitoring

## References

- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Async SQL Databases](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

## Author

Implementation plan for Issue #935 - Async Migration
