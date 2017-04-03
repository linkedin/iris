class dummy_app(object):
    name = 'dummy app'

    def __init__(self, vendor):
        vendor.time_taken = 2
        self.send = vendor.send
