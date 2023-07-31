import json
from asyncio import to_thread
from jinja2 import Template, Environment, BaseLoader
from typing import Awaitable, Any, Callable

import openai

from chatlib import dict_utils
from chatlib.chatbot import ResponseGenerator, Dialogue, DialogueTurn
from chatlib.openai_utils import ChatGPTModel, ChatGPTRole, \
    ChatGPTParams, \
    make_chat_completion_message, run_chat_completion


class ChatGPTResponseGenerator(ResponseGenerator):
    __jinja_env = None

    @classmethod
    def __get_jinja_env(cls: 'ChatGPTResponseGenerator') -> Environment:
        if cls.__jinja_env is None:
            cls.__jinja_env = Environment(loader=BaseLoader())
        return cls.__jinja_env

    @classmethod
    def convert_to_jinja_template(cls: 'ChatGPTResponseGenerator', template_string: str) -> Template:
        return cls.__get_jinja_env().get_template(template_string)

    def __init__(self,
                 model: str = ChatGPTModel.GPT_4_latest,
                 base_instruction: str | Template | None = None,
                 instruction_parameters: dict | None = None,
                 initial_user_message: str | list[dict] | None = None,
                 params: ChatGPTParams | None = None,
                 function_handler: Callable[[str, dict | None], Awaitable[Any]] | None = None,
                 special_tokens: list[tuple[str, str, Any]] | None = None,
                 verbose: bool = False
                 ):

        self.model = model

        self.gpt_params = params or ChatGPTParams()

        self.initial_user_message = initial_user_message

        self.__special_tokens = special_tokens

        self.__base_instruction = base_instruction if base_instruction is not None else "You are a ChatGPT assistant that is empathetic and supportive."

        self.__instruction_parameters = instruction_parameters

        self.__resolve_instruction()

        self.function_handler = function_handler

        self.verbose = verbose

    def __resolve_instruction(self):
        if isinstance(self.__base_instruction, Template):
            if self.__instruction_parameters is not None:
                self.__instruction = self.__base_instruction.render(**self.__instruction_parameters)
            else:
                self.__instruction = self.__base_instruction.render()
        else:
            self.__instruction = self.__base_instruction

    @property
    def base_instruction(self)->str:
        return self.__base_instruction

    @base_instruction.setter
    def base_instruction(self, new: str):
        self.__base_instruction = new
        self.__resolve_instruction()

    def update_instruction_parameters(self, params: dict):
        if self.__instruction_parameters is not None:
            self.__instruction_parameters.update(params)
        else:
            self.__instruction_parameters = params
        self.__resolve_instruction()

    async def _get_response_impl(self, dialog: Dialogue) -> tuple[str, dict | None]:
        message, metadata = await self.__run_chatgpt(dialog)
        if self.__special_tokens is not None and len(self.__special_tokens) > 0:
            original_message = message
            for token, key, value in self.__special_tokens:
                if token in message:
                    message = message.replace(token, "")
                    metadata = dict_utils.set_nested_value(metadata, key, value)
                    metadata = dict_utils.set_nested_value(metadata, ["chatgpt", "original_message"], original_message)

        return message, metadata

    async def __run_chatgpt(self, dialog: Dialogue) -> tuple[str, dict | None]:
        dialogue_converted = []
        for turn in dialog:
            function_messages = dict_utils.get_nested_value(turn.metadata, ["chatgpt", "function_messages"])
            if function_messages is not None:
                dialogue_converted.extend(turn.metadata["chatgpt"]["function_messages"])

            original_message = dict_utils.get_nested_value(turn.metadata, ["chatgpt", "original_message"])
            dialogue_converted.append(
                make_chat_completion_message(original_message if original_message is not None else turn.message,
                                             ChatGPTRole.USER if turn.is_user else ChatGPTRole.ASSISTANT))

        instruction = self.__instruction
        if instruction is not None:

            instruction_turn = make_chat_completion_message(instruction, ChatGPTRole.SYSTEM)

            messages = [instruction_turn]
            if self.initial_user_message is not None:
                if isinstance(self.initial_user_message, str):
                    messages.append(make_chat_completion_message(self.initial_user_message, ChatGPTRole.USER))
                else:
                    messages.extend(self.initial_user_message)

            messages.extend(dialogue_converted)
        else:
            messages = dialogue_converted

        result = await run_chat_completion(self.model, messages, self.gpt_params)

        top_choice = result.choices[0]

        if top_choice.finish_reason == 'stop':
            response_text = top_choice.message.content
            return response_text, None
        elif top_choice.finish_reason == 'function_call':
            function_call_info = top_choice["message"]["function_call"]
            function_name = function_call_info["name"]
            function_args = json.loads(function_call_info["arguments"])

            if self.verbose: print(f"Call function - {function_name} ({function_args})")

            function_call_result = await self.function_handler(function_name, function_args)
            function_turn = make_chat_completion_message(function_call_result, ChatGPTRole.FUNCTION, name=function_name)
            function_messages = [top_choice.message, function_turn]
            dialogue_with_func_result = messages + function_messages

            new_result = await run_chat_completion(self.model, dialogue_with_func_result, self.gpt_params)

            top_choice = new_result.choices[0]
            if top_choice.finish_reason == 'stop':
                response_text = top_choice.message.content
                return response_text, {
                    "chatgpt": {
                        "function_messages": function_messages
                    }
                }
            else:
                print("Shouldn't reach here")

        else:
            raise Exception(f"ChatGPT error - {top_choice.finish_reason}")

    def write_to_json(self, parcel: dict):
        parcel["model"] = self.model
        parcel["gpt_params"] = self.gpt_params.to_params()
        parcel["initial_user_message"] = self.initial_user_message
        parcel["base_instruction"] = self.__base_instruction
        parcel["instruction_parameters"] = self.__instruction_parameters
        parcel["verbose"] = self.verbose

    def restore_from_json(self, parcel: dict):
        self.model = parcel["model"]
        self.gpt_params = ChatGPTParams(**parcel["gpt_params"])
        self.initial_user_message = parcel["initial_user_message"]
        self.__base_instruction = parcel["base_instruction"]
        self.__instruction_parameters = parcel["instruction_parameters"]
        self.verbose = parcel["verbose"]
        self.__resolve_instruction()
