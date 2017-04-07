import os
from iris.api import load_config, get_api
application = get_api(load_config(os.environ['CONFIG']))
