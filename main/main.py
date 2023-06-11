import sys
import socket
from utilities.log import Logger

import multiprocessing

from motion_controller.motion_controller import MotionController
from abort_controller.abort_controller import AbortController
from gamepad_controller.gamepad_controller import GamepadController
from send_controller.send_controller import SendController
from recv_controller.recv_controller import RecvController
from GUI_controller.GUI_controller import GUIController

log = Logger().setup_logger()

sever_ip = '0.0.0.0'
sever_port = 8485


# Multiprocessing
def process_abort_controller(communication_queues):
    abort = AbortController(communication_queues)
    abort.do_process_events_from_queue()

def process_motion_controller(communication_queues):
    motion = MotionController(communication_queues)
    motion.do_process_events_from_queues()

def process_gamepad_controller(communication_queues):
    gamepad_controller = GamepadController(communication_queues)
    gamepad_controller.do_process_events_from_queues()

def process_send_controller(communication_queues):
    send_controller = SendController(communication_queues)
    send_controller.send_video()

def process_recv_controller(communication_queues):
    # recv_controller = RecvController(communication_queues)
    # recv_controller.run(communication_queues)
    RecvController(communication_queues).run(communication_queues)

def process_GUI_controller(communication_queues):
    GUIController(communication_queues).GUI_comm(communication_queues)

# Queues
def create_controllers_queues():
    communication_queues = {'abort_controller': multiprocessing.Queue(1),
                            'motion_controller': multiprocessing.Queue(1),
                            'socket_queue': multiprocessing.Queue(1)}

    log.info('Created the communication queues: ' + ', '.join(communication_queues.keys()))

    return communication_queues

def close_controllers_queues(communication_queues):
    log.info('Closing controller queues')

    for queue in communication_queues.items():
        queue.close()
        queue.join_thread()

def main():

    communication_queues = create_controllers_queues()

    send_controller = multiprocessing.Process(target=process_send_controller, 
                                              args=(communication_queues,))
    send_controller.daemon = True

    recv_controller = multiprocessing.Process(target=process_recv_controller, 
                                              args=(communication_queues,))
    recv_controller.daemon = True

    # Controls the 0E port from PCA9685 to cut the power to the servos conveniently if needed.
    abort_controller = multiprocessing.Process(target=process_abort_controller, 
                                               args=(communication_queues,))
    abort_controller.daemon = True  # The daemon dies if the parent process dies

    motion_controller = multiprocessing.Process(target=process_motion_controller, 
                                                args=(communication_queues,))
    motion_controller.daemon = True

    GUI_controller = multiprocessing.Process(target=process_GUI_controller, 
                                                args=(communication_queues,))
    GUI_controller.daemon = True

    # gamepad_controller = multiprocessing.Process(target=process_gamepad_controller, args=(communication_queues,))
    # gamepad_controller.daemon = True

    # Start the processes
    send_controller.start()
    recv_controller.start()
    abort_controller.start()
    motion_controller.start()
    GUI_controller.start()
    # gamepad_controller.start()

    # Make sure all controllers are working
    if not abort_controller.is_alive():
        log.error("SpotMicro can't work without abort_controller")
        sys.exit(1)
    if not motion_controller.is_alive():
        log.error("SpotMicro can't work without motion_controller")
        sys.exit(1)
    # if not gamepad_controller.is_alive():
    #     log.error("SpotMicro can't work without gamepad_controller")
    #     sys.exit(1)

    # Wait till the processes end
    send_controller.join()
    recv_controller.join()
    abort_controller.join()
    motion_controller.join()
    GUI_controller.join()
    # gamepad_controller.join()
    

    close_controllers_queues(communication_queues)


if __name__ == '__main__':
    # log.info('SpotMicro starting...')

    try:
        main()

    except KeyboardInterrupt:
        log.info('Terminated due Control+C was pressed')

    else:
        log.info('Normal termination')
