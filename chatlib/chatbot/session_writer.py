import json
import shutil
from abc import ABC, abstractmethod
from os import path, getcwd, makedirs

import jsonlines

from .types import DialogueTurn, Dialogue


class SessionWriterBase(ABC):

    @abstractmethod
    def exists(self, session_id: str)->bool:
        pass

    @abstractmethod
    def write_turn(self, session_id: str, turn: DialogueTurn):
        pass

    @abstractmethod
    def delete_turn(self, session_id: str, turn_id: str)->DialogueTurn | None:
        pass

    @abstractmethod
    def read_dialogue(self, session_id: str) -> Dialogue:
        pass

    @abstractmethod
    def write_dialogue(self, session_id: str, dialog: Dialogue):
        pass

    @abstractmethod
    def write_session_info(self, session_id, session_info: dict):
        pass

    @abstractmethod
    def read_session_info(self, session_id) -> dict:
        pass

    @abstractmethod
    def clear_data(self, session_id) -> bool:
        pass


class SessionFileWriter(SessionWriterBase):

    @staticmethod
    def __get_dialogue_directory_path(session_id: str, create: bool = False) -> str:
        p = path.join(getcwd(), "data/sessions/", session_id)
        if not path.exists(p) and create:
            makedirs(p)
        return p

    @staticmethod
    def __get_dialogue_file_path(session_id: str, create_dir: bool = False) -> str:
        dir_path = SessionFileWriter.__get_dialogue_directory_path(session_id, create=create_dir)
        return path.join(dir_path, "dialogue.jsonl")

    @staticmethod
    def __get_session_info_file_path(session_id: str, create_dir: bool = False) -> str:
        dir_path = SessionFileWriter.__get_dialogue_directory_path(session_id, create_dir)
        return path.join(dir_path, "info.json")

    def exists(self, session_id: str) -> bool:
        return path.exists(self.__get_session_info_file_path(session_id))

    def write_session_info(self, session_id, session_info: dict):
        with open(self.__get_session_info_file_path(session_id, True), "w", encoding='utf-8') as f:
            json.dump(session_info, f, indent=2)

    def read_session_info(self, session_id) -> dict:
        with open(self.__get_session_info_file_path(session_id), 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_turn(self, session_id: str, turn: DialogueTurn):
        with jsonlines.open(self.__get_dialogue_file_path(session_id, True), 'a') as writer:
            writer.write(turn.__dict__)


    def delete_turn(self, session_id: str, turn_id: str) -> DialogueTurn | None:
        dialogue = self.read_dialogue(session_id)
        deleted_turn = None
        for i, turn in enumerate(dialogue):
            if turn.id == turn_id:
                deleted_turn = dialogue.pop(i)
                break

        if deleted_turn is not None:
            self.write_dialogue(session_id, dialogue)

        return deleted_turn

    def read_dialogue(self, session_id: str) -> Dialogue | None:
        fp = self.__get_dialogue_file_path(session_id)
        if path.exists(fp):
            with jsonlines.open(fp, "r") as reader:
                return [DialogueTurn(**row) for row in reader]
        else:
            return None

    def write_dialogue(self, session_id: str, dialog: Dialogue):
        fp = self.__get_dialogue_file_path(session_id)
        if path.exists(fp):
            with jsonlines.open(fp, "w") as writer:
                writer.write_all([turn.__dict__ for turn in dialog])

    def clear_data(self, session_id) -> bool:
        dir_path = SessionFileWriter.__get_dialogue_directory_path(session_id)
        if path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                return True
            except OSError as e:
                print(f"Error while removing the session directory {dir_path} - {e}")
                return False
        else:
            return False


session_writer = SessionFileWriter()
