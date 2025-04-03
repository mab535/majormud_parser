# Author:   Mark Buchanan
# Date:     31 March 2025
# Purpose:  Class that processes lines of text from MajorMUD
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

class majormudParser(object):
    
    def __init__(self):
        # some constants
        self.BLANK_LINE = "\n"
        self.CURRENTADVENTURERSBANNER = "         ===================\n"
        self.KNOWN_ROOMS = ["Newhaven, Arena", "Newhaven, General Store", "Newhaven, Village Entrance", "Newhaven, Armour Shop", "Newhaven, Spell Shop"]

        # some variables for current status
        self.currentRoom = "NONE"
        self.alsoHereList = []
        self.youNoticeList = []

        # variables for picking up cash
        self.collectCopper = True
        self.collectSilver = True
        self.collectPlatinum = True
        self.collectRunic = True

        # test variable to pick up items
        self.pickUpItemList = ["padded vest"]

        # test variable for monsters
        self.monsterList = ["carrion beast"]

        # variables for current adventurers list
        self.currentAdventurersContinued = False
        self.currentAdventurersBlankLineCount = 0


        # variables for looking at someone
        self.lookingContinued = False
        self.lookingBlankLineCount = 0

        # variables for You notice...
        self.youNoticeContinued = False
        self.youNoticeCompleted = False
        self.youNoticeBuf = ""

        # variables for Also here:
        self.alsoHereContinued = False
        self.alsoHereBuf = ""
        self.alsoHereCompleted = False
        

    def process_line(self, line):
        ####################################
        #       DETERMINING ROOM           #
        ####################################
        if line.count(',') == 1 and len(line) <= 30 and line[0:4] != 'Also' and ord(line[0]) < 90:
            self.processRoom(line)

        ####################################
        #        CURRENT ADVENTURERS       #
        ####################################
        if line == self.CURRENTADVENTURERSBANNER or self.currentAdventurersContinued:
            self.processCurrentAdventurers(line)
   
        ####################################
        #       LOOKING AT PLAYER          #
        ####################################
        if (('[ ' in line and ' ]' in line) or self.lookingContinued):
            self.processLookingAtPlayer(line)

        ####################################
        #       Also here:                 #
        ####################################
        if 'Also here: ' in line or self.alsoHereContinued:
            self.processAlsoHere(line)

        ####################################
        #       You notice                 #
        ####################################
        if 'You notice ' in line or self.youNoticeContinued:
            self.processYouNotice(line)


    # helper function to strip out gang names, character name, item slot, etc.
    def getValueBetweenDelims(self, text, start_delimiter, end_delimiter):

        start_index = text.find(start_delimiter)
        if start_index == -1:
            return None

        start_index += len(start_delimiter)
        end_index = text.find(end_delimiter, start_index)
        if end_index == -1:
            return None

        return text[start_index:end_index]

    def processRoom(self, line):

        ####################################
        #       DETERMINING ROOM           #
        ####################################
        
        # kind of heuristic based?, meaning it:
        # has exactly one ',' 
        # is 30 chararacters or less?
        # removing the case of  "Also here: ...."
        # needs to start with a capital letter (ascii code < 90)

        room = line.strip()
        self.currentRoom = room

    def processCurrentAdventurers(self, line): 
            # state to say we are in Current Adventurers
            self.currentAdventurersContinued = True

            # if we hit both blank lines, we are done with the processing
            if self.currentAdventurersBlankLineCount == 2:
                self.currentAdventurersBlankLineCount = 0
                self.currentAdventurersContinued = False

            # determine if we have a blank line/carriage return
            if line == self.BLANK_LINE:
                self.currentAdventurersBlankLineCount += 1

            # this is a don't care line for the "========" banner
            elif line == self.CURRENTADVENTURERSBANNER:
                x = 1
            elif self.currentAdventurersBlankLineCount == 1:

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
                
                #if alignment == "":
                #    print("ALIGNMENT: NEUTRAL")
                #else:
                #    print("ALIGNMENT: " + alignment)

                characterName = alignmentName[9:].strip()
                #print("NAME: " + characterName)


                # for [1], we split on 'of' for title and gang
                titleGang = "".join(toks[1])
                if 'of' in titleGang:
                    title = titleGang.split('of')[0].strip()
                #    print("TITLE: " + title)
                    gang = titleGang.split('of')[1].strip()
                #    print("GANG: " + gang)
                #    print("--------------------")
                else:
                    title = titleGang.split('of')[0].strip()
                #    print("TITLE: " + title)
                #    print("--------------------")
 
    def processLookingAtPlayer(self, line):

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

            self.lookingContinued = True

            # if it is the first line, like [ Violet Plant ], get the name of the character
            if '[ ' in line:
                name = self.getValueBetweenDelims(line, '[ ', ' ]')
                #print("LOOKING AT: " + name)

            # blank line counter
            if line == self.BLANK_LINE:
                self.lookingBlankLineCount += 1
                
                if self.lookingBlankLineCount == 3:
                    self.lookingContinued = False
                    self.lookingBlankLineCount = 0
                    #print("DONE LOOKING")

            # else we don't have a blank line and should process it
            else:

                # 1 blank line is the physical description
                # TODO: mine for stats? does anyone care about that?


                # 2 blank lines is the equipped items section
                if self.lookingBlankLineCount == 2:
                    slot = self.getValueBetweenDelims(line, '(', ')')
                    #print("SLOT: " + slot)
                    item = line.split('(')[0].strip()
                    #print("ITEM: " + item)


                    #TODO: Build a character and add equipped items to the slots?
    
    def processAlsoHere(self, line):
        
        # chop off Also here if this is the first line
        if 'Also here:' in line:
                line = line[11:]

        # if we have a '.', we've ended
        if '.' in line:
            line = line.rstrip()

            # rebuild the line with all values, strip whitespace/newlines
            line = self.alsoHereBuf + " " + line
            line = line.replace('\n','')

            # tokenize on ','
            toks = line.split(',')

            # iterate over the tokens
            for x in toks:
                # get rid of leading whitespace if it exists
                if x[0] == " ":
                    x = x[1:]
                # get rid of '.' if it is there
                if x[-1] == ".":
                    x = x[:-1]

                # add item to the list
                self.alsoHereList.append(x)

            # zero out the buffer and set flags for "done processing"
            self.alsoHereBuf = ""
            self.alsoHereCompleted = True
            self.alsoHereContinued = False
        else:
                # we need to buffer
                self.alsoHereBuf += line
                self.alsoHereContinued = True

        if self.alsoHereCompleted and len(self.alsoHereList) > 0:
            #print("Also here stuff: " + str(self.alsoHereList))


            # TODO: ADD LOGIC TO HANDLE THIS LIST - attack monsters, players, etc.

            # example, iterate through the list:
            for x in self.alsoHereList:
                
                # TODO:
                # get rid of the annoying adjectives added to the monsters:
                # small, nasty, fierce, angry, thin, fat, short
                # Maybe do this in the processing above to save time?

                if x in self.monsterList:
                    print("Ok, monster " + x + " is here. I should have the program respond with: {ATTACK_TYPE} " + x)



            
            # zero out our list
            self.alsoHereList = []

    def processYouNotice(self, line):
        
        # chop off 'You notice ' if this is the first line
        if 'You notice ' in line:
                line = line[11:]

        # if we have a '.', we've ended
        if '.' in line:
            line = line.rstrip()

            # rebuild the line with all values, strip whitespace/newlines
            line = self.youNoticeBuf + " " + line
            line = line.replace('\n','')

            # tokenize on ','
            toks = line.split(',')

            # iterate over the tokens
            for x in toks:
                # get rid of leading whitespace if it exists
                if x[0] == " ":
                    x = x[1:]
                # get rid of "here." ending characters
                if ' here.' in x:
                    x = x[:-6]

                # add item to the list
                self.youNoticeList.append(x)

            # zero out the buffer and set flags for "done processing"
            self.youNoticeBuf = ""
            self.youNoticeCompleted = True
            self.youNoticeContinued = False
        else:
                # we need to buffer
                self.youNoticeBuf += line
                self.youNoticeContinued = True

        if self.youNoticeCompleted and len(self.youNoticeList) > 0:
            #print("You notice stuff: " + str(self.youNoticeList))


            # TODO: ADD LOGIC TO HANDLE THIS LIST - pick up items?

            # Example to pick up items/cash
            for x in self.youNoticeList:

                if 'copper farthing' in x and self.collectCopper:
                    print("Ok, I should have the program respond with: g " + x)

                if 'silver noble' in x and self.collectSilver:
                    print("Ok, I should have the program respond with: g " + x)

                if x in self.pickUpItemList:
                    print("Ok, the program should respond with: g " + x)

            # zero out our list
            self.youNoticeList = []