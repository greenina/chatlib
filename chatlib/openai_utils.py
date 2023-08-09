from asyncio import to_thread
from enum import StrEnum
from typing import TypedDict, Optional, Any

import openai


class ChatGPTModel(StrEnum):
    GPT_3_5_latest = "gpt-3.5-turbo"
    GPT_3_5_16k_latest = "gpt-3.5-turbo-16k"
    GPT_4_latest = "gpt-4"
    GPT_4_32k_latest = "gpt-4-32k"
    GPT_4_0613 = "gpt-4-0613"
    GPT_3_5_0613 = "gpt-3.5-0613"


class ChatGPTRole(StrEnum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatGPTFunctionParameterProperty(TypedDict):
    type: str
    description: Optional[str]
    enum: Optional[list[str]]


class ChatGPTFunctionParameters(TypedDict):
    type: str
    properties: dict[str, ChatGPTFunctionParameterProperty]


class ChatGPTFunctionInfo(TypedDict):
    name: str
    description: Optional[str]
    parameters: ChatGPTFunctionParameters


class ChatGPTParams:
    def __init__(self,
                 temperature: float | None = None,
                 presence_penalty: float | None = None,
                 frequency_penalty: float | None = None,
                 functions: list[ChatGPTFunctionInfo | dict] | None = None
                 ):
        self.temperature = temperature
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.functions = functions

    def to_params(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if value is not None}


def make_chat_completion_message(message: str, role: str, name: str = None) -> dict:
    result = {
        "content": message,
        "role": role
    }

    if name is not None and len(name) > 0:
        result["name"] = name

    return result


async def run_chat_completion(model: str, messages: list[dict], gpt_params: ChatGPTParams,
                                     trial_count: int = 5) -> Any:
    trial = 0
    result = None
    while trial <= trial_count and result is None:
        try:
            result = await to_thread(openai.ChatCompletion.create,
                                     model=model,
                                     messages=messages,
                                     **gpt_params.to_params()
                                     )
        except (openai.error.APIError, openai.error.Timeout, openai.error.APIConnectionError) as e:
            result = None
            trial += 1
            print("OpenAI API error - ", e)
            print("Retry ChatCompletion.")

    return result
