from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
import configparser

# Obtient la liste des utilisateurs du workspace Slack
def get_slack_users():
    config = configparser.ConfigParser()
    config.read("config.ini")

    client = WebClient(token=config.get("Slack", "slack_token"))

    try:
        response = client.users_list()
        return [True, response["members"]]
    except SlackApiError as e:
        return [False, e.response["error"]]


# Retourne l'id Slack de quelqu'un en fonction de son nom, prénom ou email
def get_slack_id_from_info(first_name, last_name, username, email):
    res = get_slack_users()
    if res[0]:
        users = res[1]
        for user in users:
            # Vérifiez le nom réel
            if "real_name" in user and user["real_name"] == f"{first_name} {last_name}":
                return user["id"]
            # Vérifiez le nom d'utilisateur
            elif "name" in user and user["name"] == username:
                return user["id"]
            # Vérifiez l'email
            elif (
                "profile" in user
                and "email" in user["profile"]
                and user["profile"]["email"] == email
            ):
                return user["id"]
        return None
    else:
        print("⚠️ Erreur lors de l'obtention de la liste des utilisateurs : ", res[1])
        return None


# Envoi un message sur Slack
def send_slack_message(message):
    config = configparser.ConfigParser()
    config.read("config.ini")

    client = WebClient(token=config.get("Slack", "slack_token"))

    try:
        client.chat_postMessage(channel=config.get("Slack", "channel_id"), text=message)
        return [True, message]
    except SlackApiError as e:
        return [False, e.response["error"]]