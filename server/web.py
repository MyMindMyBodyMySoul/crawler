
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler,  Application
from queue_manager import QueueClient
import json
import hashlib
import settings


class AnalyzeMeHandler(RequestHandler):

    def post(self):

        user_id = hashlib.sha256(str(self.request)).hexdigest()
        domain = self.get_argument('domain')

        c = QueueClient()
        qm = c.queue_manager()

        qm.put_user(domain, user_id)
        r = qm.get_user_result(user_id)
        self.write(json.dumps(r))


if __name__ == "__main__":

    application = Application([
        (r"/analyzeme", AnalyzeMeHandler),
    ])
    application.listen(settings.WEB_SERVER_PORT, settings.WEB_SERVER_ADDRESS)

    print("WebServer listen at %s:%s/analyzeme" % (settings.WEB_SERVER_ADDRESS, settings.WEB_SERVER_PORT))

    IOLoop.current().start()
