# Assessments New Findings

Python Script to compare the findings from an assessment in two different dates and send an email with new findings

## Getting Started

### Arguments

| Argument | Example                                                                          | Description                                  |
|----------|----------------------------------------------------------------------------------|----------------------------------------------|
| -d       | -d 5                                                                             | Number of days to compare the assessment     |
| -n       | -n "Best Pratices"                                                               | Assessment Name                              |
| -a       | -a <cloud_account_1_dome9ID> <cloud_account_2_dome9ID> <cloud_account_N_dome9ID> | Cloud Accounts ID (Dome9 ID)                 |
| -e       | -e <email_1@domain.com> <email_2@domain.com>  <email_N@domain.com>               | Email addresses to receive the script output |

### Environment Vars

| Variable           | Description                                                                                                                                                                                                        |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DOME9_API_KEY      | DOME 9 API KEY - Please visit to create a new API Key - https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=sk144514&partition=General&product=CloudGuard    |
| DOME9_API_SECRET   | DOME 9 API SECRET - Please visit to create a new API Key - https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=sk144514&partition=General&product=CloudGuard |
| DOME9_HTTPS_PROXY  | Example: http://<ip>:<port>                                                                                                                                                                                  |
| SMTP_SERVER        | SMTP Server To Send the Email                                                                                                                                                                                      |
| SMTP_PORT          | SMTP Server Port                                                                                                                                                                                                   |
| SMTP_USER          | SMTP Server User to authenticate and send the email                                                                                                                                                                                  |
| SMTP_USER_PASSWORD | SMTP Server User password                                                                                                                                                                                          |
| SMTP_SSL           | Configure this var with value true if want use SMTP over SSL                                                                                                                                                                                                                   |

### Run

It's necessary have docker installed

* Use Environment Variables file

```bash
# Create a new environment file with name .env (this file should be copied from .env.example>
cp .env.example .env
# Edit the file and fill with your credentials
vi .env
# Run the script
docker run --rm \
   --env-file ./.env \
   outscope/dome9-scripts-assessment-new-findings -d <days> -n '<assessment_name>' -a <cloud_account_dome9_id> -e <email1> <email2>
```

* Use OS Environment Variables

**NOTE:** Configure the environment variables in your Operation System before run the command

```bash
# Configure 
docker run --rm \
   -e DOME9_API_KEY \
   -e DOME9_API_SECRET \
   -e DOME9_HTTPS_PROXY \
   -e SMTP_SERVER \
   -e SMTP_PORT \
   -e SMTP_USER \
   -e SMTP_USER_PASSWORD \
   outscope/dome9-scripts-assessment-new-findings -d <days> -n '<assessment_name>' -a <cloud_account_dome9_id> -e <email1> <email2>
```

* Pass environment Variables in command line

```bash
docker run --rm \
   -e DOME9_API_KEY=<dome9_api_key> \
   -e DOME9_API_SECRET=<dome9_api_secret> \
   -e DOME9_HTTPS_PROXY=<dome9_https_proxy> \
   -e SMTP_SERVER=<smtp_server> \
   -e SMTP_PORT=<smpt_port> \
   -e SMTP_USER=<smtp_user> \
   -e SMTP_USER_PASSWORD=<smtp_user_password> \
   outscope/dome9-scripts-assessment-new-findings -d <days> -n '<assessment_name>' -a <cloud_account_dome9_id> -e <email1> <email2>
```

