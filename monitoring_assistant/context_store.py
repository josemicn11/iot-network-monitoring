chat_contexts = {}
chat_messages = {}


def get_context(chat_id):
    # Return the stored context for a chat or an empty one if it does not exist
    return chat_contexts.get(chat_id, {
        "intent": None,
        "host": None,
    })


def set_context(chat_id, context):
    # Save the current context for a chat
    chat_contexts[chat_id] = context


def clear_context(chat_id):
    # Remove the stored context for a chat
    if chat_id in chat_contexts:
        del chat_contexts[chat_id]


def add_message_id(chat_id, message_id):
    # Store message IDs so old bot messages can be managed later
    if chat_id not in chat_messages:
        chat_messages[chat_id] = []

    chat_messages[chat_id].append(message_id)

    # Keep only the last 50 message IDs for each chat
    chat_messages[chat_id] = chat_messages[chat_id][-50:]


def get_message_ids(chat_id):
    # Return the stored message IDs for a chat
    return chat_messages.get(chat_id, [])


def clear_message_ids(chat_id):
    # Remove all stored message IDs for a chat
    if chat_id in chat_messages:
        del chat_messages[chat_id]