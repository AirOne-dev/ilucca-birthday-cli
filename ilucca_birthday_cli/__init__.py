import argparse
import locale
import schedule
import time
from . import birthday_utils

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


# Pour exécuter le script en ligne de commande et choisir
# si on veut afficher le prochain anniversaire ou tous les anniversaires
def cli():
    parser = argparse.ArgumentParser(description='Affiche les prochains anniversaires.', add_help=False, usage='python3 %(prog)s [-h] [--next | --all | --today]')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Affiche ce message d\'aide.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-n', '--next', action='store_true', help='Affiche le prochain anniversaire à venir.')
    group.add_argument('-a', '--all', action='store_true', help='Affiche tous les anniversaires à venir.')
    group.add_argument('-t', '--today', action='store_true', help='Affiche tous les anniversaires du jour.')
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        exit()
    print(birthday_utils.get_birthdays(returnNext=args.next, returnAll=args.all, returnToday=args.today))


# Affiche le prochain anniversaire à venir
def next():
    print(birthday_utils.get_birthdays(returnNext=True))


# Affiche tous les anniversaires à venir
def all():
    print(birthday_utils.get_birthdays(returnAll=True))

# Affiche les anniversaires du jour
def today():
    print(birthday_utils.get_birthdays(returnToday=True))


# Serveur qui check tous les jours à 08:30 si c'est l'anniversaire de quelqu'un
# Si c'est le cas, envoi un message sur Slack
def server():
    print("Serveur démarré")
    schedule.every().day.at("08:30").do(birthday_utils.send_today_birthday_to_slack)
    print("Tâche planifiée pour 08:30 tous les jours")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
            pass
    except KeyboardInterrupt:
        print("Serveur arrêté")


def update_data():
    birthday_utils.update_data()

# Si le script est exécuté directement, on le lance en mode cli
if __name__ == "__main__":
    cli()