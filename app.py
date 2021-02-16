import dash

# import requests
# import dash_auth

#### APP

# get authentication pairs
# with open(".auth_app.txt") as f:
# VALID_USERNAME_PASSWORD_PAIRS = dict(x.rstrip().split(":") for x in f)
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,  # ,external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
)
server = app.server
# auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
