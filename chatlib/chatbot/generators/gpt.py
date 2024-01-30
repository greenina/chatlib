from functools import cache
from typing import Callable, Awaitable, Any

from jinja2 import Template

from chatlib.chat_completion import ChatCompletionMessage
from chatlib.chatbot import TokenLimitExceedHandler, ChatCompletionResponseGenerator, ChatCompletionParams
from chatlib.openai_utils import GPTChatCompletionAPI, ChatGPTModel


class ChatGPTResponseGenerator(ChatCompletionResponseGenerator):
    @classmethod
    @cache
    def get_api(cls) -> GPTChatCompletionAPI:
        return GPTChatCompletionAPI()

    def __init__(self, model: str = ChatGPTModel.GPT_4_0613, base_instruction: str | Template | None = None,
                 instruction_parameters: dict | None = None,
                 initial_user_message: str | list[ChatCompletionMessage] | None = None,
                 chat_completion_params: ChatCompletionParams | None = None,
                 function_handler: Callable[[str, dict | None], Awaitable[Any]] | None = None,
                 special_tokens: list[tuple[str, str, Any]] | None = None, verbose: bool = False,
                 token_limit_exceed_handler: TokenLimitExceedHandler | None = None, token_limit_tolerance: int = 1024):
        super().__init__(self.get_api(), model, base_instruction, instruction_parameters, initial_user_message,
                         chat_completion_params, function_handler, special_tokens, verbose, token_limit_exceed_handler,
                         token_limit_tolerance)
