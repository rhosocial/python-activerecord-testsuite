# src/rhosocial/activerecord/testsuite/feature/mixins/test_soft_delete.py
"""
Test soft delete functionality
"""
import pytest

from datetime import datetime, timezone


@pytest.mark.asyncio


async def test_soft_delete_basic(task_model):
    """Test basic soft delete functionality"""
    from datetime import timedelta
    # Create new record
    t = task_model(title="Test Task")
    await t.save()

    # Verify initial state
    assert t.deleted_at is None

    # Record time before deletion
    before_delete = datetime.now(timezone.utc)

    # Perform soft delete
    await t.delete()

    # Record time after deletion
    after_delete = datetime.now(timezone.utc)

    # Verify deletion time is correctly set
    assert t.deleted_at is not None
    assert isinstance(t.deleted_at, datetime)
    assert before_delete <= t.deleted_at <= after_delete
    utc_plus_8 = timezone(timedelta(hours=8))
    assert t.deleted_at.astimezone(utc_plus_8).utcoffset() == timedelta(hours=8)

    # Verify database record consistency
    db_task = task_model.query_with_deleted().where(f"{task_model.primary_key()} = ?", (t.id,)).one()
    assert db_task is not None
    assert db_task.deleted_at == t.deleted_at



@pytest.mark.asyncio



async def test_soft_delete_query(task_model):
    """Test soft delete query functionality"""
    # Create test data
    t1 = task_model(title="Task 1")
    await t1.save()
    t2 = (task_model(title="Task 2"))
    await t2.save()
    t3 = task_model(title="Task 3")
    await t3.save()

    # Delete one record
    await t2.delete()

    # Test normal query (should only see undeleted records)
    active_tasks = await task_model.find_all()
    assert len(active_tasks) == 2
    assert all(t.deleted_at is None for t in active_tasks)

    # Test query including deleted records
    all_tasks = task_model.query_with_deleted().all()
    assert len(all_tasks) == 3

    # Test query only deleted records
    deleted_tasks = task_model.query_only_deleted().all()
    assert len(deleted_tasks) == 1
    assert deleted_tasks[0].id == t2.id


@pytest.mark.asyncio


async def test_soft_delete_restore(task_model):
    """Test restoring deleted records"""
    # Create and delete record
    t = task_model(title="Test Task")
    await t.save()
    await t.delete()

    # Confirm record is soft deleted
    assert t.deleted_at is not None
    assert await task_model.find_one(t.id) is None

    # Restore record
    t.restore()

    # Verify restore result
    assert t.deleted_at is None
    restored_task = await task_model.find_one(t.id)
    assert restored_task is not None
    assert restored_task.deleted_at is None


@pytest.mark.asyncio


async def test_soft_delete_identity(task_model):
    """Test identity preservation after soft delete"""
    t = task_model(title="Test Task")
    await t.save()
    original_id = t.id

    # Perform soft delete
    await t.delete()

    # Verify primary key is not cleared
    assert t.id == original_id

    # Verify deleted record can be queried by primary key
    found = task_model.query_with_deleted().where(f"{task_model.primary_key()} = ?", (original_id,)).one()
    assert found is not None
    assert found.id == original_id

    # Verify deletion can be restored
    t.restore()
    assert t.id == original_id  # Primary key remains unchanged
