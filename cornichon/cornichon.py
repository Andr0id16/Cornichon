"""A small Gherkin DSL parser that generates stub code against various test frameworks"""
import gherkin


def Settings(output):
    """Get the default settings for the output type"""
    mod = gherkin.Import(output)
    settings = mod.Settings()
    gherkin.Import(output, True)
    return settings


def PrintSettings(settings, level="settings"):
    """Utility that prints all the given settings"""
    for key in settings:
        try:
            if type(settings[key]) is str:
                print('{}["{}"] = "{}"'.format(level, key, settings[key]))
            else:
                PrintSettings(settings[key], '{}["{}"]'.format(level, key))
        except TypeError:
            pass


def HelpSettings(output):
    """Utility that prints all the help for individual settings"""
    mod = gherkin.Import(output)
    settings = mod.HelpSettings()
    gherkin.Import(output, True)
    PrintSettings(settings)


def ListModules():
    """Utility that lists all the output types available to generate stub code"""
    for mod in gherkin.ListModules():
        print(mod)


def Generate(input, settings, output):
    """Generate the stub code for the output type"""
    parsed = gherkin.Parse(input, settings)
    mod = gherkin.Import(output)
    stubCode = mod.Generate(parsed, settings)
    gherkin.Import(output, True)
    stubCode = LimitCharacters(stubCode,PATTERN,DEFAULT_CHUNK_SIZE)
    return stubCode

def ReGenerate(input:str, existingText:str, settings:dict, output:str):
    """ReGenerate the stub code for the output type"""
    parsed = gherkin.Parse(input, settings)
    mod = gherkin.Import(output)
    existingSymbols = mod.ParseOutput(existingText)
    newParsed = mod.ParseDiff(parsed,existingSymbols,settings)
    stubCode = mod.ReGenerate(newParsed, settings)
    gherkin.Import(output, True)
    stubCode = LimitCharacters(stubCode,PATTERN,DEFAULT_CHUNK_SIZE)
    return stubCode

DEFAULT_CHUNK_SIZE = 250

# characters where text can be split
PATTERN = [' ','+','-','::',",","(","["]


def LimitCharacters(text:str,pattern:list[str]=PATTERN,chunkSize:int=DEFAULT_CHUNK_SIZE):
    '''
    Transform a string into lines with at most chunkSize characters per line
    If possible string is split at 

    Args:
        text : string to be transformed
        chunkSize : maximum size of line, DEFAULT_CHUNK_SIZE = 250
    Returns:
        transformed string
    Examples:
    >>> LimitCharacters("Paragh with more than 250 chars in a line",[' ','+','-','::',",","(","["],250)
    '''
    lines = text.split("\n")
    for index,line in enumerate(lines):
        
        if(len(line)>chunkSize):
            try:
                # try splitting at character in pattern
                lines[index] = CreateAndWrapChunksSmart(line,pattern,chunkSize) 
            except ValueError as e:
                # if not possible, split at the 250th character, doesn't preserve indentation 
                lines[index] = CreateAndWrapChunks(line,chunkSize=DEFAULT_CHUNK_SIZE)
                print(f"line {index}:",e, ", splitting using dumb method")
            except Exception as e:
                print(f"line {index}:",e)
    return '\n'.join(lines)



def CreateAndWrapChunks(line:str,chunkSize:int=DEFAULT_CHUNK_SIZE):
    '''
    Split line into lines with at most chunkSize characters per line by splitting at indices that are multiples of chunkSize

    Does not preserve indentation 

    Args:
        line : line to be transformed
        chunkSize : maximum size of line, DEFAULT_CHUNK_SIZE = 250

    Returns:
        transformed line

    Examples:
    >>> CreateAndWrapChunks("Line with more than 250 chars")
    '''    
    # might be faster than loop
    # list comprehension for getting chunks of size chunkSize
    # max range for i is len(line) because min value of limit is 1, in which case there will be len(line) chunks of size 1 (the characters of line)
    # subtracting one for the line splicing character "\"
    return '\\\n'.join([line[i:i+chunkSize-1] for i in range(0,len(line),chunkSize-1)])

def CreateAndWrapChunksSmart(line:str,pattern:list[str],chunkSize:int=DEFAULT_CHUNK_SIZE,):
    '''
    Split line into lines with at most chunkSize characters per line by splitting at last valid one of " +-*," characters

    Args:
        line : line to be transformed
        pattern : list of characters that are valid split characters
        chunkSize : maximum size of line, DEFAULT_CHUNK_SIZE = 250

    Returns:
        transformed line

    Examples:
    >>> CreateAndWrapChunksSmart("Line with more than 250 chars",[" ","+"],250)
    '''

    chunkStart=0

    # need to add extra element in beginning to add indentation for first chunk
    lines = [""]
    strippedLine = line.strip()
    indent = len(line) - len(strippedLine) 

    # While there are more than 250 characters left to process
    while(len(strippedLine)-chunkStart>250):
        chunk = strippedLine[chunkStart:chunkStart+chunkSize]
        chunkSplitPos = findValidIndex(chunk,pattern)

        # Doesn't work if none of the pattern characters are in the stripped line
        if(chunkSplitPos==-1):
            raise ValueError(f"Cannot find splittable character in stripped line of size greater than {chunkSize}")
        
        # chunkSplitPos is only within current chunk
        # to find split index in entire string, need to add chunkSplitPos to the index where current chunk starts 
        lastSplitIndex = chunkStart+chunkSplitPos
        lines.append(strippedLine[chunkStart:lastSplitIndex+1])

        # to start next chunk
        chunkStart = lastSplitIndex+1
    lines.append(strippedLine[chunkStart:])

    # join with newline and indentation in between
    return f"\n{' '*indent}".join(lines)

def findValidIndex(text:str,pattern:list[str]):
    '''
    Given a pattern find last index of meaningless character from pattern

    Args:
        text: sentence/line to find the valid split index in
        pattern: list of characters that are valid split characters
    Returns:
        index of in text if valid character from pattern was found, else -1
    Example:
    >>> findValidIndex("...lotsofcharacters morecharacters...."," +-*,")
    19
    >>> findValidIndex("...lotsofcharacters_morecharacters...."," +-*,")
    -1
    '''

    inString = [] # stack to store " and ' to find if a string has been opened - like valid parantheses
    lastValidIndex = -1
    for i in range(len(text)):
        if(text[i] in ["'",'"']):
            if(inString and inString[-1]==text[i]):
                inString.pop()
            else:
                inString.append(text[i])
        if(text[i] in pattern and not inString):
            lastValidIndex = i
    return lastValidIndex