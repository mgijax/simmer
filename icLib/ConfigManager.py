'''
ConfigManager.py

This module defines two classes: ConfigManager and SimmerConfigParser.

A ConfigManager integrates (combines) configuration parameters coming from config files
with those given on the command line. Config files are read into an extended ConfigParser
object, and the command line parameters are injected into that object. 
The net result is SimmerConfigParser, which clients use to access all parameters
in a uniform way. 
A SimmerConfigParser is a subclass of ConfigParser.ConfigParser (standard Python lib) that
adds some convenience methods, e.g., for finding config sections containing a given variable.

Config files. Config files follow the syntax described in the docs for the standard 
ConfigParser module. Here's a little sample (see the ConfigParser docs for details):

	[DEFAULT]
	motd: Today is my birthday. 

	[SomeSection]
	someVar: Hi there
	anotherVar: %(someVar), everybody!
	message: %(anotherVar)s %(motd)s

	[AnotherSection]
	...

Config files can be specified on the command line with the -c/--config option.
This option is added by the config manager. If no config files are specified on the
command line, the default is read. The default config file is named config.cfg and
is located in the parent directory of this (Config_Manager.py) file.

Command line parameters. The command line is parsed by a standard optparse.OptionParser. 
The ConfigManager creates the OptionParser and controls when it is called. 
The client supplies a callback for adding options and otherwise configuring the parser. 
In addition, the ConfigManager adds two options of its own: -c/--config for specifying
config files, and -D/--define for adding variables to arbitrary sections (see below).
After the command line is parsed, the ConfigManager injects the results (the named options
and the positional arguments) into the SimmerConfigParser object.
Named options are injected into the section [CmdLineOpts]. They are named acoording to 
the "dest" attribute of the option and have whatever value the parsing produced. This is
often, but not always, a string. For example, the option -x is defined, given a dest 
of "xvalue" and has type="int". The config parser object will then have a variable named
"xvalue" in section "CmdLineOpts".
Positional arguments are injected into [CmdLineArgs] as the single variable "args",
whose value is a list of strings.

The -D/--define command line option is added and processed by the ConfigManager.
It allows any variable in any config section to be added/overridden.
The syntax is: 
	-D someSection.someVar=someValue
This will cause someVar in section someSection to be given the value someValue.

Example:
	
	# MyApplication.py
	from ConfigManager import ConfigManager

	# The client program defines whatever command line options it wants
	def configOpts(oParser):
	    oParser.add_option('-x','--xoption', dest='x', type="int")

	# create a ConfigManager and call readConfig.
	# result is a SimmerConfigParser
	cp = ConfigManager(configOpts).readConfig()

	# cp inherits all the ConfigParser methods
	print cp.sections()
	print cp.get('MySection', 'someVariable')

	# cp is a SimmerConfigParser, so there are some additional methods
	print cp.getConfigObj('SomeSection') # a dict with the var/value pairs
	print cp.sectionsWith('somevar', 'somevalue'):

	# command line args are available in special sections
	print cp.get('CmdLineOpts','x')
	print cp.get('CmdLineArgs','args')

'''


import sys
import os
import ConfigParser
import optparse

#-----------------------------------------------------
CMD_OPT_SECTION = "CmdLineOpts"
CMD_ARG_SECTION = "CmdLineArgs"

'''
A ConfigManager combines options specified on the command line with those specified in
a config file.
The parameter, opConfig, is a callable that accepts an instance of optparse.OptionParser; 
it adds whatever options it wants to the parser, except -c/--config and -D/--define. These
are defined by ConfigManager.
'''
class ConfigManager(object):
    def __init__(self, configureOP):
        self.cp=SimmerConfigParser()
        self.op=optparse.OptionParser()

	#
	self.op.add_option("-c", "--config", dest="configFiles", default=[], 
	    action="append",
	    metavar="FILE",
	    help="Specify a config file. This option can be repeated to specify more than one config file. Config files are read in order. If the same variable is set in multiple files, the last one wins. If (and only if) no config files are specified, the default config file is read.")

	#
	self.op.add_option("-D", "--define", dest="defs", default=[],
	    action="append",
	    metavar="section.variable=value",
	    help="Define or override a config setting.")

	#
	configureOP(self.op)

    def defaultConfigFile(self):
	return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.cfg"))

    def readConfig(self, argv=None):
	# First, parse the command line
	if argv is None:
	    argv=sys.argv
	(opts,args) = self.op.parse_args(argv)

	# Find read config files
	if len(opts.configFiles) == 0:
	    opts.configFiles.append(self.defaultConfigFile())
	self.cp.read(opts.configFiles)

	# Inject command line opts into config 
	if not self.cp.has_section(CMD_OPT_SECTION):
	    self.cp.add_section(CMD_OPT_SECTION)
	if not self.cp.has_section(CMD_ARG_SECTION):
	    self.cp.add_section(CMD_ARG_SECTION)
	for (n,v) in opts.__dict__.items():
	    self.cp.set(CMD_OPT_SECTION, n, v)
	self.cp.set(CMD_ARG_SECTION,"args",args)

	# Inject "-D" command line opts into config
	for dv in opts.defs:
	    parts = dv.split("=",1)
	    n = parts[0]
	    value = parts[1] if len(parts)==2 else None
	    parts = n.split(".", 1)
	    if len(parts) == 2:
	        section,varname = parts
	    else:
		section = CMD_OPT_SECTION
	        varname = n
	    self.cp.set(section, varname, value)

	return self.cp

#-----------------------------------------------------
'''
A SimmerConfigParser is a subclass of SafeConfigParser that adds a couple of useful methods:
	sectionsWith : returns a list of section names where the section contains a given variable
	getConfigObj : returns all the vars in a section in a dictionary
In addtion, a SimmerConfigParser has case sensitive option names.
'''
class SimmerConfigParser(ConfigParser.ConfigParser):
    # override default: make names case sensitive
    def optionxform(self, name):
        return name

    # Return True iff the given section actually defines the variable (not just inherits it from DEFAULT)
    def has_own_option(self, section, name):
        if self.has_option(section,name):
	    if self.has_option('DEFAULT',name):
		# both sections include the named option. The only way to know for
		# sure if it's inherited is to temporarily remove it from DEFAULT and see if the
		# section still has it.

		# save the current raw value then remove it
		v = self.get('DEFAULT',name,True)
		self.remove_option('DEFAULT',name)
		# see if the section still sees it. then put it back.
		res = self.has_option(section,name)
		self.set('DEFAULT',name,v)
		# return the result
		return res
	    else:
	        return True
	else:
	    return False

    # return list of variable names actually defined in the section (exclude those only inherited from DEFAULT)
    def own_options(self, section):
        return filter( lambda o:self.has_own_option(section, o), self.options(section) )

    # returns list if (name,value) pairs for items actually defined in the section.
    def own_items(self, section, raw=False):
        return filter( lambda i:self.has_own_option(section, i[0]), self.items(section,raw) )

    # returns list of section names where section contains the given var name
    # and (optionally) that var has the given value
    def sectionsWith(self,name,value=None,raw=False):
	name = self.optionxform(name)
        rlist=[]
        for s in self.sections():
	    if self.has_option(s,name):
		if value is None or value == self.get(s,name,raw):
		    rlist.append(s)
        return rlist

    # returns a dict containing all the vars in a section. If no section named, returns
    # all vars from all sections as a 2-level dict.
    def getConfigObj(self,section=None,raw=False,includeInherited=True):
	items = self.items if includeInherited else self.own_items
	if section:
	    return dict(items(section,raw))
        sectionInfo={}
        for s in self.sections():
	    sectionInfo[s] = dict(items(s,raw))
        return sectionInfo

def __testSimmerConfigParser__():
    import StringIO

    s='''

[DEFAULT]
inheritMe=howdy

[SectionOne]
foo=10
bar=%(foo)s
inheritMe=hello

[SectionTwo]
foo=99
'''
    scp = SimmerConfigParser()
    scp.readfp(StringIO.StringIO(s))

    print scp.sectionsWith("foo")
    print scp.sectionsWith("FOO")
    print scp.sectionsWith("foo","10")
    print scp.sectionsWith("bar","10")
    print scp.sectionsWith("inheritMe")
    print scp.sectionsWith("inheritMe","blah")
    print scp.getConfigObj('SectionOne')
    print scp.getConfigObj()

def __testConfigManager__():
    def setConfigOptions(op):
	op.add_option("-n", "--number", metavar="NUM", dest="n", type="int", help="A number.")
        
    argv=["-n","99", "-D", "SectionOne.bar=xyzzy","-D","newvar=17","arg1","arg2","arg3"]
    cm = ConfigManager(setConfigOptions)
    c = cm.readConfig()
    print c.sections()
    global cp
    cp = c


def __test__():
    __testSimmerConfigParser__()
    __testConfigManager__()

if __name__=="__main__":
    __test__()
