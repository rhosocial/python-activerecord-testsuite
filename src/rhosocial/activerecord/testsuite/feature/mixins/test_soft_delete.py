# src/rhosocial/activerecord/testsuite/feature/mixins/test_soft_delete.py
"""
Test soft delete functionality
"""
from datetime import datetime

import tzlocal


def test_soft_delete_basic(task_model):
    """Test basic soft delete functionality"""
    # Create new record
    t = task_model(title="Test Task")
    t.save()

    # Verify initial state
    assert t.deleted_at is None

    # Record time before deletion
    before_delete = datetime.now(tzlocal.get_localzone())

    # Perform soft delete
    t.delete()

    # Record time after deletion
    after_delete = datetime.now(tzlocal.get_localzone())

    # Verify deletion time is correctly set
    assert t.deleted_at is not None
    assert isinstance(t.deleted_at, datetime)
    assert before_delete <= t.deleted_at <= after_delete

    # Verify database record consistency
    db_task = task_model.query_with_deleted().where(f"{task_model.primary_key()} = ?", (t.id,)).one()
    assert db_task is not None
    assert db_task.deleted_at == t.deleted_at


def test_soft_delete_query(task_model):
    """Test soft delete query functionality"""
    # Create test data
    t1 = task_model(title="Task 1")
    t1.save()
    t2 = (task_model(title="Task 2"))
    t2.save()
    t3 = task_model(title="Task 3")
    t3.save()

    # Delete one record
    t2.delete()

    # Test normal query (should only see undeleted records)
    active_tasks = task_model.find_all()
    assert len(active_tasks) == 2
    assert all(t.deleted_at is None for t in active_tasks)

    # Test query including deleted records
    all_tasks = task_model.query_with_deleted().all()
    assert len(all_tasks) == 3

    # Test query only deleted records
    deleted_tasks = task_model.query_only_deleted().all()
    assert len(deleted_tasks) == 1
    assert deleted_tasks[0].id == t2.id


def test_soft_delete_restore(task_model):
    """Test restoring deleted records"""
    # Create and delete record
    t = task_model(title="Test Task")
    t.save()
    t.delete()

    # Confirm record is soft deleted
    assert t.deleted_at is not None
    assert task_model.find_one(t.id) is None

    # Restore record
    t.restore()

    # Verify restore result
    assert t.deleted_at is None
    restored_task = task_model.find_one(t.id)
    assert restored_task is not None
    assert restored_task.deleted_at is None


def test_soft_delete_identity(task_model):
    """Test identity preservation after soft delete"""
    t = task_model(title="Test Task")
    t.save()
    original_id = t.id

    # Perform soft delete
    t.delete()

    # Verify primary key is not cleared
    assert t.id == original_id

    # Verify deleted record can be queried by primary key
    found = task_model.query_with_deleted().where(f"{task_model.primary_key()} = ?", (original_id,)).one()
    assert found is not None
    assert found.id == original_id

    # Verify deletion can be restored
    t.restore()
    assert t.id == original_id  # Primary key remains unchanged
