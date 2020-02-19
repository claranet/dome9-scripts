FROM python:3

WORKDIR app
ADD src/ .
RUN pip install  -r requirements.txt

ENTRYPOINT [ "python", "get_new_findings.py"]
