import os
import logging
from iris.config import load_config
from iris.api import get_api

logging.basicConfig(format='[%(asctime)s] [%(process)d] [%(levelname)s] %(name)s %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S %z')
application = get_api(load_config(os.environ['CONFIG']))
