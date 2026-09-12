from influx_client import MonitoringInfluxClient
from assistant_core import process_user_message


def main():
    # Start the command-line monitoring assistant
    print("Asistente de monitorización iniciado.")
    print("Escribe tu consulta o 'salir' para terminar.\n")

    influx_client = MonitoringInfluxClient()

    last_context = {
        "intent": None,
        "host": None,
    }

    try:
        while True:
            user_input = input("> ").strip()

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("Asistente finalizado.")
                break

            response, last_context = process_user_message(
                user_input,
                last_context,
                influx_client
            )

            print(response)
            print()

    finally:
        # Close the InfluxDB connection before exiting
        influx_client.close()


if __name__ == "__main__":
    main()