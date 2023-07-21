from dateutil.relativedelta import relativedelta
from datetime import datetime
from . import slack_utils
from . import global_utils
import requests
import json
import os


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
def get_birthdays(
    returnAll=False, returnNext=False, returnToday=False, prettyPrint=True
):
    nbParams = returnAll + returnNext + returnToday
    if nbParams > 1:
        print(
            "⚠️ Erreur: get_birthdays: returnAll et returnNext et returnToday ne peuvent pas être True en même temps"
        )
        exit(1)
    if nbParams == 0:
        print(
            "⚠️ Erreur: get_birthdays: returnAll ou returnNext ou returnToday doit être défini"
        )
        exit(1)

    try:
        with open(
            os.path.join(os.path.dirname(__file__), "ilucca_data.json")
        ) as json_data_file:
            data = json.load(json_data_file)
    except FileNotFoundError:
        print(
            "⚠️ Erreur: ilucca_data.json introuvable, veuillez exécuter la commande 'poetry run update_data'"
        )
        exit(1)

    # Converti les données JSON en une liste d'anniversaires
    birthdays = [
        {
            "name": item["name"],
            "birthday": item["birthDate"],
            "firstName": item["firstName"],
            "lastName": item["lastName"],
            "mail": item["mail"],
        }
        for item in data["data"]["items"]
    ]

    today = datetime.today()

    returnedText = (
        "\nLe prochain anniversaire: \n\n"
        if returnNext
        else "\nLes prochains anniversaires: \n\n"
        if returnAll
        else "\nLes anniversaires du jour: \n\n"
        if returnToday
        else ""
    )
    returnedBirthday = []

    for day in birthdays:
        birthday = datetime.strptime(day["birthday"], "%Y-%m-%dT%H:%M:%S")
        # Calcule le nombre de jours restants pour chaque anniversaire et l'ajoute à l'objet anniversaire
        day["remaining_days"] = left_days(birthday)
        # Calcule l'âge que la personne fêtera
        day["age"] = relativedelta(datetime.now(), birthday).years

        # Si l'anniversaire n'est pas aujourd'hui, ajouter 1 an à l'âge
        day["age"] += (
            1
            if not (
                today.month == birthday.month
                and today.day == birthday.day
                and today.year == birthday.year
            )
            else 0
        )

    # Trie les anniversaires selon le nombre de jours restants
    birthdays = sorted(birthdays, key=lambda k: k["remaining_days"])

    for day in birthdays:
        birthday = datetime.strptime(day["birthday"], "%Y-%m-%dT%H:%M:%S")
        if returnAll:
            returnedText += (
                "🗓️  {0:<2} {1:<15} 🧍 {2:<25} 🎂 {3:<10} ⌛ {4:<3} jours\n".format(
                    birthday.day,
                    birthday.strftime("%B"),
                    day["name"],
                    day["age"],
                    day["remaining_days"],
                )
            )
            returnedBirthday.append(day)
        elif returnNext:
            returnedText += (
                "🗓️  {0:<2} {1:<15} 🧍 {2:<25} 🎂 {3:<10} ⌛ {4:<3} jours\n".format(
                    birthday.day,
                    birthday.strftime("%B"),
                    day["name"],
                    day["age"],
                    day["remaining_days"],
                )
            )
            returnedBirthday.append(day)
            break
        elif (
            returnToday and birthday.day == today.day and birthday.month == today.month
        ):
            day["age"] -= 1
            returnedText += "🎂 {0:>3} ans {1:<2} 🧍 {2:<25}\n".format(
                day["age"], "", day["name"]
            )
            returnedBirthday.append(day)

    if prettyPrint and len(returnedBirthday) == 0:
        return "\nAucun anniversaire à afficher.\n\n"

    return returnedText if prettyPrint else returnedBirthday


# Envoi un message sur Slack si c'est l'anniversaire de quelqu'un
def send_today_birthday_to_slack():
    current_birthdays = get_birthdays(returnToday=True, prettyPrint=False)
    if len(current_birthdays) > 0:
        for birthday in current_birthdays:
            user_id = slack_utils.get_slack_id_from_info(
                birthday["firstName"],
                birthday["lastName"],
                birthday["name"],
                birthday["mail"],
            )
            res = slack_utils.send_slack_message(
                "🎂 Joyeux anniversaire à {0} qui fête ses {1} ans ! 🎂".format(
                    "<@{0}>".format(user_id) if user_id else birthday["name"],
                    birthday["age"],
                )
            )
            if res[0]:
                print("✅ Message envoyé sur Slack : " + res[1])
            else:
                print("⚠️ Erreur lors de l'envoi sur Slack : ", res[1])
    else:
        print("Aucun anniversaire aujourd'hui.")


def update_data():
    config = global_utils.get_config()

    iluccaUrl = config.get(
        "Ilucca", "ilucca_api_url"
    ) + "/users/birthday?fields=name,firstname,mail,lastname,picture.href,birthDate&startsOn={0}-01-01&endsOn={1}-01-01".format(
        datetime.today().year, datetime.today().year + 1
    )
    cookies = {"authToken": config.get("Ilucca", "ilucca_auth_token")}

    response = requests.get(iluccaUrl, cookies=cookies)
    if response.status_code == 200:
        with open(
            os.path.join(os.path.dirname(__file__), "ilucca_data.json"), "wb"
        ) as json_data_file:
            json_data_file.write(response.content)
        print("ilucca_data.json updated successfully.")
    else:
        print("⚠️ Error updating ilucca_data.json. Status code:", response.status_code)
