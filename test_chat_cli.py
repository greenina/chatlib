import asyncio

import openai
from chatlib import cli, env_helper
from chatlib.integration.azure_llama2_utils import AzureLlama2Environment
from chatlib.chatbot import ChatCompletionResponseGenerator
from chatlib.integration.openai_utils import GPTChatCompletionAPI, ChatGPTModel

if __name__ == "__main__":

    asyncio.run(cli.run_chat_loop(ChatCompletionResponseGenerator(
        api=GPTChatCompletionAPI(),
        model=ChatGPTModel.GPT_4_latest,
        base_instruction="You are a helpful assistant that asks the user about their daily activity and feelings. "
                         "Put special token <|Terminate|> at the end of message only if the user wants to finish the conversation.",
        initial_user_message="Hi!",
        special_tokens=[("<|Terminate|>", "terminate", True)]

    ), commands=cli.DEFAULT_TEST_COMMANDS))
