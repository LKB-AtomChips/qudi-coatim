# -*- coding: utf-8 -*-

__all__ = ['AbsorptionInterface']

from abc import abstractmethod

from qudi.core.module import Base


class AbsorptionInterface(Base):
    """ This is an interface for hardware for qudi.
    """
    @property
    @abstractmethod
    def trigger_time(self) -> float:
        """ Read-only property holding the trigger high duration.
        """
        pass

    @abstractmethod
    def send_trigger(self) -> None:
        """ Send a single trigger.
        """
        pass