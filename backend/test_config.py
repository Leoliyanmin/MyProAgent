import sys
sys.path.insert(0, 'server_backend')
from config import settings

print(f"TEST_MODE: {settings.TEST_MODE}")
print(f"Type: {type(settings.TEST_MODE)}")