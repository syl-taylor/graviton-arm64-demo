FROM public.ecr.aws/lts/ubuntu:20.04_stable

WORKDIR /home/app

COPY requirements.txt .
COPY app.py .

RUN apt update && \
    apt install -y --no-install-recommends python3-pip && \
    pip install -r requirements.txt

RUN python3 app.py && \
    ls -lh | grep 'plot.png'
