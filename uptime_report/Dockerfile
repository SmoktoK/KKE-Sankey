FROM python:3.9

RUN mkdir -p /app/
WORKDIR /app/

COPY ../sdk /app/sdk/
COPY ./uptime_report /app/uptime_report/
COPY ../requirements.txt /app/
COPY ../app_Uptime.py /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

EXPOSE 8050

CMD ["python", "app_Uptime.py"]