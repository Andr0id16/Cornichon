import common
import cpputils

def Settings():
    settings = cpputils.Settings()
    return settings


def HelpSettings():
    settings = cpputils.HelpSettings()
    return settings


class PrintScenario(common.PrintScenario):
    def __init__(self,settings):
        super().__init__()
        self.line = f"\n{settings['indent']*4}std::clog << %s << std::endl;"
        self.contractions = {' << ""': '', ' "" << ': ' '}
        self.sub = '" << %s << "'
        self.step = """
[[indent]][[indent]][[indent]]/// Gherkin DSL step
[[indent]][[indent]][[indent]]void [[stepName]]([[arguments]])[[braceIndentL3]]{
[[description]]
[[indent]][[indent]][[indent]]}

"""[1:]
        # self.step = self.step.replace("[[braceIndent]]",settings['braceIndent'])
        braceIndentL3 = (settings['bracesep'] + settings['indent']*3) if '\n' in settings['bracesep'] else settings['bracesep']

        self.step = self.step.replace("[[braceIndentL3]]",braceIndentL3)

        # self.step = self.step.replace("[[braceSep]]",settings['bracesep'])
        self.step = self.step.replace("[[indent]]",settings['indent'])


def Generate(parsed, settings):
    scenarios = parsed[0]
    feature = parsed[1]
    featureName = common.FeatureName(feature, settings["cases"]["namespace"])

    printer = PrintScenario(settings) # !!!THE PRINT SCENARIO CLASS DEFINED IN THIS FILE!!!
    featureDesc = printer.FeatureDesc(feature)

    concat = """
#pragma once

// Local headers

// Third party headers

// Standard library headers
#include <iostream>
#include <string>

namespace [[fullnamespace]] {
"""[1:]

    namespace = common.Tokenise(featureName, settings["cases"]["namespace"])
    namespace = cpputils.NameSpace(settings, namespace + "::Scenarios")
    concat = concat.replace("[[fullnamespace]]", namespace.Begin())

    for scenario in scenarios:
        buffer = """
[[indent]]/// Test class scenario
[[indent]]class [[featureName]][[braceIndent]]{
[[indent]][[indent]]public:
[[indent]][[indent]][[indent]]/// Constructor
[[indent]][[indent]][[indent]][[featureName]]()[[braceIndentL3]]{
[[documentation]]
[[indent]][[indent]][[indent]]}

[[steps]]
  };

"""[1:]

        buffer = buffer.replace("[[featureName]]", common.Tokenise(scenario.lines, settings["cases"]["class"]))
        documentation = printer.Documentation(scenario, featureDesc, settings)
        buffer = buffer.replace("[[documentation]]", documentation)
        buffer = buffer.replace("[[steps]]", printer.Steps(scenario, settings))
        buffer = buffer.replace("[[braceIndent]]",settings['braceIndent'])
        braceIndentL3 = (settings['bracesep'] + settings['indent']*3) if '\n' in settings['bracesep'] else settings['bracesep']

        buffer = buffer.replace("[[braceIndentL3]]",braceIndentL3)

        buffer = buffer.replace("[[braceSep]]",settings['bracesep'])
        buffer = buffer.replace("[[indent]]",settings['indent'])
        concat += buffer

    concat = concat[:-2] + """
[[endnamespace]]
""".replace("[[endnamespace]]", namespace.End())
    return concat


def ReGenerate(parsed:tuple[list,str], settings:dict):
    '''
    Similar to the generate function
    
    Used with parse diff to generate hpp file text for new scenarios only

    Args:
        parsed: two-tuple of:
            1. list of scenario objects
            2. string feature name
        setting: settings for given framework
    '''
    scenarios = parsed[0]
    feature = parsed[1]
    featureName = common.FeatureName(feature, settings["cases"]["namespace"])

    printer = PrintScenario()
    featureDesc = printer.FeatureDesc(feature)
    # There are two extra spaces followed by new line after "[[fullnamespace]] {", this is to preserve opening "{"  in case there are no new scenarios
    # In case of no new scenarios and no extra spaces the 'concat = concat[:-2] + """' line removes "{"
    concat = """
namespace [[fullnamespace]][[braceSep]]{  
"""[1:]

    namespace = common.Tokenise(featureName, settings["cases"]["namespace"])
    namespace = cpputils.NameSpace(settings, namespace + "::Scenarios")
    concat = concat.replace("[[fullnamespace]]", namespace.Begin())
    beforeScenarios = concat
    for scenario in scenarios:
        buffer = """
[[indent]]/// Test class scenario
[[indent]]class [[featureName]][[braceIndent]]{
[[indent]][[indent]]public:
[[indent]][[indent]][[indent]]/// Constructor
[[indent]][[indent]][[indent]][[featureName]]()[[braceIndentL3]]{
[[documentation]]
[[indent]][[indent]][[indent]]}

[[steps]]
  };

"""[1:]

        buffer = buffer.replace("[[featureName]]", common.Tokenise(scenario.lines, settings["cases"]["class"]))
        documentation = printer.Documentation(scenario, featureDesc, settings)
        buffer = buffer.replace("[[documentation]]", documentation)
        buffer = buffer.replace("[[steps]]", printer.Steps(scenario, settings))
        buffer = buffer.replace("[[braceIndent]]",settings['braceIndent'])
        braceIndentL2 = (settings['bracesep'] + settings['indent']*2) if '\n' in settings['bracesep'] else  settings['bracesep']
        buffer = buffer.replace("[[braceIndentL2]]",braceIndentL2)
        buffer = buffer.replace("[[braceSep]]",settings['bracesep'])
        buffer = buffer.replace("[[indent]]",settings['indent'])


        concat += buffer

    if(len(concat)==len(beforeScenarios)):
        return ""
    concat = concat[:-2] + """
[[endnamespace]]
""".replace("[[endnamespace]]", namespace.End())
    return concat


import re
def ParseOutput(scenariosFileText:str):
    '''
    Get all scenario names in a header file
    Args:
        scenariosFileText: string representing content of the header file
    Returns:
        scenarios: set of all scenario names found in text
    '''
    scenarios = set()
    pattern = re.compile(r"(class[\s\\]*)(\S*)([\s\\]*{)")
    matches = re.findall(pattern,scenariosFileText)
    for match in matches:
        scenarios.add(match[1])
    return scenarios


import copy
def ParseDiff(parsed:tuple[list,str],symbols:set,settings:dict):
    '''
    Find difference in symbols (scenario names) found in feature file and those in existing hpp file  
    Args:
        parsed: two-tuple of:
            1. list of scenario objects
            2. string feature name
        symbols: set of test case names found in existing hpp file
        setting: settings for given framework
    Returns:
        A new object of type same as parsed but only the containing the differing scenarios
    
    Example:
    >>> parsed = gherkin.Parse(input, settings)
        existingSymbols = ParseOutput(existingText)
        newParsed = ParseDiff(parsed,existingSymbols,settings)
    '''
    diff = []
    scenarios = parsed[0]
    for scenario in scenarios:

        # common.Tokenise creates scenario name from a sentence like "Get a socket" => "GetASocket" 
        scenarioName = common.Tokenise(scenario.lines.split("\n")[0], settings["cases"]["class"])
        if(scenarioName not in symbols):
            diff.append(scenario)
    newParsed = copy.deepcopy(parsed)
    newParsed[0] = diff
    return newParsed
            
