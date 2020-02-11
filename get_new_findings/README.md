## Assessment History New Non compliants

* It's necessary configure the following environment vars

```bash
export DOME9_API_KEY=<dome9-api-key>
export DOME9_API_SECRET=<dome9-api-secret>
export SMTP_SERVER=<smtp-server>
export SMTP_PORT=<smtp-port>
export SMTP_USER=<smtp-user>
 export SMTP_USER_PASSWORD=<smtp-password>
```

* Run:

```bash
python get_new_findings.py -d <days> -n "Assessment Name" -a <cloudAccount1> <cloudAccount2> <cloudAccountN> -e <email_to>

# Help
pthon get_new_findings.py -h
```
