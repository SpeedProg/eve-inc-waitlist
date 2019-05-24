from abc import ABC, abstractmethod
from typing import List

class ComConnector(ABC):

    @abstractmethod
    def send_notification(self, name:str , message: str) -> None:
        """ Send the message to the user with the given name.
        """
        raise NotImplemented('send_notification not implemented')

    @abstractmethod
    def move_to_safety(self, names: List[str]) -> None:
        """ Move the users with the given names to the safety channel
        """
        raise NotImplemented('move_to_safety not implemented')

    @abstractmethod
    def register_user(self, name: str, password:str, acc_id: int) -> None:
        """ Register a user with the given username and assign the password
            If the user already exists, the password is reset.
            If the account already has a different user connected, he is removed first
        """
        raise NotImplemented('register_user not implemented')

    @abstractmethod
    def update_user_rights(self, wl_account_id: int, name: str) -> None:
        """ Update user rights
        """
        raise NotImplemented('update_user_rights not implemented')

    @abstractmethod
    def data_updated(self) -> None:
        """Called when coms data was updated
        """
        raise NotImplemented('data_updated not implemented')

    @abstractmethod
    def close(self) -> None:
        """Called when this connector is no longer needed
        """
        raise NotImplemented('close not implemented')

    @abstractmethod
    def get_connect_display_info(self) -> str:
        """Called when you want to get a short string to display connection info to user
        """
        raise NotImplemented('get_connect_display_info not implemented')

    @abstractmethod
    def get_basic_connect_info(self) -> str:
        """Return a basic connection string
        """
        raise NotImplemented('get_basic_connect_info not implemented')


com_connector: ComConnector = None

def get_connector() -> ComConnector:
    global com_connector
    return com_connector

def set_connector(connector: ComConnector) -> None:
    global com_connector
    com_connector = connector

