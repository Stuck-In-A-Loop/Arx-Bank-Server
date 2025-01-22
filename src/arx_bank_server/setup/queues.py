import multiprocessing

from arx_bank_server.setup import settings

frame_queue: multiprocessing.Queue = multiprocessing.Queue()
