from typing import Optional

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from influx_client import MonitoringInfluxClient
from assistant_core import process_user_message
from context_store import get_context, set_context


WELCOME_TEXT = (
    "¡Hola! Soy tu asistente de monitorización :)\n\n"
    "Puedo ayudarte a consultar información sobre tu red "
    "y los dispositivos conectados a ella.\n\n"
    "Usa /help para ver ejemplos de cosas que me puedes preguntar."
)

MANUAL_TEXT = (
    "MANUAL DE USO DEL ASISTENTE\n\n"
    "Comandos disponibles:\n"
    "/start - iniciar conversación\n"
    "/restart - reiniciar el contexto de este chat\n"
    "/help - ver este manual\n\n"
    "Hosts soportados:\n"
    "- pc / ordenador / asus\n"
    "- raspberry / raspi\n\n"
    "Ejemplos de consultas:\n"
    "- dime el estado del pc\n"
    "- dime como se encuentra la raspberry\n"
    "- cual es la carga actual del pc\n"
    "- cuanta ram usa la raspberry\n"
    "- como esta el disco del pc\n"
    "- dime los clientes activos ahora mismo\n"
    "- dime el estado del trafico dns hoy\n"
    "- que host tiene menos memoria ram disponible\n"
    "- que host va peor de disco\n"
    "- cuales son los dominios mas consultados\n"
)


def detect_smalltalk(text: str) -> Optional[str]:
    # Handle simple conversational messages
    normalized = text.lower().strip()

    greeting_clues = [
        "hola",
        "holi",
        "hey",
        "buenas",
        "buenos dias",
        "buenos días",
        "buenas tardes",
        "buenas noches",
        "que tal",
        "qué tal",
        "como estas",
        "cómo estás",
        "como va",
        "cómo va",
        "como te encuentras",
    ]

    if normalized in greeting_clues:
        return WELCOME_TEXT

    if any(clue in normalized for clue in [
        "gracias",
        "muchas gracias",
        "perfecto gracias",
    ]):
        return "¡De nada!"

    if any(clue in normalized for clue in [
        "adios",
        "adiós",
        "hasta luego",
        "nos vemos",
    ]):
        return "¡Hasta luego! Cuando quieras seguimos."

    return None


def detect_capabilities_request(text: str) -> Optional[str]:
    # Detect questions about what the assistant can do
    normalized = text.lower().strip()

    capability_clues = {
        "en que me puedes ayudar",
        "en qué me puedes ayudar",
        "que te puedo preguntar",
        "qué te puedo preguntar",
        "que cosas te puedo preguntar",
        "qué cosas te puedo preguntar",
        "que me puedes preguntar",
        "qué me puedes preguntar",
        "que puedes hacer",
        "qué puedes hacer",
        "sobre que me puedes informar",
        "sobre qué me puedes informar",
        "que informacion me puedes dar",
        "qué información me puedes dar",
        "sobre que cosas me puedes responder",
        "sobre qué cosas me puedes responder",
        "de que me puedes informar",
        "de qué me puedes informar",
    }

    if normalized in capability_clues:
        return (
            "Puedo darte información sobre estas áreas:\n\n"
            "• Estado general de hosts: PC y Raspberry\n"
            "• CPU/carga actual y comparaciones\n"
            "• RAM: uso, disponible y comparaciones\n"
            "• Disco: uso, estado y comparaciones\n"
            "• DNS: estado general del tráfico\n"
            "• Consultas DNS totales, QPS, bloqueadas y cacheadas\n"
            "• Clientes activos y clientes con más consultas\n"
            "• Dominios más consultados\n"
            "• Consultas a un dominio concreto, por ejemplo google.com\n"
            "• Tipos de consulta DNS y su distribución\n"
            "• Comparativa entre tráfico cacheado y reenviado\n\n"
            "También puedes usar /help para ver ejemplos de consultas."
        )

    return None


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # Send the initial welcome message
    await update.message.reply_text(
        "¡Hola! Soy Mordisquitos, tu asistente de monitorización :)\n\n"
        "Puedo ayudarte a consultar el estado de los hosts y del DNS, "
        "entre muchas otras cosas.\n\n"
        "Usa /help para ver ejemplos de posibles consultas "
        "y /restart para reiniciar la conversación."
    )


async def restart_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # Clear the stored conversation context
    chat_id = update.effective_chat.id
    set_context(chat_id, {})

    await update.message.reply_text(
        "Conversación reiniciada. "
        "Ya no conservo contexto previo de este chat."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # Show the assistant manual
    await update.message.reply_text(MANUAL_TEXT)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # Ignore messages without text
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    influx_client = context.application.bot_data["influx_client"]

    thinking_msg = await update.message.reply_text("Pensando...")

    try:
        last_context = get_context(chat_id)

        # Handle questions about the assistant capabilities
        capabilities_response = detect_capabilities_request(user_input)

        if capabilities_response:
            await update.message.reply_text(capabilities_response)
            return

        # Handle greetings and other simple conversational messages
        smalltalk_response = detect_smalltalk(user_input)

        if smalltalk_response:
            await update.message.reply_text(smalltalk_response)
            return

        # Process monitoring queries
        response, updated_context = process_user_message(
            user_input,
            last_context,
            influx_client
        )

        set_context(
            chat_id,
            updated_context
        )

    except Exception as e:
        response = (
            f"Ha ocurrido un error procesando la consulta: {e}"
        )

    finally:
        # Remove the temporary thinking message
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=thinking_msg.message_id
            )
        except Exception:
            pass

    await update.message.reply_text(response)


def main():
    # Create the Telegram application
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    influx_client = MonitoringInfluxClient()
    app.bot_data["influx_client"] = influx_client

    # Register bot commands and text messages
    app.add_handler(
        CommandHandler("start", start_command)
    )
    app.add_handler(
        CommandHandler("restart", restart_command)
    )
    app.add_handler(
        CommandHandler("help", help_command)
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot de Telegram iniciado...")

    try:
        app.run_polling()
    finally:
        # Close the InfluxDB connection when the bot stops
        influx_client.close()


if __name__ == "__main__":
    main()