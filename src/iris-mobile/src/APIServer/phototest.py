import base64
import requests
import urllib
import cStringIO
from PIL import Image


url = "http://ingraphs.prod.linkedin.com/api/v2/img/dashboard/inmon-system-alerts/graph/Inmon%20-%20Pipeline%20Signal%20End%20to%20End?fabrics=prod-ltx1&legend=false&show_autoalerts&start=1498053687&end=1498075287&height=80&width=400&as_png&timezone=US/Pacific"

file = cStringIO.StringIO(urllib.urlopen(url).read())
img = Image.open(file)
encoded_string = base64.b64encode(urllib.urlopen(url).read())
print encoded_string
