from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
WRITE_KEY = REDIZ_COLLIDER_CONFIG["write_key"]

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint.pprint(rdz.get_home(write_key=WRITE_KEY))
    print(WRITE_KEY)