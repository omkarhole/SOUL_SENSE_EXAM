import pytest
import uuid
from sqlalchemy import text, select
from api.models import User
from api.services.db_router import PrimarySessionLocal

@pytest.mark.asyncio
async def test_tenant_isolation_rls():
    tenant_1 = str(uuid.uuid4())
    tenant_2 = str(uuid.uuid4())
    
    async with PrimarySessionLocal() as db:
        engine_name = db.bind.engine.name 
        if "postgresql" not in engine_name:
            pytest.skip("RLS tests require PostgreSQL")
            
        # Force RLS for table owners (tests usually run as table owner)
        await db.execute(text("ALTER TABLE users FORCE ROW LEVEL SECURITY"))
            
        # Tenant 1 Context
        await db.execute(text(f"SET app.tenant_id = '{tenant_1}'"))
        user1 = User(username=f"t1_{uuid.uuid4().hex[:8]}", password_hash="test", tenant_id=tenant_1)
        db.add(user1)
        await db.commit()
        
        # Tenant 2 Context
        await db.execute(text(f"SET app.tenant_id = '{tenant_2}'"))
        user2 = User(username=f"t2_{uuid.uuid4().hex[:8]}", password_hash="test", tenant_id=tenant_2)
        db.add(user2)
        await db.commit()
        
        # Verify Tenant 1 isolation
        await db.execute(text(f"SET app.tenant_id = '{tenant_1}'"))
        res1 = await db.execute(select(User).filter(User.tenant_id.in_([tenant_1, tenant_2])))
        users1 = res1.scalars().all()
        assert len(users1) == 1
        assert str(users1[0].tenant_id) == tenant_1
        
        # Verify Tenant 2 isolation
        await db.execute(text(f"SET app.tenant_id = '{tenant_2}'"))
        res2 = await db.execute(select(User).filter(User.tenant_id.in_([tenant_1, tenant_2])))
        users2 = res2.scalars().all()
        assert len(users2) == 1
        assert str(users2[0].tenant_id) == tenant_2
