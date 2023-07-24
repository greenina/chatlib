from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from chatlib.chatbot import ResponseGenerator, Dialogue

StateType = TypeVar('StateType')


class StateBasedResponseGenerator(ResponseGenerator, Generic[StateType], ABC):

    def __init__(self,
                 initial_state: StateType,
                 initial_state_payload: dict | None = None,
                 verbose: bool = False
                 ):
        self.__current_state = initial_state
        self.__current_state_payload: dict | None = initial_state_payload
        self.__current_generator: ResponseGenerator | None = None
        self.verbose = verbose

    # Return response generator for a state
    @abstractmethod
    async def get_generator(self, state: StateType, payload: dict | None) -> ResponseGenerator:
        pass

    # Calculate the next state based on the current state and the dialog.
    # Return None if the state does not change.
    @abstractmethod
    async def calc_next_state_info(self, current: StateType, dialog: Dialogue) -> tuple[StateType, dict | None] | None:
        pass

    async def _get_response_impl(self, dialog: Dialogue) -> tuple[str, dict | None]:
    
        # Calculate state and update response generator if the state was changed:
        next_state, next_state_payload = await self.calc_next_state_info(self.__current_state, dialog) or (None, None)
        if next_state is not None:
            pre_state = self.__current_state
            self.__current_state = next_state
            self.__current_state_payload = next_state_payload
            self.__current_generator = await self.get_generator(self.__current_state, self.__current_state_payload)
            if self.verbose:
                print("▤▤▤▤▤▤▤▤▤▤▤▤ State transition from {} to {} ▤▤▤▤▤▤▤▤▤▤▤▤▤".format(pre_state, self.__current_state))
        elif self.__current_generator is None:
            self.__current_generator = await self.get_generator(self.__current_state, self.__current_state_payload)

        # Generate response from the child generator:
        return (await self.__current_generator.get_response(dialog))[0], {"state": self.__current_state, "payload": self.__current_state_payload}

    def write_to_json(self, parcel: dict):
        parcel["state"] = self.__current_state
        parcel["state_payload"] = self.__current_state_payload
        parcel["verbose"] = self.verbose

    def restore_from_json(self, parcel: dict):
        self.__current_state = parcel["state"]
        self.__current_state_payload = parcel["state_payload"]
        self.verbose = parcel["verbose"] or False
        self.__current_generator = None
