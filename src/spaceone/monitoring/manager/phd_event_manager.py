import logging
import requests
import json
from datetime import datetime

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.event_response_model import EventModel
from spaceone.monitoring.error.event import *

_LOGGER = logging.getLogger(__name__)


class PersonalHealthDashboardManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, options, raw_data):
        try:
            if raw_data.get('Type') == 'SubscriptionConfirmation':
                self.request_subscription_confirm(raw_data.get('SubscribeURL'))
                return []
            else:
                """ --- RAW_DATA Sample ---
                "TopicArn": "arn:xxxxx",
                "Subject": "ALARM: ....",
                "SigningCertURL": "https://sns..../...pem",
                "MessageId": "838a70d8-d3c7-5d0c-a03a-29789bc46b66",
                "Message": "{RAW_JSON_MESSAGE}",
                "Timestamp": "2021-08-25T13:29:39.389Z",
                "SignatureVersion": "1",
                "Type": "Notification",
                "Signature": "ht4kn+........==",
                "UnsubscribeURL": "https://sns......"
                """
                return self._generate_events(self._get_json_message(raw_data.get('Message', {})), raw_data)

        except Exception as e:
            raise ERROR_PARSE_EVENT(field=e)

    def _generate_events(self, message, raw_data):
        events = []

        """ MESSAGE Sample1
            {
              "version": "0",
              "id": "7bf73129-1428-4cd3-a780-95db273d1602",
              "detail-type": "AWS Health Event",
              "source": "aws.health",
              "account": "123456789012",
              "time": "2016-06-05T06:27:57Z",
              "region": "ap-southeast-2",
              "resources": [],
              "detail": {
                "eventArn": "arn:aws:health:ap-southeast-2::event/AWS_ELASTICLOADBALANCING_API_ISSUE_90353408594353980",
                "service": "ELASTICLOADBALANCING",
                "eventTypeCode": "AWS_ELASTICLOADBALANCING_API_ISSUE",
                "eventTypeCategory": "issue",
                "startTime": "Sat, 04 Jun 2016 05:01:10 GMT",
                "endTime": "Sat, 04 Jun 2016 05:30:57 GMT",
                "eventDescription": [{
                  "language": "en_US",
                  "latestDescription": "A description of the event will be provided here"
                }]
              }
            }
        """

        """ MESSAGE Sample2
            {
              "version": "0",
              "id": "7bf73129-1428-4cd3-a780-95db273d1602",
              "detail-type": "AWS Health Event",
              "source": "aws.health",
              "account": "123456789012",
              "time": "2016-06-05T06:27:57Z",
              "region": "us-west-2",
              "resources": ["i-abcd1111"],
              "detail": {
                "eventArn": "arn:aws:health:us-west-2::event/AWS_EC2_INSTANCE_STORE_DRIVE_PERFORMANCE_DEGRADED_90353408594353980",
                "service": "EC2",
                "eventTypeCode": "AWS_EC2_INSTANCE_STORE_DRIVE_PERFORMANCE_DEGRADED",
                "eventTypeCategory": "issue",
                "startTime": "Sat, 05 Jun 2016 15:10:09 GMT",
                "eventDescription": [{
                  "language": "en_US",
                  "latestDescription": "A description of the event will be provided here"
                }],
                "affectedEntities": [{
                  "entityValue": "i-abcd1111",
                  "tags": {
                    "stage": "prod",
                    "app": "my-app"
                  }
                }]
              }
            }
        """

        """ Message Sample3
            {
              "version": "0",
              "id": "7bf73129-1428-4cd3-a780-95db273d1602",
              "detail-type": "AWS Health Abuse Event",
              "source": "aws.health",
              "account": "123456789012",
              "time": "2018-08-01T06:27:57Z",
              "region": "global",
              "resources": ["arn:aws:ec2:us-east-1:123456789012:instance/i-abcd1111", "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd2222"],
              "detail": {
                "eventArn": "arn:aws:health:global::event/AWS_ABUSE_DOS_REPORT_92387492375_4498_2018_08_01_02_33_00",
                "service": "ABUSE",
                "eventTypeCode": "AWS_ABUSE_DOS_REPORT",
                "eventTypeCategory": "issue",
                "startTime": "Wed, 01 Aug 2018 06:27:57 GMT",
                "eventDescription": [{
                  "language": "en_US",
                  "latestDescription": "A description of the event will be provided here"
                }],
                "affectedEntities": [{
                  "entityValue": "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd1111"
                }, {
                  "entityValue": "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd2222"
                }]
              }
            }
        """

        """ Message Sample4
            {
              "version": "0",
              "id": "7bf73129-1428-4cd3-a780-95db273d1602",
              "detail-type": "AWS Health Abuse Event",
              "source": "aws.health",
              "account": "123456789012",
              "time": "2018-08-01T06:27:57Z",
              "region": "global",
              "resources": ["arn:aws:ec2:us-east-1:123456789012:instance/i-abcd1111", "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd2222"],
              "detail": {
                "eventArn": "arn:aws:health:global::event/AWS_ABUSE_DOS_REPORT_92387492375_4498_2018_08_01_02_33_00",
                "service": "ABUSE",
                "eventTypeCode": "AWS_ABUSE_DOS_REPORT",
                "eventTypeCategory": "issue",
                "startTime": "Wed, 01 Aug 2018 06:27:57 GMT",
                "eventDescription": [{
                  "language": "en_US",
                  "latestDescription": "A description of the event will be provided here"
                }],
                "affectedEntities": [{
                  "entityValue": "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd1111"
                }, {
                  "entityValue": "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd2222"
                }]
              }
            }
        """
        # event_id = message.get('id', '')
        resource_type = message.get('source', 'aws.health')
        account_id = message.get('account', '')
        # region_code = message.get('region', '')
        detail_event = message.get('detail', {})

        event_arn = detail_event.get('eventArn', '')
        # service = detail_event.get('service', '')
        event_type_code = detail_event.get('eventTypeCode', '')
        event_type_category = detail_event.get('eventTypeCategory', '')
        occurred_at = self._get_occurred_at(detail_event)
        event_description = self._generate_description(detail_event, account_id)
        # affected_entities = detail_event.get('affectedEntities', '')
        # affected_resources = [resource.get('entityValue', '') for resource in affected_entities]
        event_dict = self._generate_event_dict(event_arn, event_type_category, resource_type, event_description,
                                               event_type_code,
                                               occurred_at, message)
        events.append(self._evaluate_parsing_data(event_dict))

        return events

    def _generate_event_dict(self, event_arn, event_type_category, resource_type, event_description, event_type_code,
                             occurred_at, message):
        return {
            'event_key': event_arn,
            'event_type': self._get_event_type(),
            'severity': self._get_severity(event_type_category),
            'resource': self._get_resource_for_event(event_arn, resource_type),
            'description': event_description,
            'title': self._change_string_format(event_type_code),
            'rule': event_type_category,
            'occurred_at': occurred_at,
            'additional_info': self._get_additional_info(message)
        }

    @staticmethod
    def _change_string_format(event_type_code):
        title = event_type_code.replace('_', ' ').title()
        return title

    @staticmethod
    def _generate_description(detail_event, account_id):
        description = ''
        for index, text in enumerate(detail_event.get('eventDescription', []), 1):
            description += text.get('latestDescription', '')
            if index >= 2:
                description += f" {text.get('latestDescription', '')}"
        description += f'(Account:{account_id})'
        return description

    @staticmethod
    def request_subscription_confirm(confirm_url):
        r = requests.get(confirm_url)
        _LOGGER.debug(f'[Confirm_URL: SubscribeURL] {confirm_url}')
        _LOGGER.debug(f'[AWS SNS: Status]: {r.status_code}, {r.content}')

    @staticmethod
    def _get_occurred_at(detail_event):
        if t := detail_event.get('startTime'):
            return datetime.strptime(t, '%a, %d %b %Y %H:%M:%S %Z')
        else:
            return datetime.now()

    @staticmethod
    def _get_additional_info(message):
        additional_info = {}
        additional_info_key = ['id', 'account', 'region', 'service', 'eventTypeCode'] #TODO: " , 'affectedEntities' "

        for _key in message:
            if _key in additional_info_key and message.get(_key):
                additional_info.update({_key: message.get(_key)})
            if _key == "detail":
                detail_event = message.get(_key)
                for detail_key in detail_event:
                    if detail_key in additional_info_key:
                        additional_info.update({detail_key: detail_event.get(detail_key)})

        return additional_info

    @staticmethod
    def _get_severity(event_type_category):
        """
        Severity:
            - issue, scheduledChange -> ERROR
            - accountNotification -> INFO
        """

        if event_type_category in ['issue', 'scheduledChange']:
            severity_flag = 'ERROR'
        else:
            severity_flag = 'INFO'

        return severity_flag

    @staticmethod
    def _get_resource_for_event(event_arn, resource_type):
        return {
            'resouce_id': event_arn,
            'resource_type': resource_type
        }

    @staticmethod
    def _get_event_type():
        return 'ALERT'

    @staticmethod
    def _get_json_message(json_raw_data):
        return json.loads(json_raw_data)

    @staticmethod
    def _evaluate_parsing_data(event_data):
        event_result_model = EventModel(event_data, strict=False)
        event_result_model.validate()
        return event_result_model.to_native()
