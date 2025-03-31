# Author:   Mark Buchanan
# Date:     31 March 2025
# Purpose:  Provide example MajorMUD parsing line-by-line as would be inside a telnet client
# Contact:  mab535@gmail.com
# Copyright (C) 2025 Mark Buchanan


# TODOS:
# ------
# Parse Obvious exits, store them in a list similar to my "stuff" variable for items on the ground (you notice...)
# Parse "Also here: " for players and monsters
# Add a python class to store characters:
#   can get class from 'who' along with estimating the level
#   can get race and stats (if needed) from looking at them
#   can get a detalied inventory list (if needed) from looking at them
# Convert this into a python class/object that gets fed a stream (like that of telnet) and keeps track of state and updates data internally
# Add JSON files to "known players", "items", "Monsters", etc. and load them on startup
#   e.g. auto collect money, certain items, flag some monsters as non-hostile, etc.
# [SEPARATELY] figure out combat, path planning, exp/hr, round timing, etc.


# DONE:
# -----
# Parses looking at players and it will pull the name and items they're wearing (nothing with description yet)
# Parses parse the 'who' command for name, gang (if applicable) and alignment
# Parses the current room, also trying to use the megamud parlance of "known room" vs "unknown" room
# Parses "You notice XYZ here." for items in the room and stores them in a list


# control variables for parsing out the various types of messages
doLooking = False
doYouNotice = False
doCurrentAdventurers = False
doRooms = True

# Constants
BLANK_LINE = "\n"
CURRENTADVENTURERSBANNER = "         ===================\n"
KNOWN_ROOMS = ["Newhaven, Arena", "Newhaven, General Store", "Newhaven, Village Entrance", "Newhaven, Armour Shop", "Newhaven, Spell Shop"]

# variables for current adventurers list
currentAdventurersContinued = False
currentAdventurersBlankLineCount = 0

# variables for looking at someone
lookingContinued = False
lookingBlankLineCount = 0

# variables for You notice...
youNoticeContinued = False
partialItemStr = ""
handlePartialItem = False
doneProcessingYouNotice = False
stuff = []

# debug function for finding out what characters are on a line
def printStrBytes(strIn):

    print("String: " + strIn)
    print(list(strIn))

# helper function to strip out gang names, character name, item slot, etc.
def getValueBetweenDelims(text, start_delimiter, end_delimiter):

    start_index = text.find(start_delimiter)
    if start_index == -1:
        return None

    start_index += len(start_delimiter)
    end_index = text.find(end_delimiter, start_index)
    if end_index == -1:
        return None

    return text[start_index:end_index]

currentRoom = "NONE"

# test capture file
with open(r"test.txt", "r") as file:
#with open(r"2025-03-31_10-56-19.log", "r") as file:

    line = file.readline()

    while line:

        ####################################
        #        CURRENT ADVENTURERS       #
        ####################################
        if line == CURRENTADVENTURERSBANNER or currentAdventurersContinued and doCurrentAdventurers:
   
            # state to say we are in Current Adventurers
            currentAdventurersContinued = True

            # if we hit both blank lines, we are done with the processing
            if currentAdventurersBlankLineCount == 2:
                currentAdventurersBlankLineCount = 0
                currentAdventurersContinued = False

            # determine if we have a blank line/carriage return
            if line == BLANK_LINE:
                currentAdventurersBlankLineCount += 1

            # this is a don't care line for the "========" banner
            elif line == CURRENTADVENTURERSBANNER:
                x = 1
            elif currentAdventurersBlankLineCount == 1:

                # ok now we have the data
                line = line.rstrip()

                # we split at the '-' character
                # ex:     Good Eddie Vedder          -  Troubadour  of -=<WoToN>=-
                # becomes:  [0]:      Good Eddie Vedder          
                #           [1]:  Troubadour  of -=<WoToN>=-
                toks = line.split(' - ')

                # for [0], we need to strip out the characters
                #alignmentName = toks[0].join()
                alignmentName = "".join(toks[0])
                alignment = alignmentName[1:9].replace(' ','')
                
                if alignment == "":
                    print("ALIGNMENT: NEUTRAL")
                else:
                    print("ALIGNMENT: " + alignment)

                characterName = alignmentName[9:].strip()
                print("NAME: " + characterName)


                # for [1], we split on 'of' for title and gang
                titleGang = "".join(toks[1])
                if 'of' in titleGang:
                    title = titleGang.split('of')[0].strip()
                    print("TITLE: " + title)
                    gang = titleGang.split('of')[1].strip()
                    print("GANG: " + gang)
                    print("--------------------")
                else:
                    title = titleGang.split('of')[0].strip()
                    print("TITLE: " + title)
                    print("--------------------")




        ####################################
        #       LOOKING AT PLAYER          #
        ####################################
        

        # FULL EXAMPLE - has the bracket line, description and 3 blank lines to complete
        # a "look" processing block
        # [ Violet Plant ]
        # Violet is a stout, moderately built Human Priest with no hair and black eyes.
        # He moves cautiously, and is likable in an unassuming sort of way.  Violet
        # appears to be intelligent and looks fairly knowledgeable.  He is unwounded.

        # He is equipped with:

        # padded gloves                  (Hands)
        # padded vest                    (Torso)
        # quarterstaff                   (Weapon Hand)

        if (('[ ' in line and ' ]' in line) or lookingContinued) and doLooking:

            lookingContinued = True

            # if it is the first line, like [ Violet Plant ], get the name of the character
            if '[ ' in line:
                name = getValueBetweenDelims(line, '[ ', ' ]')
                print("LOOKING AT: " + name)

            # blank line counter
            if line == BLANK_LINE:
                lookingBlankLineCount += 1
                
                if lookingBlankLineCount == 3:
                    lookingContinued = False
                    lookingBlankLineCount = 0
                    print("DONE LOOKING")

            # else we don't have a blank line and should process it
            else:

                # 1 blank line is the physical description
                # TODO: mine for stats? does anyone care about that?


                # 2 blank lines is the equipped items section
                if lookingBlankLineCount == 2:
                    slot = getValueBetweenDelims(line, '(', ')')
                    print("SLOT: " + slot)
                    item = line.split('(')[0].strip()
                    print("ITEM: " + item)


        ####################################
        #       DETERMINING ROOM           #
        ####################################
        
        # kind of heuristic based?, meaning it:
        # has exactly one ',' 
        # is 30 chararacters or less?
        # removing the case of  "Also here: ...."
        # needs to start with a capital letter (ascii code < 90)

        if line.count(',') == 1 and len(line) <= 30 and line[0:4] != 'Also' and ord(line[0]) < 90 and doRooms: 
            room = line.strip()

            currentRoom = room
        
                
        ####################################
        #       You notice......           #
        ####################################               
        if ('You notice' in line or youNoticeContinued) and doYouNotice:
            


            # this section ends with a '.'
            # if it isn't there, there are additional lines
            if '.' not in line and 'You notice' in line:
                youNoticeContinued = True
                chompedLine = line.split('You notice')[1]
                toks = chompedLine.split(',')
                lastToken = str(toks[-1]).lstrip()

                for x in toks[:-1]:
                    stuff.append(x.lstrip())

                if lastToken[-1] == '\n':
                    partialItemStr = lastToken.rstrip() + " "
                    handlePartialItem = True
            # this is a single line
            elif '.' in line and 'You notice' in line:
                
                chompedLine = line.split('You notice')[1]
                toks = chompedLine.split(',')

                if len(toks) == 1:
                    myTok = str(toks[0])
                    myTok = myTok[1:-7]
                    stuff.append(myTok)
                else:
                    lastTok = str(toks[-1])
                    lastTok = lastTok[1:-7]

                    for x in toks[0:-1]:
                        stuff.append(x.lstrip())

                    stuff.append(lastTok)
                doneProcessingYouNotice = True

            # this is just a line of items separated by ','s
            elif '.' not in line and 'You notice' not in line:
                toks = line.split(',')
                lastToken = str(toks[-1])

                # if we need to rebuild the first item, append the string to the first token
                if handlePartialItem:
                    firstToken = partialItemStr + toks[0]
                    handlePartialItem = False
                    partialItemStr = ""
                    toks[0] = firstToken

                for x in toks[:-1]:
                    stuff.append(x.lstrip())

                if lastToken[-1] == "\n":
                    lastToken = lastToken.lstrip()
                    partialItemStr = lastToken.rstrip() + " "
                    handlePartialItem = True

            # ok now the section is ended
            else:
                toks = line.split(',')
                lastToken = str(toks[-1])

                # if we need to rebuild the first item, append the string to the first token
                if handlePartialItem:
                    firstToken = partialItemStr + toks[0]
                    handlePartialItem = False
                    partialItemStr = ""
                    stuff.append(firstToken)
                else:
                    stuff.append(toks[0])

                for x in toks[1:-1]:
                    stuff.append(x.lstrip())

                # handle the last token
                lastTok = str(toks[-1])
                stuff.append(lastTok[1:-7])
                youNoticeContinued = False
                doneProcessingYouNotice = True
                # DO YOUR PROCESSING ON THE LIST HERE
                # TODO


            if doneProcessingYouNotice:
                print("Ok stuff is: " + str(stuff))
                stuff = []
                doneProcessingYouNotice = False

        # get the next line and start all over again
        line = file.readline()