from requests import Session, Request
from datetime import datetime, timedelta
import json
from os import environ
import argparse
import sys
import smtplib
import re
from email.message import EmailMessage


message = EmailMessage()
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


class validate_email():
    def __call__(self, value):
        regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        if not re.search(regex, value):
            raise argparse.ArgumentTypeError(value+" is not a valid email")
        return value


def check_environment_vars():
    if environ.get('DOME9_API_KEY') is None:
        print("Environment Variable required: DOME9_API_KEY")
        sys.exit(0)

    if environ.get('DOME9_API_SECRET') is None:
        print("Environment Variable required: DOME9_API_SECRET")
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
        '-e', '--email', dest='email', type=validate_email(),
        help='Email to send Report')

    return parser.parse_args()


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
        response = s.send(prepared_request, proxies=environ.get('DOME9_PROXY'))
        if response.status_code != 200:
            raise Exception("Dome9 API Response unexpected: " + response.reason)
    except Exception as e:
        print(str(e))
        sys.exit(0)
    return response.json()


def send_email():

    if args.email is None:
        return

    if environ.get('SMTP_SERVER') is None or environ.get('SMTP_PORT') is None or environ.get('SMTP_USER') is None or environ.get('SMTP_USER_PASSWORD') is None:
        print("Environment Variables required: SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_USER_PASSWORD")
        print("EMAIL haven't been send")
        return

    message['Subject'] = "New Findings"
    message['From'] = environ.get('SMTP_USER')
    message['To'] = args.email

    try:
        server = smtplib.SMTP_SSL(environ.get('SMTP_SERVER'), environ.get('SMTP_PORT'))
        server.ehlo()
        server.login(environ.get('SMTP_USER'), environ.get('SMTP_USER_PASSWORD'))
        server.send_message(message)
    except Exception as e:
        print("Error sending the email")
        print(str(e))
        sys.exit(0)


def has_cloud_accounts(processed_cloud_accounts):
    return False if len(processed_cloud_accounts) == 0 else True


def get_assessment_history():
    return api_request("POST", "AssessmentHistoryV2/view/timeRange", True)


def get_assessment_result(id):
    return api_request("GET", "AssessmentHistoryV2/" + str(id), False)


def get_assessments():
    assessments = dict()
    assessments[args.assessment_name] = dict()
    for cloud_account in args.cloud_accounts:
        assessments[args.assessment_name][cloud_account] = dict()
    has_next = True
    page_number = 1
    processed_cloud_accounts = args.cloud_accounts.copy()
    while has_next:
        history = get_assessment_history()
        payload['pageNumber'] = page_number
        for assessment in history["results"]:
            if args.assessment_name != assessment["request"]["name"] or assessment["request"]["dome9CloudAccountId"] not in processed_cloud_accounts:
                continue
            # print(assessment_name)
            # print(assessment["request"]["dome9CloudAccountId"])
            result = get_assessment_result(assessment["id"])
            assessments[args.assessment_name][assessment["request"]["dome9CloudAccountId"]] = get_rules_from_assessment(result["tests"], result["testEntities"])

            processed_cloud_accounts.remove(assessment["request"]["dome9CloudAccountId"])
            if not has_cloud_accounts(processed_cloud_accounts):
                break

        page_number += 1
        if page_number < history["pageNumber"] or not has_cloud_accounts(processed_cloud_accounts):
            has_next = False

    return assessments


def get_rules_from_assessment(rules, entities):
    rules_result = dict()
    for rule in rules:
        if rule["nonComplyingCount"] != 0:
            rules_result[rule["rule"]["ruleId"]] = dict()
            rules_result[rule["rule"]["ruleId"]]["name"] = rule["rule"]["name"]
            rules_result[rule["rule"]["ruleId"]]["entities"] = get_entities_from_rule(rule, entities)
    return rules_result


def get_entities_from_rule(rule, entities):
    entities_result = dict()
    for entity in rule["entityResults"]:
        if int(entity["testObj"]["entityIndex"]) >= 0:
            entities_result[entity["testObj"]["id"]] = dict()
            entities_result[entity["testObj"]["id"]]["type"] = entity["testObj"]["entityType"]
            entities_result[entity["testObj"]["id"]]["name"] = entities[entity["testObj"]["entityType"]][entity["testObj"]["entityIndex"]]["name"]
    return entities_result


def rule_has_entities(entities):
    return True if len(entities) > 0 else False


def print_entity(entity):
    print("Type: " + str(entity["type"]) + " => Name: " + str(entity["name"]))

args = args()
check_environment_vars()


payload['creationTime'] = dict()
payload['creationTime']["from"] = datetime.strftime(datetime.now() - timedelta(args.days), '%Y-%m-%dT00:00:00Z')
payload['creationTime']["to"] = datetime.strftime(datetime.now() - timedelta(args.days), '%Y-%m-%dT23:59:59Z')
first_day_assessments = get_assessments()
payload['creationTime']["from"] = datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%dT00:00:00Z')
payload['creationTime']["to"] = datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%dT23:59:59Z')
last_day_assessments = get_assessments()

for cloud_account in args.cloud_accounts:
    print("Assessment: " + args.assessment_name + " => Cloud Account: " + cloud_account)
    for rule in last_day_assessments[args.assessment_name][cloud_account]:
        print("Rule Name: " + last_day_assessments[args.assessment_name][cloud_account][rule]["name"])
        if rule_has_entities(last_day_assessments[args.assessment_name][cloud_account][rule]["entities"]):
            if rule in first_day_assessments[args.assessment_name][cloud_account]:
                for entity in last_day_assessments[args.assessment_name][cloud_account][rule]["entities"]:
                    if entity not in first_day_assessments[args.assessment_name][cloud_account][rule]["entities"]:
                        print_entity(last_day_assessments[args.assessment_name][cloud_account][rule]["entities"][entity])
            else:
                for entity in last_day_assessments[args.assessment_name][cloud_account][rule]["entities"]:
                    print_entity(last_day_assessments[args.assessment_name][cloud_account][rule]["entities"][entity])
        else:
            if rule not in first_day_assessments[args.assessment_name][cloud_account]:
                print("This Rule hasn't have entities but it's a new non compliant")
