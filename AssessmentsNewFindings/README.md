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
| SMTP_SERVER        | SMTP Server To Send the Email                                                                                                                                                                                      |
| SMTP_PORT          | SMTP Server Port                                                                                                                                                                                                   |
| SMTP_USER          | SMTP Server User to authenticate                                                                                                                                                                                   |
| SMTP_USER_PASSWORD | SMTP Server User password                                                                                                                                                                                          |
|                    |                                                                                                                                                                                                                    |

## Deployment

It's necessary have docker installed


* Run:

```bash
python get_new_findings.py -d <days> -n "Assessment Name" -a <cloudAccount1> <cloudAccount2> <cloudAccountN> -e <email_to>

# Help
python get_new_findings.py -h
```
