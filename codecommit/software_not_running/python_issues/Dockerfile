FROM public.ecr.aws/lts/ubuntu:20.04_stable

WORKDIR /home/app

COPY app.py .

RUN apt update && \
    apt install -y --no-install-recommends python3-pip && \
    pip install numpy==1.18.5

RUN python3 app.py
