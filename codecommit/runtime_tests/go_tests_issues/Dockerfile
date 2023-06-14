FROM public.ecr.aws/lts/ubuntu:20.04_stable

WORKDIR /home/app

RUN apt update && apt install -y ca-certificates openssl
ARG cert_location=/usr/local/share/ca-certificates
RUN openssl s_client -showcerts -connect github.com:443 </dev/null 2>/dev/null|openssl x509 -outform PEM > ${cert_location}/github.crt && \
    openssl s_client -showcerts -connect proxy.golang.org:443 </dev/null 2>/dev/null|openssl x509 -outform PEM >  ${cert_location}/proxy.golang.crt && \
    update-ca-certificates

RUN apt update && \
    apt install -y --no-install-recommends wget git && \
    wget --no-check-certificate https://go.dev/dl/go1.20.2.linux-amd64.tar.gz && \
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.20.2.linux-amd64.tar.gz && \
    export PATH=$PATH:/usr/local/go/bin && \
    git clone https://github.com/segmentio/parquet-go.git && \
    cd parquet-go && \
    git checkout e1109e2  && \
    # Runtime tests
    go test -tags amd64 -v ./
