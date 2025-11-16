import json
import sqlite3

from book_downloader.exceptions import MessageInfoNotFoundError, MultipleEntriesForMessageInfoError
from book_downloader.storate.sqlite import connections_factory
from book_downloader.telegram.data.message_info import MessageInfo


class MessageInfoRepository:
    def __init__(self) -> None:
        sqlite3.register_adapter(MessageInfo, self._message_info_to_data)
        sqlite3.register_converter('message_info', self._data_to_message_info)

        with connections_factory() as cursor:
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS message_info (message_id INTEGER PRIMARY KEY, data message_info, updated_at TEXT)'
            )

    @staticmethod
    def _message_info_to_data(message_info: MessageInfo) -> bytes:
        return message_info.model_dump_json().encode(encoding='utf-8')

    @staticmethod
    def _data_to_message_info(data: bytes) -> MessageInfo:
        return MessageInfo(**json.loads(data.decode(encoding='utf-8')))

    def get_message_info(self, message_id: int) -> MessageInfo:
        with connections_factory() as connection:
            cursor = connection.execute(
                'SELECT data FROM message_info WHERE message_id = :message_id', {'message_id': message_id}
            )
            rows = cursor.fetchall()

        if not rows:
            raise MessageInfoNotFoundError(message_id)

        if len(rows) > 1:
            raise MultipleEntriesForMessageInfoError(message_id)

        message_info = rows[0]['data']
        assert isinstance(message_info, MessageInfo)
        return message_info

    def save_message_info(self, message_id: int, info: MessageInfo) -> None:
        with connections_factory() as connection:
            connection.execute(
                'INSERT OR REPLACE INTO message_info (message_id, data, updated_at) VALUES (:message_id, :data, datetime())',
                {'message_id': message_id, 'data': info},
            )


message_info_repository = MessageInfoRepository()
