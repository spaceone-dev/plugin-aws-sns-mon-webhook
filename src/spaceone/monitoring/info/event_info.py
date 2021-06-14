import functools
from spaceone.api.monitoring.plugin import event_pb2
from spaceone.monitoring.model.event_response_model import EventModel
from spaceone.core.pygrpc.message_type import *

__all__ = ['EventInfo', 'EventsInfo']


def EventInfo(event_Info_data: EventModel):
    info = {
        'event_key': event_Info_data['event_key'],
        'event_type': event_Info_data['event_type'],
        'description': event_Info_data.get('description'),
        'title': event_Info_data['title'],
        'severity': event_Info_data['severity'],
        'resource': change_struct_type(event_Info_data['resource']),
        'rule': event_Info_data.get('rule'),
        'tags': change_struct_type(event_Info_data.get('tags'))
    }
    return event_pb2.EventInfo(**info)


def EventsInfo(event_Info_vos, **kwargs):
    return event_pb2.EventsInfo(results=list(map(functools.partial(EventInfo, **kwargs), event_Info_vos)))