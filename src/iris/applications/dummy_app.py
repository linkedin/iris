class dummy_app(object):
    name = 'dummy app'

    def __init__(self, vendor):
        self.vendor = vendor

        # Contrived example of how a sample application can change how a
        # message is sent
        self.time_taken = 2

    def send(self, message):
        return self.vendor.send(message, {'time_taken': self.time_taken})
