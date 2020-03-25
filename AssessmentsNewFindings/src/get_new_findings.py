from requests import Session, Request
from datetime import datetime, timedelta
import json
from os import environ
import argparse
import sys
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import copy

result = dict()

base_url = "https://api.dome9.com/v2/"

payload = {
    "sorting": {
        "fieldName": "createdTime",
        "direction": -1
    }
}

headers = {
    'content-type':
        'application/json'
}

dome9_url_assets = "https://secure.dome9.com/v2/protected-asset/generic?"

type_to_url = {
    'kms': 'KMS',
    'rds': 'RDS',
    'vpc': 'VPC',
    'efs': 'EFS',
    'elb': 'ELB',
}

resources_without_url = ["iamPolicy", "region", "subnet", "iam", "routeTable", "ecsTask"]


class validate_email():
    def __call__(self, value):
        regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        if not re.search(regex, value):
            raise argparse.ArgumentTypeError(value+" is not a valid email")
        return value


def convertType_to_url(type, account, assetId):
    if type in resources_without_url:
        return 'N/A'

    if type == 'securityGroup':
        return 'https://secure.dome9.com/v2/security-group/aws/'+assetId

    if type in type_to_url:
        return dome9_url_assets + "cloudAccountId="+account+"&assetType="+type_to_url[type] +"&assetId="+assetId
    return dome9_url_assets + "cloudAccountId="+account+"&assetType="+type[0].upper() + type[1:] +"&assetId="+assetId


def check_environment_vars():
    if environ.get('DOME9_API_KEY') is None:
        print("Environment Variable required: DOME9_API_KEY")
        sys.exit(0)

    if environ.get('DOME9_API_SECRET') is None:
        print("Environment Variable required: DOME9_API_SECRET")
        sys.exit(0)

    if environ.get('SMTP_SERVER') is None:
        print("Environment Variable required: SMTP_SERVER")
        sys.exit(0)

    if environ.get('SMTP_PORT') is None:
        print("Environment Variable required: SMTP_PORT")
        sys.exit(0)

    if environ.get('SMTP_USER') is None:
        print("Environment Variable required: SMTP_USER")
        sys.exit(0)


def args():
    parser = argparse.ArgumentParser(description='Get the New Findings between the last X Days')
    parser.add_argument(
        '-d', '--days', dest="days", type=int, default=7,
        help='The number of days to search for new findings')

    parser.add_argument(
        '-n', '--name', dest='assessment_name', type=str, required=True,
        help='<Required> Assessment Name to search for new findings')

    parser.add_argument(
        '-a', '--accounts', dest='cloud_accounts', type=str, nargs='+', required=True,
        help='<Required> Cloud Accounts ID')

    parser.add_argument(
        '-e', '--email', dest='email', type=validate_email(), nargs='+', required=True,
        help='<Required> Email to send Report')

    return parser.parse_args()


def send_email(html):

    if args.email is None:
        return

    message = MIMEMultipart('alternative')
    message['Subject'] = 'Dome 9: '+ args.assessment_name + ' Assessment - New Findings Since ' + datetime.strftime(datetime.now() - timedelta(args.days), '%Y-%m-%d')
    message['From'] = environ.get('SMTP_USER')
    message['To'] = ", ".join(args.email)
    if sys.version_info[0] < 3:
        message.attach(MIMEText(html.encode('utf-8'), 'html'))
    else:
        message.attach(MIMEText(html, 'html'))

    try:
        if environ.get('SMTP_SSL') is not None and environ.get('SMTP_SSL'):
            server = smtplib.SMTP_SSL(environ.get('SMTP_SERVER'), environ.get('SMTP_PORT'))
        else:
            server = smtplib.SMTP(environ.get('SMTP_SERVER'), environ.get('SMTP_PORT'))
        server.ehlo()
        if environ.get('SMTP_USER_PASSWORD') is not None:
            server.login(environ.get('SMTP_USER'), environ.get('SMTP_USER_PASSWORD'))

        server.sendmail(message['From'], args.email, message.as_string())
        server.quit()
    except Exception as e:
        print("Error sending the email")
        print(str(e))
        sys.exit(0)


def api_request(verb, url, has_data):
    try:
        s = Session()
        r = Request(
            verb,
            base_url+url,
            headers=headers,
            auth=(environ.get('DOME9_API_KEY'), environ.get('DOME9_API_SECRET'))
        )

        if has_data:
            r.data = json.dumps(payload)
        prepared_request = s.prepare_request(r)
        response = s.send(prepared_request, proxies={
            "https": environ.get('DOME9_HTTPS_PROXY')
        })
        if response.status_code != 200:
            raise Exception("Dome9 API Response unexpected: " + response.reason)
    except Exception as e:
        print(str(e))
        sys.exit(0)
    return response.json()


def has_cloud_accounts(processed_cloud_accounts):
    return False if len(processed_cloud_accounts) == 0 else True


def get_assessment_history():
    return api_request("POST", "AssessmentHistoryV2/view/timeRange", True)


def get_cloudAccount_name(id):
    return api_request("GET", "CloudAccounts/" + str(id), False)["name"]


def get_assessment_result(id):
    return api_request("GET", "AssessmentHistoryV2/" + str(id), False)


def get_assessments():
    assessments = dict()
    assessments[args.assessment_name] = dict()
    for cloud_account in args.cloud_accounts:
        assessments[args.assessment_name][cloud_account] = dict()
    has_next = True
    page_number = 1
    processed_cloud_accounts = copy.deepcopy(args.cloud_accounts)
    while has_next:
        history = get_assessment_history()
        payload['pageNumber'] = page_number
        for assessment in history["results"]:
            if args.assessment_name != assessment["request"]["name"] or assessment["request"]["dome9CloudAccountId"] not in processed_cloud_accounts:
                continue
            result = get_assessment_result(assessment["id"])
            assessments[args.assessment_name][assessment["request"]["dome9CloudAccountId"]]["rules"] = get_rules_from_assessment(result["tests"], result["testEntities"])
            assessments[args.assessment_name][assessment["request"]["dome9CloudAccountId"]]["awsCloudAccountID"] = assessment["request"]["externalCloudAccountId"]
            assessments[args.assessment_name][assessment["request"]["dome9CloudAccountId"]]["name"] = get_cloudAccount_name(assessment["request"]["dome9CloudAccountId"])
            processed_cloud_accounts.remove(assessment["request"]["dome9CloudAccountId"])
            if not has_cloud_accounts(processed_cloud_accounts):
                break

        page_number += 1
        if page_number > history["pageSize"] or not has_cloud_accounts(processed_cloud_accounts):
            has_next = False

    return assessments


def get_rules_from_assessment(rules, entities):
    rules_result = dict()
    for rule in rules:
        if rule["nonComplyingCount"] != 0:
            rules_result[rule["rule"]["ruleId"]] = dict()
            rules_result[rule["rule"]["ruleId"]]["name"] = rule["rule"]["name"]
            rules_result[rule["rule"]["ruleId"]]["severity"] = rule["rule"]["severity"]
            rules_result[rule["rule"]["ruleId"]]["remediation"] = rule["rule"]["remediation"]
            rules_result[rule["rule"]["ruleId"]]["entities"] = get_entities_from_rule(rule, entities)
    return rules_result


def get_entities_from_rule(rule, entities):
    entities_result = dict()
    for entity in rule["entityResults"]:
        if int(entity["testObj"]["entityIndex"]) >= 0:
            entities_result[entity["testObj"]["id"]] = dict()
            entities_result[entity["testObj"]["id"]]["type"] = entity["testObj"]["entityType"]
            entities_result[entity["testObj"]["id"]]["name"] = entities[entity["testObj"]["entityType"]][entity["testObj"]["entityIndex"]]["name"]
            entities_result[entity["testObj"]["id"]]["assetId"] = entity["testObj"]["id"]
    return entities_result


def rule_has_entities(entities):
    return True if len(entities) > 0 else False


def add_entity_to_result(account, name, awsCloudAccountID, rule, entity):
    if account not in result:
        result[account] = dict()
        result[account]['awsCloudAccountID'] = awsCloudAccountID
        result[account]['name'] = name
    if rule["severity"] not in result[account]:
        result[account][rule["severity"]] = dict()
    if rule["name"] not in result[account][rule["severity"]]:
        result[account][rule["severity"]][rule["name"]] = dict()
        result[account][rule["severity"]][rule["name"]]["entities"] = []
        result[account][rule["severity"]][rule["name"]]["remediation"] = rule["remediation"]
    if entity is not None:
        result[account][rule["severity"]][rule["name"]]["entities"].append({
            'name': entity['name'],
            'type': entity['type'],
            'url': convertType_to_url(entity['type'], account, entity['assetId'])
        })


def get_assessment_by_date(days):
    payload['creationTime'] = dict()
    payload['creationTime']["from"] = datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%dT00:00:00Z')
    payload['creationTime']["to"] = datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%dT23:59:59Z')
    return get_assessments()


def get_assessment_diff(first_day_assessments, last_day_assessments):
    for cloud_account in args.cloud_accounts:
        if 'rules' in last_day_assessments[args.assessment_name][cloud_account]:
            for rule in last_day_assessments[args.assessment_name][cloud_account]["rules"]:
                if rule_has_entities(last_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"]):
                    if rule in first_day_assessments[args.assessment_name][cloud_account]["rules"]:
                        for entity in last_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"]:
                            if entity not in first_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"]:
                                add_entity_to_result(
                                    cloud_account,
                                    last_day_assessments[args.assessment_name][cloud_account]['name'],
                                    last_day_assessments[args.assessment_name][cloud_account]['awsCloudAccountID'],
                                    last_day_assessments[args.assessment_name][cloud_account]["rules"][rule],
                                    last_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"][entity]
                                )
                    else:
                        for entity in last_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"]:
                            add_entity_to_result(
                                cloud_account,
                                last_day_assessments[args.assessment_name][cloud_account]['name'],
                                last_day_assessments[args.assessment_name][cloud_account]['awsCloudAccountID'],
                                last_day_assessments[args.assessment_name][cloud_account]["rules"][rule],
                                last_day_assessments[args.assessment_name][cloud_account]["rules"][rule]["entities"][entity]
                            )
                else:
                    if rule not in first_day_assessments[args.assessment_name][cloud_account]["rules"]:
                        add_entity_to_result(
                            cloud_account,
                            last_day_assessments[args.assessment_name][cloud_account]['name'],
                            last_day_assessments[args.assessment_name][cloud_account]['awsCloudAccountID'],
                            last_day_assessments[args.assessment_name][cloud_account]["rules"][rule],
                            None
                        )


def main():
    check_environment_vars()
    first_day_assessments = get_assessment_by_date(args.days)
    last_day_assessments = get_assessment_by_date(0)
    get_assessment_diff(first_day_assessments, last_day_assessments)
    template_loader = FileSystemLoader('templates')
    env = Environment(loader=template_loader)
    template = env.get_template('table.html')
    html = ""
    for cloud_account in args.cloud_accounts:
        html += template.render(result=result, cloud_account=cloud_account, name=last_day_assessments[args.assessment_name][cloud_account]['name'])
    send_email(html)


args = args()
if __name__== "__main__":
    main()
