# Author:   Mark Buchanan
# Date:     31 March 2025
# Purpose:  Test file for working with a capture
# Contact:  mab535@gmail.com
# Copyright (C) 2025 Mark Buchanan

from majormudParser import majormudParser 

# instantiate an object
mp = majormudParser()

# test capture file
with open(r"2025-03-31_10-56-19.log", "r") as file:

    # read the first line of the capture
    line = file.readline()

    while line:

        # main call, feed a line to the class and let it do its thing
        mp.process_line(line)

        # grab the next while not EOF and continue processing
        line = file.readline()


