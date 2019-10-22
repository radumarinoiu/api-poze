import os
import sys
from subprocess import Popen

if len(sys.argv) == 2:
    image = str(sys.argv[1])
    Popen(["docker", "build", "-t", "{}".format(image.lower()), "./{}".format(image)]).wait()
