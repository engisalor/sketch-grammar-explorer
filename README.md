# Sketch Grammar Explorer

## Usage

### Filtering Table Data

* numbers: 
  * e.g. "79" (quotes required)
  * results will include 79 & 23.79
* greater, lesser & equals signs:
  * e.g. >=64, !=author & <102
  * quotes usually optional
* text
  * e.g. atmospheric sciences
  * quotes usually optional

## Recreating the Data Set

None of the data are provided in this repository, so follow these steps for initial setup.

### Python prep

Create a virtual environment and install requirements.txt.

### App setup

#### API access

Define your Sketch Engine username and api key in a file named `auth_api.txt` with the following format:

``` bash
username:YOUR USERNAME
api_key:YOUR API KEY
```

#### Password protection

To use the app locally, comment out these lines in `app.py`:

``` python
import dash_auth

with open('auth_app.txt') as f:
    VALID_USERNAME_PASSWORD_PAIRS = dict(x.rstrip().split(":") for x in f)

auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
```

#### Add sketch grammar

Supply a file named `grammar.txt` that contains the desired sketch grammar. These are available on Sketch Engine in the corpus details page.

If using a sketch grammar other than EcoLexicon's, additional changes are necessary (see Customization).

#### Get corpus info

Run `corp_info.py` to retrieve the corpus details.

#### Get data

Run `freqs_api.py` to collect frequency data for each CQL expression.

#### Process data

Run `freqs_prep.py` to process the data, generate statistics, and save it in several .csv files.

## Using other corpora

Below are general instructions for using other corpora.

Refer to Sketch Engine and Dash documentation for details:

* <https://www.sketchengine.eu/documentation/api-documentation/>
* <https://dash.plotly.com/>
