FROM public.ecr.aws/lts/ubuntu:20.04_stable

WORKDIR /home/app

COPY requirements.txt .
COPY classify.py .
COPY creditcard.csv .

RUN apt update && \
    apt install -y --no-install-recommends python3-pip && \
    pip install -r requirements.txt

RUN python3 classify.py
