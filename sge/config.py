import keyring
import getpass
import pathlib
import yaml


def config(hidden_config=False):
    """Manage Sketch Engine API credentials.

    `hidden_config=True` uses a config file untracked by git (".config.yml").
    """

    path = pathlib.Path("sge/data")

    if hidden_config:
        creds_file = path / ".config.yml"
    else:
        creds_file = path / "config.yml"

    app = "Sketch Grammar Explorer"

    def _save_creds(user, key):
        yn = "y"
        if pathlib.Path(creds_file).exists():
            yn = input("\nOverwrite {}? (y/N) ".format(creds_file))
        if yn.lower() == "y":
            with open(creds_file, "w", encoding="utf-8") as f:
                dt = {"username": user, "api_key": key}
                yaml.dump(dt, f, allow_unicode=True, sort_keys=False, indent=2)
            print("Done")
        else:
            print("Operation cancelled")

    def _add_keyring():
        print("\nAdd credentials to keyring:")
        user = input("User: ")
        key = getpass.getpass()
        keyring.set_password("Sketch Grammar Explorer", user, key)
        _save_creds(user, "")
        print("Service: {}".format(app))
        print("User: {}".format(app))

    def _del_keyring():
        print("Remove credentials from keyring:")
        user = input("User: ")
        keyring.delete_password(app, user)
        check = keyring.get_password(app, user)
        if not check:
            print("Credentials removed")
        else:
            print("Error removing credentials. Try deleting from your keyring manually")

    def _plaintext():
        print("\nStore username AND key to {}:".format(creds_file))
        user = input("User: ")
        key = getpass.getpass()
        _save_creds(user, key)

    # Execute
    print("Welcome to", app)

    response = input(
        "Select an option below:\n1 - store API key w/ keyring\n2 - delete credentials w/ keyring\n3 - store username AND key in plaintext\n"
    )

    if response == "1":
        _add_keyring()
    elif response == "2":
        _del_keyring()
    elif response == "3":
        _plaintext()
    else:
        print("Selection not available: try again")
