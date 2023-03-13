FROM python:3.9

RUN mkdir -p /app/
WORKDIR /app/

COPY ../sdk /app/sdk/
COPY ./sankey /app/sankey/
COPY ../requirements.txt /app/
COPY ../app_Sankey.py /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8050

CMD ["python", "app_Sankey.py"]