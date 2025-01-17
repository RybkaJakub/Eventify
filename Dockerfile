FROM python:3.10

WORKDIR ${PWD}

COPY requirements.txt ${PWD}

RUN pip install --no-cache-dir -r requirements.txt

COPY . ${PWD}

EXPOSE 8000

# Příkaz pro spuštění serveru
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
