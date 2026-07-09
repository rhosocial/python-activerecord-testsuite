# src/rhosocial/activerecord/testsuite/feature/events/test_lifecycle_async.py
"""
Event Lifecycle Test Module

This module tests the event lifecycle functionality of the ActiveRecord class.
"""
import pytest
from rhosocial.activerecord.interface import ModelEvent
from rhosocial.activerecord.model import ActiveRecord


async def test_insert_lifecycle_events(async_event_model):
    """Test INSERT lifecycle events for new records"""
    instance = async_event_model(name="test")

    # Record event trigger sequence
    event_sequence = []

    def on_before_validate(instance, **kwargs):
        event_sequence.append(("BEFORE_VALIDATE", instance.revision))

    def on_after_validate(instance, **kwargs):
        event_sequence.append(("AFTER_VALIDATE", instance.revision))

    def on_before_insert(instance, data, **kwargs):
        event_sequence.append(("BEFORE_INSERT", instance.revision))
        instance.revision += 1

    def on_after_insert(instance, data, result, **kwargs):
        event_sequence.append(("AFTER_INSERT", instance.revision))

    # Register all event handlers
    instance.on(ModelEvent.BEFORE_VALIDATE, on_before_validate)
    instance.on(ModelEvent.AFTER_VALIDATE, on_after_validate)
    instance.on(ModelEvent.BEFORE_INSERT, on_before_insert)
    instance.on(ModelEvent.AFTER_INSERT, on_after_insert)

    # Save record (INSERT for new record)
    await instance.save()

    # Verify event sequence
    expected_sequence = [
        ("BEFORE_VALIDATE", 1),
        ("AFTER_VALIDATE", 1),
        ("BEFORE_INSERT", 1),
        ("AFTER_INSERT", 2)
    ]
    assert event_sequence == expected_sequence


async def test_update_lifecycle_events(async_event_model):
    """Test UPDATE lifecycle events for existing records"""
    instance = async_event_model(name="test")
    await instance.save()

    # Reset event sequence
    event_sequence = []

    def on_before_validate(instance, **kwargs):
        event_sequence.append("BEFORE_VALIDATE")

    def on_after_validate(instance, **kwargs):
        event_sequence.append("AFTER_VALIDATE")

    def on_before_update(instance, data, dirty_fields, **kwargs):
        event_sequence.append(("BEFORE_UPDATE", sorted(dirty_fields)))

    def on_after_update(instance, data, dirty_fields, result, **kwargs):
        event_sequence.append(("AFTER_UPDATE", sorted(dirty_fields)))

    # Register all event handlers
    instance.on(ModelEvent.BEFORE_VALIDATE, on_before_validate)
    instance.on(ModelEvent.AFTER_VALIDATE, on_after_validate)
    instance.on(ModelEvent.BEFORE_UPDATE, on_before_update)
    instance.on(ModelEvent.AFTER_UPDATE, on_after_update)

    # Update record
    instance.name = "updated"
    await instance.save()

    # Verify event sequence
    assert "BEFORE_VALIDATE" in event_sequence
    assert "AFTER_VALIDATE" in event_sequence
    assert ("BEFORE_UPDATE", ["name"]) in event_sequence
    assert ("AFTER_UPDATE", ["name"]) in event_sequence


async def test_delete_lifecycle_events(async_event_model):
    """Test delete lifecycle events"""
    instance = async_event_model(name="test")
    await instance.save()

    event_sequence = []

    def on_before_delete(instance, **kwargs):
        event_sequence.append("BEFORE_DELETE")
        instance.status = "deleting"

    def on_after_delete(instance, **kwargs):
        event_sequence.append("AFTER_DELETE")

    # Register delete event handlers
    instance.on(ModelEvent.BEFORE_DELETE, on_before_delete)
    instance.on(ModelEvent.AFTER_DELETE, on_after_delete)

    # Delete record
    await instance.delete()

    # Verify event sequence and status change
    assert event_sequence == ["BEFORE_DELETE", "AFTER_DELETE"]
    assert instance.status == "deleting"


async def test_validation_lifecycle_events(async_event_model):
    """Test validation lifecycle events"""
    instance = async_event_model(name="test")

    validation_data = {}

    def on_before_validate(instance, **kwargs):
        validation_data["before"] = instance.name
        instance.name = instance.name.strip()

    def on_after_validate(instance, **kwargs):
        validation_data["after"] = instance.name

    # Register validation event handlers
    instance.on(ModelEvent.BEFORE_VALIDATE, on_before_validate)
    instance.on(ModelEvent.AFTER_VALIDATE, on_after_validate)

    # Create instance with name containing spaces and save
    instance.name = " test_name "
    await instance.save()

    # Verify name changes before and after validation
    assert validation_data["before"] == " test_name "
    assert validation_data["after"] == "test_name"
    assert instance.name == "test_name"


async def test_nested_event_handling(async_event_model):
    """Test nested event handling"""
    parent = async_event_model(name="parent")
    child = async_event_model(name="child")

    event_sequence = []

    async def parent_insert_handler(instance, data, **kwargs):
        event_sequence.append("parent_before_insert")
        # Save child object when parent object is saved
        await child.save()

    def child_insert_handler(instance, data, **kwargs):
        event_sequence.append("child_before_insert")

    # Register event handlers
    parent.on(ModelEvent.BEFORE_INSERT, parent_insert_handler)
    child.on(ModelEvent.BEFORE_INSERT, child_insert_handler)

    # Save parent object
    await parent.save()

    # Verify execution order of nested events
    assert event_sequence == ["parent_before_insert", "child_before_insert"]


async def test_event_error_handling(async_event_model):
    """Test event error handling"""
    instance = async_event_model(name="test")

    def error_handler(instance, data, **kwargs):
        raise ValueError("Test error in event handler")

    # Register handler that may raise errors
    instance.on(ModelEvent.BEFORE_INSERT, error_handler)

    # Verify error propagates correctly (wrapped in DatabaseError)
    from rhosocial.activerecord.backend.errors import DatabaseError
    with pytest.raises(DatabaseError) as exc_info:
        await instance.save()
    assert "Test error in event handler" in str(exc_info.value)


async def test_conditional_event_handling(async_event_model):
    """Test conditional event handling"""
    instance = async_event_model(name="test", status="draft")
    await instance.save()  # First save as new record

    handled_events = []

    def status_change_handler(instance, data, dirty_fields, **kwargs):
        if "status" in dirty_fields:
            handled_events.append(("status_change", instance.status))

    def content_change_handler(instance, data, dirty_fields, **kwargs):
        if "content" in dirty_fields:
            handled_events.append(("content_change", instance.content))

    # Register conditional handlers for UPDATE events
    instance.on(ModelEvent.BEFORE_UPDATE, status_change_handler)
    instance.on(ModelEvent.BEFORE_UPDATE, content_change_handler)

    # Test status change
    instance.status = "published"
    await instance.save()

    # Test content change
    instance.content = "new content"
    await instance.save()

    # Verify only relevant handlers were triggered
    assert handled_events == [
        ("status_change", "published"),
        ("content_change", "new content")
    ]


async def test_before_insert_can_modify_data(async_event_model):
    """Test BEFORE_INSERT event can modify save data"""
    instance = async_event_model(name="test")

    def modify_data_handler(instance, data, **kwargs):
        # Modify data before insert
        data['name'] = 'modified_name'
        data['status'] = 'auto_status'

    instance.on(ModelEvent.BEFORE_INSERT, modify_data_handler)
    await instance.save()

    # Verify the data was modified in the database by querying
    saved = await async_event_model.find_one(instance.id)
    assert saved.name == 'modified_name'
    assert saved.status == 'auto_status'


async def test_before_update_can_modify_data(async_event_model):
    """Test BEFORE_UPDATE event can modify save data"""
    instance = async_event_model(name="test", status="initial")
    await instance.save()

    def modify_data_handler(instance, data, dirty_fields, **kwargs):
        # Modify data before update
        if 'name' in dirty_fields:
            data['status'] = 'name_changed'

    instance.on(ModelEvent.BEFORE_UPDATE, modify_data_handler)

    # Update name
    instance.name = "updated_name"
    await instance.save()

    # Verify the data was modified in the database by querying
    saved = await async_event_model.find_one(instance.id)
    assert saved.name == "updated_name"
    assert saved.status == "name_changed"


async def test_after_insert_receives_result(async_event_model):
    """Test AFTER_INSERT event receives QueryResult"""
    instance = async_event_model(name="test")

    result_data = {}

    def after_insert_handler(instance, data, result, **kwargs):
        result_data['affected_rows'] = result.affected_rows
        result_data['has_data'] = result.data is not None

    instance.on(ModelEvent.AFTER_INSERT, after_insert_handler)
    await instance.save()

    assert result_data['affected_rows'] == 1


async def test_after_update_receives_result(async_event_model):
    """Test AFTER_UPDATE event receives QueryResult and dirty_fields"""
    instance = async_event_model(name="test")
    await instance.save()

    result_data = {}

    def after_update_handler(instance, data, dirty_fields, result, **kwargs):
        result_data['affected_rows'] = result.affected_rows
        result_data['dirty_fields'] = sorted(dirty_fields)

    instance.on(ModelEvent.AFTER_UPDATE, after_update_handler)

    instance.name = "updated"
    await instance.save()

    assert result_data['affected_rows'] == 1
    assert result_data['dirty_fields'] == ["name"]


async def test_sync_callback_receives_active_record_instance(async_event_model):
    """Test that callback receives ActiveRecord instance for async model"""
    instance = async_event_model(name="test")

    received_types = []

    def handler(instance_arg, **kwargs):
        received_types.append(type(instance_arg).__name__)

    instance.on(ModelEvent.BEFORE_INSERT, handler)
    instance.on(ModelEvent.AFTER_INSERT, handler)
    await instance.save()

    # Verify the instance is the same object
    assert all(t == type(instance).__name__ for t in received_types)
    # Verify it's an AsyncActiveRecord subclass
    from rhosocial.activerecord.model import AsyncActiveRecord
    assert isinstance(instance, AsyncActiveRecord)


async def test_callback_instance_is_same_object(async_event_model):
    """Test that callback receives the exact same instance object"""
    instance = async_event_model(name="test")

    received_instances = []

    def handler(instance_arg, **kwargs):
        received_instances.append(instance_arg)

    instance.on(ModelEvent.BEFORE_INSERT, handler)
    await instance.save()

    # Verify the instance received in callback is the exact same object
    assert len(received_instances) == 1
    assert received_instances[0] is instance  # Same identity (using 'is')