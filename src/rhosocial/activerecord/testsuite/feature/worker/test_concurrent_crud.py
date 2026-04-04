# src/rhosocial/activerecord/testsuite/feature/worker/test_concurrent_crud.py
"""
Concurrent CRUD tests.

When test cases execute, the environment is already prepared by the Provider:
- Database connected
- Tables created
- WorkerPool fixture available
"""
import pytest
from typing import Type

from rhosocial.activerecord.model import ActiveRecord


class TestConcurrentCRUD:
    """Concurrent CRUD tests"""

    def test_concurrent_create(self, user_class: Type[ActiveRecord],
                                worker_pool, worker_connection_params, worker_tasks):
        """
        Test concurrent record creation.

        user_class: Configured model class
        worker_pool: WorkerPool fixture
        worker_connection_params: Connection parameters dict
        worker_tasks: Task functions module
        """
        n_tasks = 10
        futures = []

        for i in range(n_tasks):
            params = {
                **worker_connection_params,
                'username': f'user_{i}',
                'email': f'user_{i}@test.com'
            }
            futures.append(worker_pool.submit(worker_tasks.create_user_task, params))

        results = [f.result(timeout=30) for f in futures]

        # Verify all results succeeded
        success_count = sum(1 for r in results if r.get('success', False))
        assert success_count == n_tasks

        # Verify all IDs are unique
        user_ids = [r['id'] for r in results if r.get('success', False)]
        assert len(user_ids) == n_tasks
        assert len(set(user_ids)) == n_tasks

    def test_concurrent_read(self, user_class: Type[ActiveRecord],
                              worker_pool, worker_connection_params, worker_tasks):
        """
        Test concurrent record reading.

        Creates a record first, then reads it concurrently.
        """
        # Create a record first
        create_params = {
            **worker_connection_params,
            'username': 'test_user',
            'email': 'test@test.com'
        }
        create_result = worker_pool.submit(worker_tasks.create_user_task, create_params).result(timeout=30)
        assert create_result.get('success', False)
        user_id = create_result['id']

        # Concurrent reads
        n_tasks = 5
        futures = []
        for _ in range(n_tasks):
            params = {
                **worker_connection_params,
                'user_id': user_id
            }
            futures.append(worker_pool.submit(worker_tasks.read_user_task, params))

        results = [f.result(timeout=30) for f in futures]

        # Verify all reads succeeded and data is consistent
        for r in results:
            assert r.get('success', False)
            assert r['username'] == 'test_user'
            assert r['email'] == 'test@test.com'

    def test_concurrent_update(self, user_class: Type[ActiveRecord],
                                worker_pool, worker_connection_params, worker_tasks):
        """
        Test concurrent record updates.
        """
        # Create a record first
        create_params = {
            **worker_connection_params,
            'username': 'update_test',
            'email': 'update@test.com'
        }
        create_result = worker_pool.submit(worker_tasks.create_user_task, create_params).result(timeout=30)
        assert create_result.get('success', False)
        user_id = create_result['id']

        # Concurrent updates
        n_tasks = 5
        futures = []
        for i in range(n_tasks):
            params = {
                **worker_connection_params,
                'user_id': user_id,
                'age': 20 + i  # Different age values
            }
            futures.append(worker_pool.submit(worker_tasks.update_user_task, params))

        results = [f.result(timeout=30) for f in futures]

        # Verify all updates succeeded
        success_count = sum(1 for r in results if r.get('success', False))
        assert success_count == n_tasks

    def test_concurrent_delete(self, user_class: Type[ActiveRecord],
                                worker_pool, worker_connection_params, worker_tasks):
        """
        Test concurrent record deletion.
        """
        # Create multiple records first
        n_create = 10
        create_futures = []
        for i in range(n_create):
            params = {
                **worker_connection_params,
                'username': f'delete_test_{i}',
                'email': f'delete_{i}@test.com'
            }
            create_futures.append(worker_pool.submit(worker_tasks.create_user_task, params))

        create_results = [f.result(timeout=30) for f in create_futures]
        user_ids = [r['id'] for r in create_results if r.get('success', False)]
        assert len(user_ids) == n_create

        # Concurrent deletes
        delete_futures = []
        for user_id in user_ids:
            params = {
                **worker_connection_params,
                'user_id': user_id
            }
            delete_futures.append(worker_pool.submit(worker_tasks.delete_user_task, params))

        delete_results = [f.result(timeout=30) for f in delete_futures]

        # Verify all deletes succeeded
        success_count = sum(1 for r in delete_results if r.get('success', False))
        assert success_count == n_create
