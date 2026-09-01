# src/rhosocial/activerecord/testsuite/feature/events/test_handlers.py
"""
Event Handler Test Module

This module tests the event handler functionality of the ActiveRecord class.
"""
import pytest
from rhosocial.activerecord.interface import ModelEvent


def test_event_handler_registration(event_model):
    """Test event handler registration"""
    instance = event_model(name="test")

    # Register event handlers
    def handler1(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_INSERT, handler="handler1", **kwargs)

    def handler2(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_INSERT, handler="handler2", **kwargs)

    instance.on(ModelEvent.BEFORE_INSERT, handler1)
    instance.on(ModelEvent.BEFORE_INSERT, handler2)

    # Verify handlers are registered
    # Note: DefaultTimestampMixin now registers BEFORE_INSERT instead of BEFORE_SAVE
    assert len(instance._event_handlers[ModelEvent.BEFORE_INSERT]) >= 2
    assert handler1 in instance._event_handlers[ModelEvent.BEFORE_INSERT]
    assert handler2 in instance._event_handlers[ModelEvent.BEFORE_INSERT]


def test_event_handler_removal(event_model):
    """Test event handler removal"""
    instance = event_model(name="test")

    def handler(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_INSERT, handler="handler", **kwargs)

    # Register then remove handler
    instance.on(ModelEvent.BEFORE_INSERT, handler)
    assert handler in instance._event_handlers[ModelEvent.BEFORE_INSERT]

    instance.off(ModelEvent.BEFORE_INSERT, handler)
    assert handler not in instance._event_handlers[ModelEvent.BEFORE_INSERT]


def test_event_handler_execution(event_model):
    """Test event handler execution"""
    instance = event_model(name="test")
    execution_order = []

    def handler1(instance, **kwargs):
        execution_order.append("handler1")
        instance.log_event(ModelEvent.BEFORE_INSERT, handler="handler1", **kwargs)

    def handler2(instance, **kwargs):
        execution_order.append("handler2")
        instance.log_event(ModelEvent.BEFORE_INSERT, handler="handler2", **kwargs)

    instance.on(ModelEvent.BEFORE_INSERT, handler1)
    instance.on(ModelEvent.BEFORE_INSERT, handler2)

    # Trigger event (INSERT for new record)
    instance.save()

    # Verify execution order
    assert execution_order == ["handler1", "handler2"]

    # Verify event logs
    logs = instance.get_event_logs()
    before_insert_logs = [log for log in logs if log[0] == ModelEvent.BEFORE_INSERT]
    assert len(before_insert_logs) >= 2
    assert before_insert_logs[0][1]["handler"] == "handler1"
    assert before_insert_logs[1][1]["handler"] == "handler2"


def test_multiple_event_types(event_model):
    """Test multiple event types"""
    instance = event_model(name="test")

    def insert_handler(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_INSERT, type="insert", **kwargs)

    def delete_handler(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_DELETE, type="delete", **kwargs)

    def validate_handler(instance, **kwargs):
        instance.log_event(ModelEvent.BEFORE_VALIDATE, type="validate", **kwargs)

    # Register different types of event handlers
    instance.on(ModelEvent.BEFORE_INSERT, insert_handler)
    instance.on(ModelEvent.BEFORE_DELETE, delete_handler)
    instance.on(ModelEvent.BEFORE_VALIDATE, validate_handler)

    # Save record to trigger events
    instance.save()

    # Verify event records
    logs = instance.get_event_logs()
    insert_events = [log for log in logs if log[1].get("type") == "insert"]
    assert len(insert_events) == 1


def test_event_data_passing(event_model):
    """Test event data passing"""
    instance = event_model(name="test")
    received_data = {}

    def handler(instance, **kwargs):
        received_data.update(kwargs)
        instance.log_event(ModelEvent.BEFORE_INSERT, **kwargs)

    instance.on(ModelEvent.BEFORE_INSERT, handler)

    # Trigger event with data
    instance._trigger_event(ModelEvent.BEFORE_INSERT, custom_data="test", data={})

    # Verify data passing
    assert received_data["custom_data"] == "test"

    # Verify event logs
    logs = instance.get_event_logs()
    before_insert_logs = [log for log in logs if log[0] == ModelEvent.BEFORE_INSERT]
    assert before_insert_logs[0][1]["custom_data"] == "test"


def test_insert_update_handlers_separate(event_model):
    """Test that INSERT and UPDATE handlers are triggered separately"""
    instance = event_model(name="test")

    insert_called = []
    update_called = []

    def on_before_insert(instance, data, **kwargs):
        insert_called.append("before_insert")

    def on_before_update(instance, data, dirty_fields, **kwargs):
        update_called.append("before_update")

    instance.on(ModelEvent.BEFORE_INSERT, on_before_insert)
    instance.on(ModelEvent.BEFORE_UPDATE, on_before_update)

    # First save (INSERT)
    instance.save()
    assert len(insert_called) == 1
    assert len(update_called) == 0

    # Second save (UPDATE)
    instance.name = "updated"
    instance.save()
    assert len(insert_called) == 1
    assert len(update_called) == 1