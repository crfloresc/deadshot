FROM python:3.10.13-alpine3.19
ENV PYTHONBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app/ /app/app/
COPY ./labels/ /app/labels/
COPY ./out/ /app/out/
COPY ./setup.py /app/
ENV PYTHONPATH="/app:${PYTHONPATH}"

RUN python setup.py build \
    && python setup.py develop

ENTRYPOINT [ "deadshot" ]
CMD [ "-c", "config.json" ]