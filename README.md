# ral-lunch

An api for querying what is for lunch at RAL R22. Data is scraped from the PDF menu published on the restaurant's website.

## Requirements
- Python >= 3.10
- A Java runtime environment (since tabula-py requires one)

## Usage

- Clone the git repository: `git clone git@github.com:MattPrit/ral-lunch.git`

- Install the required packages: `cd ral-lunch && pip install .`

- Run the uvicorn server: `uvicorn ral-lunch.main: app`

The API is then accessable on `localhost:8000`:

```
> curl "localhost:8000/menu?day=friday&meal_type=dessert" 
"Pudding Of The Day"
```

## Usage with docker

1. `docker build -t ral-lunch .`

2. `docker run -p 8000:8000 --name ral-lunch <image-id>`

Where <image-id> is the id of the image built in step 1.
