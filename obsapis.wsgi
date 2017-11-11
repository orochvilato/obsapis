activate_this = '/opt/obsapis/.pyenv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0,'/opt/obsapis')
from obsapis import app as application
