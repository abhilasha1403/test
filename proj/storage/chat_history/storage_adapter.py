import json
from typing import Dict, List, Type

from sqlalchemy.orm import Session

from proj.core.interface.message import (
    BaseMessage,
    ConversationIdentifier,
    MessageIdentifier,
    MessageStorageItem,
    StorageConversation,
    _conversation_to_dict,
    _messages_from_dict,
)
from proj.core.interface.storage import StorageItemAdapter

from .chat_history_db import ChatHistoryEntity, ChatHistoryMessageEntity


class DBStorageConversationItemAdapter(
    StorageItemAdapter[StorageConversation, ChatHistoryEntity]
):
    def to_storage_format(self, item: StorageConversation) -> ChatHistoryEntity:
        message_ids = ",".join(item.message_ids)
        messages = None
        if not item.save_message_independent and item.messages:
            message_dict_list = [_conversation_to_dict(item)]
            messages = json.dumps(message_dict_list, ensure_ascii=False)
        return ChatHistoryEntity(
            conv_uid=item.conv_uid,
            chat_mode=item.chat_mode,
            summary=item.summary or item.get_latest_user_message().content,
            user_name=item.user_name,
            # We not save messages to chat_history table in new design
            messages=messages,
            message_ids=message_ids,
            sys_code=item.sys_code,
        )

    def from_storage_format(self, model: ChatHistoryEntity) -> StorageConversation:
        message_ids = model.message_ids.split(",") if model.message_ids else []
        old_conversations: List[Dict] = (
            json.loads(model.messages) if model.messages else []
        )
        old_messages = []
        save_message_independent = True
        if old_conversations:
            # Load old messages from old conversations, in old design, we save messages to chat_history table
            save_message_independent = False
            old_messages: List[BaseMessage] = _parse_old_conversations(
                old_conversations
            )
        return StorageConversation(
            conv_uid=model.conv_uid,
            chat_mode=model.chat_mode,
            summary=model.summary,
            user_name=model.user_name,
            message_ids=message_ids,
            sys_code=model.sys_code,
            save_message_independent=save_message_independent,
            messages=old_messages,
        )

    def get_query_for_identifier(
        self,
        storage_format: Type[ChatHistoryEntity],
        resource_id: ConversationIdentifier,
        **kwargs,
    ):
        session: Session = kwargs.get("session")
        if session is None:
            raise Exception("session is None")
        return session.query(ChatHistoryEntity).filter(
            ChatHistoryEntity.conv_uid == resource_id.conv_uid
        )


class DBMessageStorageItemAdapter(
    StorageItemAdapter[MessageStorageItem, ChatHistoryMessageEntity]
):
    def to_storage_format(self, item: MessageStorageItem) -> ChatHistoryMessageEntity:
        round_index = item.message_detail.get("round_index", 0)
        message_detail = json.dumps(item.message_detail, ensure_ascii=False)
        return ChatHistoryMessageEntity(
            conv_uid=item.conv_uid,
            index=item.index,
            round_index=round_index,
            message_detail=message_detail,
        )

    def from_storage_format(
        self, model: ChatHistoryMessageEntity
    ) -> MessageStorageItem:
        message_detail = (
            json.loads(model.message_detail) if model.message_detail else {}
        )
        return MessageStorageItem(
            conv_uid=model.conv_uid,
            index=model.index,
            message_detail=message_detail,
        )

    def get_query_for_identifier(
        self,
        storage_format: Type[ChatHistoryMessageEntity],
        resource_id: MessageIdentifier,
        **kwargs,
    ):
        session: Session = kwargs.get("session")
        if session is None:
            raise Exception("session is None")
        return session.query(ChatHistoryMessageEntity).filter(
            ChatHistoryMessageEntity.conv_uid == resource_id.conv_uid,
            ChatHistoryMessageEntity.index == resource_id.index,
        )


def _parse_old_conversations(old_conversations: List[Dict]) -> List[BaseMessage]:
    old_messages_dict = []
    for old_conversation in old_conversations:
        messages = (
            old_conversation["messages"] if "messages" in old_conversation else []
        )
        for message in messages:
            if "data" in message:
                message_data = message["data"]
                additional_kwargs = message_data.get("additional_kwargs", {})
                additional_kwargs["param_value"] = old_conversation.get("param_value")
                additional_kwargs["param_type"] = old_conversation.get("param_type")
                additional_kwargs["model_name"] = old_conversation.get("model_name")
                message_data["additional_kwargs"] = additional_kwargs

        old_messages_dict.extend(messages)

    old_messages: List[BaseMessage] = _messages_from_dict(old_messages_dict)
    return old_messages
