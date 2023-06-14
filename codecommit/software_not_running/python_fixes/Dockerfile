FROM public.ecr.aws/lts/ubuntu:20.04_stable

WORKDIR /home/app

COPY app.py .

# Upgrade numpy to get pre-built wheel, alternatively build from source (add build tools)
RUN apt update && \
    apt install -y --no-install-recommends python3-pip && \
    pip install numpy==1.19.0

RUN python3 app.py
