import logging
import sys

class SocketIOHandler(logging.Handler):
    """A custom logging handler that emits logs over Socket.IO."""
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        log_entry = self.format(record)
        self.socketio.emit('log_message', {'data': log_entry})

def setup_logger(socketio=None):
    """Sets up the main application logger."""
    logger = logging.getLogger('BTSeedAggregator')
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Socket.IO Handler
    if socketio:
        socketio_handler = SocketIOHandler(socketio)
        socketio_handler.setFormatter(formatter)
        logger.addHandler(socketio_handler)

    return logger

# Initialize a basic logger without Socket.IO first
log = setup_logger()
