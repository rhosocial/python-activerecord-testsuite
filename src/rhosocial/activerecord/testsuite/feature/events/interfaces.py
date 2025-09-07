# src/rhosocial/activerecord/testsuite/feature/events/interfaces.py
"""
This file defines the interface (or contract) that a backend's test provider
must adhere to for the "events" feature group.

By defining a standard interface, the generic tests in the testsuite can rely on
these methods being available, regardless of which database backend is actually
running the tests. Each backend must provide a concrete class that implements
these abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Type, List
from rhosocial.activerecord import ActiveRecord


class IEventsProvider(ABC):
    """
    The interface for the provider of the 'events' feature tests.
    """

    @abstractmethod
    def get_test_scenarios(self) -> List[str]:
        """
        Should return a list of scenario names (e.g., ['memory', 'file'])
        that this backend supports for this test group.
        """
        pass

    @abstractmethod
    def setup_event_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the event model under a
        given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def setup_event_tracking_model(self, scenario_name: str) -> Type[ActiveRecord]:
        """
        Should prepare the testing environment for the event tracking model under a
        given scenario and return the configured model class.
        """
        pass

    @abstractmethod
    def cleanup_after_test(self, scenario_name: str):
        """
        Should perform any necessary cleanup after a test has run, such as
        deleting temporary database files.
        """
        pass