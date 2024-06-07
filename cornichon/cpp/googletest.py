from __future__ import annotations
import copy
import re
import common
import cpputils


def Settings():
    settings = cpputils.Settings()
    settings["cases"]["scenario"] = "Camel"
    settings["cases"]["test"] = "Camel"
    settings["scenarios file"] = "../scenarios/scenarios.h"
    return settings


def HelpSettings():
    settings = cpputils.HelpSettings()
    settings["scenarios file"] = "The path to the generated scenarios to include"
    return settings


def Generate(parsed, settings):
    scenarios = parsed[0]
    feature = parsed[1]
    featureName = common.FeatureName(feature, settings["cases"]["namespace"])
    namespace = common.Tokenise(featureName, settings["cases"]["namespace"])
    testFixtureName = settings['test fixture name']
    buffer = """
// Other bespoke headers
#include "[[scenarios file]]"

// Third party headers
#include "gtest/gtest.h"

namespace [[fullnamespace]][[braceSep]]{
[[indent]]class [[testfixture]] : public ::testing::Test[[braceIndent]]{
[[indent]]protected:
[[indent]][[indent]]void SetUp() override[[braceIndentL2]]{
[[indent]][[indent]]}

[[indent]][[indent]]void TearDown() override[[braceIndentL2]]{
[[indent]][[indent]]}
[[indent]]};

[[TestBody]]
[[endnamespace]]
"""[1:]

    buffer = buffer.replace("[[scenarios file]]", settings["scenarios file"])
    buffer = buffer.replace("[[testfixture]]", testFixtureName)
    ns = cpputils.NameSpace(settings, namespace)
    buffer = buffer.replace("[[fullnamespace]]", ns.Begin())
    buffer = buffer.replace("[[endnamespace]]", ns.End())
    decl = "  static void {0}({1})"
    testdecl = f"  TEST_F({testFixtureName}, {{0}})"
    cpp = cpputils.Cpp(settings, decl, testdecl, settings['indent'])
    buffer = buffer.replace("[[braceIndent]]", settings['braceIndent'])
    braceIndentL2 = (
        settings['bracesep'] + settings['indent'] * 2) if '\n' in settings['bracesep'] else settings['bracesep']
    buffer = buffer.replace("[[braceIndentL2]]", braceIndentL2)
    buffer = buffer.replace("[[indent]]", settings['indent'])
    testBody = cpp.TestBody(scenarios, settings)
    if (not testBody or testBody.isspace()):
        buffer = buffer.replace("\n[[TestBody]]\n", testBody)
    else:
        buffer = buffer.replace("[[TestBody]]", testBody)
    buffer = buffer.replace("[[braceSep]]", settings['bracesep'])

    return buffer


def ReGenerate(parsed: tuple[list, str], settings: dict):
    '''
    Similar to the generate function

    Used with parse diff to generate cpp file text for new test cases only

    Args:
        parsed: two-tuple of:
            1. list of scenario objects
            2. string feature name
        setting: settings for given framework
    '''
    scenarios = parsed[0]
    feature = parsed[1]
    featureName = common.FeatureName(feature, settings["cases"]["namespace"])
    namespace = common.Tokenise(featureName, settings["cases"]["namespace"])
    testFixtureName = settings['test fixture name']
    buffer = """
namespace [[fullnamespace]][[braceSep]]{


[[TestBody]]
[[endnamespace]]
"""[1:]

    ns = cpputils.NameSpace(settings, namespace)
    buffer = buffer.replace("[[fullnamespace]]", ns.Begin())
    buffer = buffer.replace("[[endnamespace]]", ns.End())
    decl = "  static void {0}({1})"
    testdecl = f"  TEST_F({testFixtureName}, {{0}})"
    cpp = cpputils.Cpp(settings, decl, testdecl, settings['indent'])
    buffer = buffer.replace("[[braceIndent]]", settings['braceIndent'])
    braceIndentL2 = (
        settings['bracesep'] + settings['indent'] * 2) if '\n' in settings['bracesep'] else settings['bracesep']
    buffer = buffer.replace("[[braceIndentL2]]", braceIndentL2)
    testBody = cpp.TestBody(scenarios, settings)
    if (not testBody or testBody.isspace()):
        buffer = buffer.replace("\n[[TestBody]]\n", testBody)
    else:
        buffer = buffer.replace("[[TestBody]]", testBody)
    buffer = buffer.replace("[[TestBody]]", testBody)
    buffer = buffer.replace("[[braceSep]]", settings['bracesep'])

    # if ReGenerate is called with no differing test cases
    if (len(testBody.strip()) == 0):
        return ""
    return buffer


def ParseOutput(googleTestFileText: str):
    '''
    Get all test case names in a cpp file
    Args:
        googleTestFileText: string representing content of the cpp file
    Returns:
        testCases: set of all test case names found in text
    '''
    testCases = set()

    pattern = re.compile(r"(Scenarios::)([\s\\]*)([^\s]*)")
    matches = re.findall(pattern, googleTestFileText)
    for match in matches:
        testCases.add(match[2])
    return testCases


def ParseDiff(parsed: tuple[list, str], symbols: set, settings: dict):
    '''
    Find difference in symbols (scenario names) found in feature file and those in existing cpp file
    Args:
        parsed: two-tuple of:
            1. list of scenario objects
            2. string feature name
        symbols: set of test case names found in existing cpp file
        setting: settings for given framework
    Returns:
        A new object of type same as parsed but only the containing the differing test cases

    Example:
    >>> parsed = gherkin.Parse(input, settings)
        existingSymbols = ParseOutput(existingText)
        newParsed = ParseDiff(parsed,existingSymbols,settings)
    '''

    diff = []
    scenarios = parsed[0]
    for scenario in scenarios:
        # common.Tokenise creates test case name from a sentence like "Get a
        # socket" => "GetASocket"
        testCaseName = common.Tokenise(
            scenario.lines.split("\n")[0],
            settings["cases"]["test"])
        if (testCaseName not in symbols):
            diff.append(scenario)
    newParsed = copy.deepcopy(parsed)
    newParsed[0] = diff
    return newParsed
