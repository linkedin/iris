import os
from iris.api import load_config_file, get_api
application = get_api(load_config_file(os.environ['CONFIG']))
