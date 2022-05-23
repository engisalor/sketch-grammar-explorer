import getpass
import pathlib
import yaml

import sgex


def credentials():
    """Manage Sketch Engine API credentials.

    Options:

    - choose whether to use a hidden config file
    - add credentials for multiple servers
    - delete credentials in keyring
    - store keys in plaintext or with keyring

    Directly modify a config file for other tasks or as an alternative to this method."""

    path = pathlib.Path("")
    server = "https://api.sketchengine.eu/bonito/run.cgi"
    credentials = {}

    hidden_config = input(
        "\nWelcome to Sketch Grammar Explorer\nUse hidden config file? (y/N) "
    )
    if hidden_config.lower() == "y":
        creds_file = path / ".config.yml"
    else:
        creds_file = path / "config.yml"

    try:
        with open(creds_file, "r") as stream:
            credentials = yaml.safe_load(stream)
        print(f'Loading "{creds_file}"')
    except:
        print(f'Making new "{creds_file}"')

    def _set_server():
        new_server = input(
            f"Server:\n- leave empty for default (https://api.sketchengine.eu/bonito/run.cgi)\n- trailing slashes are removed\n"
        )
        if not new_server:
            new_server = server
        new_server = new_server.strip("/")

        return new_server

    def _save_creds(server, user, key):
        yn = "y"
        if pathlib.Path(creds_file).exists():
            yn = input("\nOverwrite {}? (y/N) ".format(creds_file))
        if yn.lower() == "y":
            with open(creds_file, "w", encoding="utf-8") as f:
                credentials[server] = {"username": user, "api_key": key}
                yaml.dump(credentials, f, allow_unicode=True, sort_keys=False, indent=2)
            print("Done")
        else:
            print("Operation cancelled")

    def _add_keyring():
        import keyring

        print("\nAdd credentials to keyring:")

        new_server = _set_server()
        user = input("User: ")
        key = getpass.getpass()
        keyring.set_password(new_server, user, key)
        _save_creds(new_server, user, "")
        print("Server: {}".format(new_server))
        print("User: {}".format(new_server))

    def _del_keyring():
        import keyring

        print("Remove credentials from keyring:")
        new_server = _set_server()
        user = input("User: ")
        keyring.delete_password(new_server, user)
        check = keyring.get_password(new_server, user)
        if not check:
            print("Credentials removed")
        else:
            print("Error removing credentials. Try deleting from your keyring manually")

    def _plaintext():
        print("\nStore username AND key to {}:".format(creds_file))
        new_server = _set_server()
        user = input("User: ")
        key = getpass.getpass()
        _save_creds(new_server, user, key)

    # Execute
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


def examples(dir="calls", format=".yml"):
    """Generates example input files to `dir` with format `.yml` or `.json`)."""

    path = pathlib.Path(dir)
    file = path / pathlib.Path("examples").with_suffix(format)
    yn = input(f'Save to "{file}"? (y/N) ')

    if yn == "y":
        path.mkdir(parents=True, exist_ok=True)
        sgex.Parse(sgex.call_examples, dest=file)
    else:
        pass