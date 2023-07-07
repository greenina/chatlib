import os
from enum import Enum
from os import getcwd, path
from asyncio import to_thread

import yaml

import openai

from core.chatbot import ResponseGenerator, DialogTurn, RegenerateRequestException


class GPT3StaticPromptResponseGenerator(ResponseGenerator):

    @classmethod
    def from_yml(cls, file_path: str, model: str | None):
        with open(path.join(getcwd(), file_path), 'r') as f:
            yml_data: dict = yaml.load(f, Loader=yaml.FullLoader)
            print(yml_data)

            return cls(
                prompt_base=yml_data["prompt-base"],
                user_prefix=yml_data["user-prefix"],
                system_prefix=yml_data["system-prefix"],
                line_separator=yml_data["line-separator"],
                initial_system_message=yml_data["initial-system-utterance"],
                gpt3_params=yml_data["gpt3-params"],
                gpt3_model=model
            )

    def __init__(self,
                 prompt_base: str,
                 user_prefix: str = "Customer: ",
                 system_prefix: str = "Me: ",
                 line_separator: str = "\n",
                 initial_system_message: str = "How's your day so far?",
                 gpt3_model: str = None,
                 gpt3_params: dict = None
                 ):

        openai.api_key = os.getenv('OPENAI_API_KEY')

        self.prompt_base = prompt_base
        self.user_prefix = user_prefix
        self.system_prefix = system_prefix
        self.line_separator = line_separator
        self.initial_system_message = initial_system_message

        if gpt3_model is not None:
            self.gpt3_model = gpt3_model
        else:
            self.gpt3_model = "text-davinci-002"

        self.max_tokens = 256

        self.gpt3_params = gpt3_params or dict(
            temperature=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.5,
            top_p=1
        )

    def _generate_prompt(self, dialog: list[DialogTurn]) -> str:
        first_user_message_index = next((i for i, v in enumerate(dialog) if v.is_user == True), -1)
        if first_user_message_index >= 0:
            str_arr: list[str] = [self.prompt_base.strip(), " ", dialog[first_user_message_index].message]

            str_arr += [f"{self.line_separator}{self.user_prefix if turn.is_user else self.system_prefix}{turn.message}"
                        for turn in dialog[first_user_message_index + 1:]]

            str_arr.append(f"{self.line_separator}{self.system_prefix}")

            return "".join(str_arr)

        else:
            return self.prompt_base

    async def _get_response_impl(self, dialog: list[DialogTurn]) -> str:
        if len(dialog) == 0:
            return self.initial_system_message
        else:
            prompt = self._generate_prompt(dialog)
            result = await to_thread(openai.Completion.create,
                                     engine=self.gpt3_model,
                                     prompt=prompt,
                                     max_tokens=self.max_tokens,
                                     stop=[self.user_prefix, self.system_prefix],
                                     **self.gpt3_params,
                                     )

            top_choice = result.choices[0]

            if top_choice.finish_reason == 'stop':
                response_text = top_choice.text.strip()
                if len(response_text) > 0:
                    return response_text
                else:
                    raise RegenerateRequestException("Empty text")
            else:
                raise Exception("GPT3 error")


class GPTModel(Enum):
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"


class ChatGPTResponseGenerator(ResponseGenerator):

    def __init__(self,
                 model: str = GPTModel.GPT_4.value,
                 base_instruction: str | None = None,
                 presence_penalty: float | None = None,
                 frequency_penalty: float | None = None,
                 temperature: float | None = None,
                 system_name: str = "system"
                 ):

        self.model = model

        self.gpt_params = dict()

        if presence_penalty is not None:
            self.gpt_params["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            self.gpt_params["frequency_penalty"] = frequency_penalty

        if temperature is not None:
            self.gpt_params["temperature"] = temperature

        self.system_name = system_name

        self.base_instruction = base_instruction if base_instruction is not None else "You are a ChatGPT assistant that is empathetic and supportive."

    def get_instruction(self) -> str | None:
        return self.base_instruction

    async def _get_response_impl(self, dialog: list[DialogTurn]) -> str:
        dialogue_converted = [{
            "content": turn.message,
            "role": "user" if turn.is_user else self.system_name
        } for turn in dialog]

        instruction = self.get_instruction()
        if instruction is not None:
            dialogue_converted.insert(0, {
                "content": instruction,
                "role": "assistant"
            })

        result = await to_thread(openai.ChatCompletion.create,
                                 model=self.model,
                                 messages=dialogue_converted,
                                 **self.gpt_params
                                 )
        top_choice = result.choices[0]

        if top_choice.finish_reason == 'stop':
            response_text = top_choice.message.content
            return response_text
        else:
            raise Exception("ChatGPT error")