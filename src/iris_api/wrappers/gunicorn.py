import os
from iris_api.api import load_config_file, get_api
application = get_api(load_config_file(os.environ['CONFIG']))
