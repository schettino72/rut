from io import BytesIO
from rut import check

from rut import saq


class TestWorker:
    def test_send_msg(self):
        w_out = BytesIO()
        worker = saq.Worker(None, w_out)
        check(worker)
