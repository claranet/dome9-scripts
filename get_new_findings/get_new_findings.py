import requests
from datetime import datetime, timedelta
import json
import os
import argparse


apiKey = os.getenv('DOME9_API_KEY')
apiSecret = os.getenv('DOME9_API_SECRET')
proxyDict = None
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
    return parser.parse_args()


def has_cloud_accounts(processed_cloud_accounts):
    return False if len(processed_cloud_accounts) == 0 else True


def get_assessment_history():
    response = requests.post(
        "https://api.dome9.com/v2/AssessmentHistoryV2/view/timeRange",
        data=json.dumps(payload),
        headers=headers,
        auth=(apiKey, apiSecret),
        proxies=proxyDict)
    if response.status_code != 200:
        # TODO Exception
        print("TODO")
    return response.json()


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


def get_assessment_result(id):
    response = requests.get(
        "https://api.dome9.com/v2/AssessmentHistoryV2/" + str(id),
        headers=headers,
        auth=(apiKey, apiSecret),
        proxies=proxyDict)
    if response.status_code != 200:
        # TODO Exception
        print("TODO")
    return response.json()


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
