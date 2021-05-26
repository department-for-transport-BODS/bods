from typing import Callable, Dict, List, Type

from transit_odp.bods.domain import commands, events
from transit_odp.bods.service_layer.usecases import consumer, worker

EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.AVLFeedStatusChanged: [
        worker.SendAVLFeedPublisherDownNotification,
        worker.SendAVLFeedSubscriberNotification,
    ],
}

COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    commands.MonitorAVLFeeds: worker.MonitorAVLFeeds,
    commands.SendFeedback: consumer.SendFeedback,
}
