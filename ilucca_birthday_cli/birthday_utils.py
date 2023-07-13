import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import configparser
import requests

# Retourne le nombre de jours restants avant un anniversaire
def left_days(birthday):
    today = datetime.today()
    birthday_this_year = datetime(today.year, birthday.month, birthday.day)

    if today > birthday_this_year:
        birthday_next_year = datetime(today.year + 1, birthday.month, birthday.day)
        return (birthday_next_year - today).days
    else:
        return (birthday_this_year - today).days


# Retourne la liste des anniversaires à venir ou le prochain anniversaire
def get_birthdays(returnAll=False, returnNext=False, returnToday=False, prettyPrint=True):
    nbParams = returnAll + returnNext + returnToday
    if nbParams > 1:
        print("⚠️ Erreur: get_birthdays: returnAll et returnNext et returnToday ne peuvent pas être True en même temps")
        exit(1)
    if nbParams == 0:
        print("⚠️ Erreur: get_birthdays: returnAll ou returnNext ou returnToday doit être défini")
        exit(1)

    try:
        with open(os.path.join(os.path.dirname(__file__), 'ilucca_data.json')) as json_data_file:
            data = json.load(json_data_file)
    except FileNotFoundError:
        print("⚠️ Erreur: ilucca_data.json introuvable, veuillez exécuter la commande 'poetry run update_data'")
        exit(1)

    # Converti les données JSON en une liste d'anniversaires
    birthdays = [{"name": item["name"], "birthday": item["birthDate"]} for item in data["data"]["items"]]

    today = datetime.today()

    returnedText = "\nLe prochain anniversaire: \n\n" if returnNext else "\nLes prochains anniversaires: \n\n" if returnAll else "\nLes anniversaires du jour: \n\n" if returnToday else ""
    returnedBirthday = []
    
    for day in birthdays:
        birthday = datetime.strptime(day['birthday'], "%Y-%m-%dT%H:%M:%S")
        # Calcule le nombre de jours restants pour chaque anniversaire et l'ajoute à l'objet anniversaire
        day['remaining_days'] = left_days(birthday)
        # Calcule l'âge que la personne fêtera
        day['age'] = relativedelta(datetime.now(), birthday).years

        # Si l'anniversaire n'est pas aujourd'hui, ajouter 1 an à l'âge
        day['age'] += 1 if not (today.month == birthday.month and today.day == birthday.day and today.year == birthday.year) else 0

    # Trie les anniversaires selon le nombre de jours restants
    birthdays = sorted(birthdays, key=lambda k: k['remaining_days'])

    for day in birthdays:
        birthday = datetime.strptime(day['birthday'], "%Y-%m-%dT%H:%M:%S")
        if returnAll:
            returnedText += "🗓️  {0:<2} {1:<15} 🧍 {2:<25} 🎂 {3:<10} ⌛ {4:<3} jours\n".format(birthday.day, birthday.strftime('%B'), day['name'], day['age'], day['remaining_days'])
            returnedBirthday.append(day)
        elif returnNext:
            returnedText += "🗓️  {0:<2} {1:<15} 🧍 {2:<25} 🎂 {3:<10} ⌛ {4:<3} jours\n".format(birthday.day, birthday.strftime('%B'), day['name'], day['age'], day['remaining_days'])
            returnedBirthday.append(day)
            break
        elif returnToday and birthday.day == today.day and birthday.month == today.month:
            day['age'] -= 1
            returnedText += "🎂 {0:>3} ans {1:<2} 🧍 {2:<25}\n".format(day['age'], '', day['name'])
            returnedBirthday.append(day)

    if prettyPrint and len(returnedBirthday) == 0:
        return "\nAucun anniversaire à afficher.\n\n"

    return returnedText if prettyPrint else returnedBirthday


# Envoi un message sur Slack si c'est l'anniversaire de quelqu'un
def send_today_birthday_to_slack():
    current_birthdays = get_birthdays(returnToday=True, prettyPrint=False)
    if len(current_birthdays) > 0:
        for birthday in current_birthdays:
            user_id = get_slack_id_from_name(birthday['first_name'], birthday['last_name'])
            if user_id:
                res = send_slack_message("🎂 Joyeux anniversaire à 🧍 <@{0}> Qui fête ses {1} ans ! 🎂".format(user_id, birthday['age']))
                if res[0]:
                    print("✅ Message envoyé sur Slack : " + res[1])
                else:
                    print("⚠️ Erreur lors de l'envoi sur Slack : ", res[1])
            else:
                print(f"⚠️ Aucun utilisateur trouvé pour {birthday['first_name']} {birthday['last_name']}")
    else:
        print("Aucun anniversaire aujourd'hui.")


# Obtient la liste des utilisateurs du workspace Slack
def get_slack_users():
    config = configparser.ConfigParser()
    config.read('config.ini')

    client = WebClient(token=config.get('Slack', 'slack_token'))

    try:
        response = client.users_list()
        return [True, response['members']]
    except SlackApiError as e:
        return [False, e.response["error"]]


# Retourne l'id Slack de quelqu'un en fonction de son nom et prénom
def get_slack_id_from_name(first_name, last_name):
    res = get_slack_users()
    if res[0]:
        users = res[1]
        for user in users:
            if 'real_name' in user and user['real_name'] == f"{first_name} {last_name}":
                return user['id']
        return None
    else:
        print("⚠️ Erreur lors de l'obtention de la liste des utilisateurs : ", res[1])
        return None


# Envoi un message sur Slack
def send_slack_message(message):
    config = configparser.ConfigParser()
    config.read('config.ini')

    client = WebClient(token=config.get('Slack', 'slack_token'))

    try:
        client.chat_postMessage(channel=config.get('Slack', 'channel_id'), text=message)
        return [True, message]
    except SlackApiError as e:
        return [False, e.response["error"]]


def update_data():
    config = configparser.ConfigParser()
    config.read('config.ini')

    iluccaUrl = config.get('ilucca', 'ilucca_api_url') + '/users/birthday?fields=name,firstname,lastname,picture.href,birthDate&startsOn={0}-01-01&endsOn={1}-01-01'.format(datetime.today().year, datetime.today().year + 1)
    cookies = {'authToken': config.get('ilucca', 'ilucca_auth_token')}

    response = requests.get(iluccaUrl, cookies=cookies)
    if response.status_code == 200:
        with open(os.path.join(os.path.dirname(__file__), 'ilucca_data.json'), 'wb') as json_data_file:
            json_data_file.write(response.content)
        print('ilucca_data.json updated successfully.')
    else:
        print('⚠️ Error updating ilucca_data.json. Status code:', response.status_code)