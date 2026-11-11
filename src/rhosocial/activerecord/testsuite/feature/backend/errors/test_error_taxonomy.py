# src/rhosocial/activerecord/testsuite/feature/backend/errors/test_error_taxonomy.py
"""Contract the semantic error taxonomy every backend must expose.

These tests import the taxonomy only; they do not touch a database. They
guarantee that a backend installed against this testsuite sees the same
category bases, retry hints, and diagnostic helper as the core package.
"""

from rhosocial.activerecord.backend.errors import (
    BulkOperationError,
    BulkValidationError,
    ConcurrencyError,
    ConnectionError,
    DataError,
    DatabaseError,
    DeadlockError,
    InfrastructureError,
    IntegrityError,
    LockError,
    OperationalError,
    PolicyError,
    QueryError,
    ReadOnlyError,
    RecordError,
    RecordNotFound,
    StaleRecordError,
    TypeConversionError,
    UnaddressableRecordError,
    ValidationError,
    attach_diagnostics,
)


class TestErrorCategories:
    def test_every_error_is_a_database_error(self):
        errors = [
            ValidationError("bad"),
            IntegrityError("dup"),
            TypeConversionError("type"),
            RecordNotFound("missing"),
            UnaddressableRecordError("Keyless", "read"),
            ReadOnlyError("Model", "create"),
            StaleRecordError(model=object, primary_key=1, expected_version=1),
            LockError("lock"),
            DeadlockError("deadlock"),
            ConnectionError("connection"),
            OperationalError("operation"),
            QueryError("query"),
            BulkValidationError([(0, "bad")]),
            BulkOperationError("bulk"),
        ]
        assert all(isinstance(item, DatabaseError) for item in errors)

    def test_data_errors(self):
        assert isinstance(ValidationError("bad"), DataError)
        assert isinstance(IntegrityError("dup"), DataError)
        assert isinstance(TypeConversionError("type"), DataError)

    def test_record_errors(self):
        assert isinstance(RecordNotFound("missing"), RecordError)
        assert isinstance(UnaddressableRecordError("M", "read"), RecordError)

    def test_policy_errors(self):
        assert isinstance(ReadOnlyError("Model", "create"), PolicyError)

    def test_concurrency_errors(self):
        assert isinstance(LockError("lock"), ConcurrencyError)
        assert isinstance(DeadlockError("deadlock"), ConcurrencyError)
        assert isinstance(
            StaleRecordError(model=object, primary_key=1, expected_version=1),
            ConcurrencyError,
        )

    def test_infrastructure_errors(self):
        assert isinstance(ConnectionError("connection"), InfrastructureError)
        assert isinstance(OperationalError("operation"), InfrastructureError)

    def test_bulk_validation_is_both_bulk_and_data(self):
        error = BulkValidationError([(0, "bad")])
        assert isinstance(error, BulkOperationError)
        assert isinstance(error, DataError)


class TestRetryContract:
    def test_concurrency_errors_are_retryable(self):
        assert LockError("lock").retryable is True
        assert DeadlockError("deadlock").retryable is True
        assert (
            StaleRecordError(model=object, primary_key=1, expected_version=1).retryable
            is True
        )

    def test_non_concurrency_errors_are_not_retryable(self):
        assert IntegrityError("dup").retryable is False
        assert ValidationError("bad").retryable is False
        assert ReadOnlyError("Model", "create").retryable is False
        assert ConnectionError("connection").retryable is False
        assert OperationalError("operation").retryable is False

    def test_transient_infrastructure_is_retryable(self):
        error = attach_diagnostics(
            OperationalError("timeout"), operation="select", transient=True
        )
        assert error.transient is True
        assert error.retryable is True


class TestDiagnosticsContract:
    def test_diagnostics_are_attachable(self):
        error = attach_diagnostics(
            IntegrityError("dup"),
            operation="insert",
            sqlstate="23505",
            driver_code=1062,
            backend="mysql",
        )
        assert error.operation == "insert"
        assert error.sqlstate == "23505"
        assert error.driver_code == 1062
        assert error.backend == "mysql"
        assert error.retryable is False
