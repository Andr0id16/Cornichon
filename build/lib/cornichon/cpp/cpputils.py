import common
import gherkin


CPP_OUTPUT_TYPE = "cpp/googletest"
HPP_OUTPUT_TYPE = "cpp/cppscenarios"

GENERATE_MODE = 'w'
REGENERATE_MODE = 'a+'
DEFAULT_FIXED_TEST_FIXTURE_NAME = 'TestFixture'
DEFAULT_BRACE_SEP = "\n"
INDENT = "  "


MAX_LINE_SIZE = 255
# value of "" skips line wrap call, hence no-wrap.MIN_LINE_SIZE is part of
# cpp util settings, to pass setting tests, it is represented as an empty
# string rather than other types of 'False' values like int 0.
MIN_LINE_SIZE = ""
# characters where text can be split
# PATTERN = [', ',' ','+','-','::',"(","[","<<"] # for multi-character separators 
PATTERN = ", +-([" # for single character separators 
# !NOTE change documentation of PATTERN key accordingly


def Settings():
    settings = common.Settings()
    settings["nested namespaces"] = "true"
    settings["rootnamespace"] = "Cornichon::"
    settings["cases"]["class"] = "Camel"
    settings["cases"]["namespace"] = "Camel"
    settings["cases"]["param"] = "camel"
    settings["cases"]["step"] = "Camel"
    settings["types"]["bool"] = "bool {}"
    settings["types"]["int"] = "int {}"
    settings["types"]["uint"] = "unsigned int {}"
    settings["types"]["float"] = "double {}"
    settings["types"]["string"] = "const std::string& {}"
    settings['wrapsize'] = MIN_LINE_SIZE
    # Inserted in between class/function declaration..etc and the opening
    # brace to the body
    settings['bracesep'] = DEFAULT_BRACE_SEP
    (DEFAULT_BRACE_SEP + INDENT) if '\n' in DEFAULT_BRACE_SEP else DEFAULT_BRACE_SEP
    settings['braceIndent'] = (
        DEFAULT_BRACE_SEP + INDENT) if '\n' in DEFAULT_BRACE_SEP else DEFAULT_BRACE_SEP
    settings['indent'] = INDENT
    settings['pattern'] = PATTERN
    settings["test fixture name"] = DEFAULT_FIXED_TEST_FIXTURE_NAME
    return settings


def HelpSettings():
    help = common.HelpSettings()
    help["nested namespaces"] = "Whether to use C++ 17 nested namespaces"
    help["rootnamespace"] = "The concatenated C++ 17 namespace ending in ::"
    help["cases"]["namespace"] = help["cases"]["class"]
    help['wrapsize'] = "number of characters after which lines are wrapped"
    help['bracesep'] = "brace seperator between function/class declaration and opening brace"
    help['braceIndent'] = 'brace with the provided indent'
    help['indent'] = 'provided indentation'
    help['pattern'] = PATTERN
    help[MIN_LINE_SIZE] = str(MIN_LINE_SIZE)
    help["test fixture name"] = 'name for test fixture class'
    return help


def ArgModifier(val, type):
    if type == "bool":
        return common.Lower(val)
    if type == "string":
        return val.replace('"', '\\"')
    return val


class NameSpace:
    def __init__(self, settings, namespace):
        self.settings = settings
        self.namespace = settings["rootnamespace"] + namespace

    def Begin(self):
        if self.settings["nested namespaces"] == "true":
            return self.namespace
        return self.namespace.replace("::", " { namespace ")

    def End(self):
        if self.settings["nested namespaces"] == "true":
            return "}"
        num = self.namespace.count("::")
        val = "}"
        for i in range(num):
            val += " }"
        return val


class Cpp(common.PrintTestBody):
    def __init__(self, settings, decl, testdecl, indent):
        self.settings = settings
        self.decl = decl
        self.testdecl = testdecl
        self.indent = indent
        self.argModifier = ArgModifier
        self.step = self.indent + '  scenario.[[method]]([[arguments]]);\n'
        self.braceIndent = settings['bracesep']
        if ('\n' in self.braceIndent):
            self.braceIndent += self.indent

    def ScenarioDecl(self, line, fullArgs, settings):
        scenarioName = common.Tokenise(
            line, self.settings["cases"]["scenario"])
        return self.decl.format(scenarioName, fullArgs)

    def TestDecl(self, line):
        scenarioName = common.Tokenise(line, self.settings["cases"]["test"])
        return self.testdecl.format(scenarioName)

    def Body(self, scenario, steps):
        buffer = """ [[braceIndent]]{
[[indent]]  Scenarios::[[className]] scenario;
[[steps]]
[[indent]]}

"""[1:]
        if(not steps or steps.isspace()):
            buffer = buffer.replace("[[steps]]\n", steps.rstrip())
        else:
            buffer = buffer.replace("[[steps]]", steps.rstrip())
        buffer = buffer.replace("[[indent]]", self.indent)
        buffer = buffer.replace("[[braceIndent]]", self.braceIndent)
        lines = scenario.lines.split('\n')
        className = common.Tokenise(lines[0], self.settings["cases"]["class"])
        buffer = buffer.replace("[[className]]", className)
        return buffer

    def Example(self, line, arguments):
        buffer = """
[[testName]][[braceIndent]]{
[[indent]]  [[scenario]]([[arguments]]);
[[indent]]}
"""
        scenario = common.Tokenise(line, self.settings["cases"]["scenario"])
        testName = " ".join([scenario, arguments])
        testName = common.Tokenise(testName, self.settings["cases"]["test"])
        testName = self.testdecl.format(testName)
        buffer = buffer.replace("[[testName]]", testName)
        buffer = buffer.replace("[[braceIndent]]", self.braceIndent)
        buffer = buffer.replace("[[indent]]", self.indent)
        buffer = buffer.replace("[[scenario]]", scenario)
        buffer = buffer.replace("[[arguments]]", arguments)
        return buffer
