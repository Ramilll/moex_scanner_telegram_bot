install poetry

mac: curl -sSL https://install.python-poetry.org | python3 -
windows: (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

install packages with poetry: poetry install --no-root
create a virtenv with poetry: poetry shell