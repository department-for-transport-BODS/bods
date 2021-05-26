import inspect

from transit_odp.bods.adapters.gateways.cavl import CAVLService
from transit_odp.bods.domain.services import AVLFeedWatcher
from transit_odp.bods.interfaces.gateways import ICAVLService
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork
from transit_odp.bods.service_layer import handlers
from transit_odp.bods.service_layer.messagebus import MessageBus
from transit_odp.bods.service_layer.unit_of_work import UnitOfWork


def bootstrap(
    uow: IUnitOfWork = UnitOfWork(),
    cavl_service: ICAVLService = CAVLService(),
    notifications: INotifications = None,
) -> MessageBus:

    if notifications is None:
        notifications = get_notifications()

    # TODO - use dry-python DI framework
    avl_feed_watcher = AVLFeedWatcher(cavl_service=cavl_service)
    dependencies = {
        "uow": uow,
        "notifications": notifications,
        "avl_feed_watcher": avl_feed_watcher,
    }
    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies) for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    # return lambda message: handler(message, **deps)
    return lambda message: handler(**deps)(message)
