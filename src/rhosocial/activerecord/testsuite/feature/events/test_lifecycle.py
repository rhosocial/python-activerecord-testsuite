# src/rhosocial/activerecord/testsuite/feature/events/test_lifecycle.py
"""
Event Lifecycle Test Module

This module tests the event lifecycle functionality of the ActiveRecord class.
"""
import pytest
from rhosocial.activerecord.interface import ModelEvent
from rhosocial.activerecord.backend.errors import ValidationError, RecordNotFound, DatabaseError


def test_insert_lifecycle_events(event_model):
    """Test INSERT lifecycle events for new records"""
    instance = event_model(name="test")

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
    instance.save()

    # Verify event sequence
    expected_sequence = [
        ("BEFORE_VALIDATE", 1),
        ("AFTER_VALIDATE", 1),
        ("BEFORE_INSERT", 1),
        ("AFTER_INSERT", 2)
    ]
    assert event_sequence == expected_sequence


def test_update_lifecycle_events(event_model):
    """Test UPDATE lifecycle events for existing records"""
    instance = event_model(name="test")
    instance.save()

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
    instance.save()

    # Verify event sequence
    assert "BEFORE_VALIDATE" in event_sequence
    assert "AFTER_VALIDATE" in event_sequence
    assert ("BEFORE_UPDATE", ["name"]) in event_sequence
    assert ("AFTER_UPDATE", ["name"]) in event_sequence


def test_delete_lifecycle_events(event_model):
    """Test delete lifecycle events"""
    instance = event_model(name="test")
    instance.save()

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
    instance.delete()

    # Verify event sequence and status change
    assert event_sequence == ["BEFORE_DELETE", "AFTER_DELETE"]
    assert instance.status == "deleting"


def test_validation_lifecycle_events(event_model):
    """Test validation lifecycle events"""
    instance = event_model(name="test")

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
    instance.save()

    # Verify name changes before and after validation
    assert validation_data["before"] == " test_name "
    assert validation_data["after"] == "test_name"
    assert instance.name == "test_name"


def test_nested_event_handling(event_model):
    """Test nested event handling"""
    parent = event_model(name="parent")
    child = event_model(name="child")

    event_sequence = []

    def parent_insert_handler(instance, data, **kwargs):
        event_sequence.append("parent_before_insert")
        # Save child object when parent object is saved
        child.save()

    def child_insert_handler(instance, data, **kwargs):
        event_sequence.append("child_before_insert")

    # Register event handlers
    parent.on(ModelEvent.BEFORE_INSERT, parent_insert_handler)
    child.on(ModelEvent.BEFORE_INSERT, child_insert_handler)

    # Save parent object
    parent.save()

    # Verify execution order of nested events
    assert event_sequence == ["parent_before_insert", "child_before_insert"]


def test_event_error_handling(event_model):
    """Test event error handling"""
    instance = event_model(name="test")

    def error_handler(instance, data, **kwargs):
        raise ValueError("Test error in event handler")

    # Register handler that may raise errors
    instance.on(ModelEvent.BEFORE_INSERT, error_handler)

    # Verify error propagates correctly (wrapped in DatabaseError)
    from rhosocial.activerecord.backend.errors import DatabaseError
    with pytest.raises(DatabaseError) as exc_info:
        instance.save()
    assert "Test error in event handler" in str(exc_info.value)


def test_conditional_event_handling(event_model):
    """Test conditional event handling"""
    instance = event_model(name="test", status="draft")
    instance.save()  # First save as new record

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
    instance.save()

    # Test content change
    instance.content = "new content"
    instance.save()

    # Verify only relevant handlers were triggered
    assert handled_events == [
        ("status_change", "published"),
        ("content_change", "new content")
    ]


def test_before_insert_can_modify_data(event_model):
    """Test BEFORE_INSERT event can modify save data"""
    instance = event_model(name="test")

    def modify_data_handler(instance, data, **kwargs):
        # Modify data before insert
        data['name'] = 'modified_name'
        data['status'] = 'auto_status'

    instance.on(ModelEvent.BEFORE_INSERT, modify_data_handler)
    instance.save()

    # Verify the data was modified in the database by querying
    saved = event_model.find_one(instance.id)
    assert saved.name == 'modified_name'
    assert saved.status == 'auto_status'


def test_before_update_can_modify_data(event_model):
    """Test BEFORE_UPDATE event can modify save data"""
    instance = event_model(name="test", status="initial")
    instance.save()

    def modify_data_handler(instance, data, dirty_fields, **kwargs):
        # Modify data before update
        if 'name' in dirty_fields:
            data['status'] = 'name_changed'

    instance.on(ModelEvent.BEFORE_UPDATE, modify_data_handler)

    # Update name
    instance.name = "updated_name"
    instance.save()

    # Verify the data was modified in the database by querying
    saved = event_model.find_one(instance.id)
    assert saved.name == "updated_name"
    assert saved.status == "name_changed"


def test_after_insert_receives_result(event_model):
    """Test AFTER_INSERT event receives QueryResult"""
    instance = event_model(name="test")

    result_data = {}

    def after_insert_handler(instance, data, result, **kwargs):
        result_data['affected_rows'] = result.affected_rows
        result_data['has_data'] = result.data is not None

    instance.on(ModelEvent.AFTER_INSERT, after_insert_handler)
    instance.save()

    assert result_data['affected_rows'] == 1


def test_after_update_receives_result(event_model):
    """Test AFTER_UPDATE event receives QueryResult and dirty_fields"""
    instance = event_model(name="test")
    instance.save()

    result_data = {}

    def after_update_handler(instance, data, dirty_fields, result, **kwargs):
        result_data['affected_rows'] = result.affected_rows
        result_data['dirty_fields'] = sorted(dirty_fields)

    instance.on(ModelEvent.AFTER_UPDATE, after_update_handler)

    instance.name = "updated"
    instance.save()

    assert result_data['affected_rows'] == 1
    assert result_data['dirty_fields'] == ["name"]