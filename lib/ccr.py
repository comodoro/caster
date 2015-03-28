﻿

"""
Continuous command recognition for programmers
============================================================================

This module allows the user switch quickly between programming languages
and use continuous command  recognition with each. It is based on the work
of many others, including people that I haven't listed here.
Thanks Christo Butcher, davitenio, poppe1219, ccowan


"""
import time

from dragonfly import *

from lib import settings, utilities


try:
    import pkg_resources
    pkg_resources.require("dragonfly >= 0.6.5beta1.dev-r99")
except ImportError:
    pass

grammar = None
current_combined_rule_ccr = None
current_combined_rule_nonccr = None
rule_pairs = {}

def merge_copy(rule1, rule2, context):
    
    if rule1 == None:
        raise Exception("first parameter can't be null")
    if rule2 != None:
        mapping = rule1._mapping.copy()
        mapping.update(rule2._mapping)
        extras_dict = rule1._extras.copy()
        extras_dict.update(rule2._extras)
        extras = extras_dict.values()
        defaults = rule1._defaults.copy()
        defaults.update(rule2._defaults)
        return MappingRule(rule1._name + "+" + rule2._name, mapping, extras, defaults, rule1._exported, context)
    else:
        return MappingRule(rule1._name, rule1._mapping, rule1._extras.values(), rule1._defaults, rule1._exported, context)

def merge_copy_compatible(rule1, rule2):
    if rule1 == None or rule2 == None:
        return True
    
    result = True
    
    for key in rule1._mapping:
        if key in rule2._mapping:
            result = False
    return result

class ConfigCCR(Config):
    def __init__(self, name):
        Config.__init__(self, name)
        self.cmd = Section("Language section")
        self.cmd.map = Item(
            {"mimic <text>": Mimic(extra="text"), },
            namespace={"Key": Key, "Text":  Text, }
        )
        self.cmd.extras = Item([Dictation("text")])
        self.cmd.defaults = Item({})
        self.cmd.ncmap = Item(
            {"mimic <text>": Mimic(extra="text"), },
            namespace={"Key": Key, "Text":  Text, }
        )
        self.cmd.ncextras = Item([Dictation("text")])
        self.cmd.ncdefaults = Item({})
        self.cmd.ncactive = Item(False)   

def generate_language_rule_pair(path):
    ''' creates a CCR subsection from a text file, also optionally a non-CCR subsection '''
    #---------------------------------------------------------------------------
    language = path.split("/")[-1].split(".")[-2]
    
    configuration = ConfigCCR("CCR " + language)
    configuration.load(path)
    #---------------------------------------------------------------------------
    ccr = MappingRule(exported=False,
        mapping=configuration.cmd.map,
        extras=configuration.cmd.extras,
        defaults=configuration.cmd.defaults)
    nonccr = None
    if configuration.cmd.ncactive:#.get_value():
        nonccr = MappingRule(exported=False,
            mapping=configuration.cmd.ncmap,
            extras=configuration.cmd.ncextras,
            defaults=configuration.cmd.ncdefaults)
    #---------------------------------------------------------------------------
    return (ccr, nonccr)
#     return ccr

def create_repeat_rule(language_rule):

    alternatives = []
    alternatives.append(RuleRef(rule=language_rule))
    single_action = Alternative(alternatives)
    
    sequence_name = "sequence_" + "language"
    sequence = Repetition(single_action, min=1, max=16, name=sequence_name)
    
    
    #---------------------------------------------------------------------------
    # Here we define the top-level rule which the user can say.
    class RepeatRule(CompoundRule):
        # Here we define this rule's spoken-form and special elements.
        spec = "<" + sequence_name + "> [[[and] repeat [that]] <n> times]"
        extras = [
                    sequence,  # Sequence of actions defined above.
                    IntegerRef("n", 1, 100),  # Times to repeat the sequence.
                   ]
        defaults = {
                    "n": 1,  # Default repeat count.
                   }
        def _process_recognition(self, node, extras):
            sequence = extras[sequence_name]  # A sequence of actions.
            count = extras["n"]  # An integer repeat count.
            for i in range(count):
                for action in sequence:
                    action.execute()

    #---------------------------------------------------------------------------
    
    return RepeatRule()

# Create and load this module's grammar.
def refresh():
    global grammar, current_combined_rule_ccr, current_combined_rule_nonccr
    unload()
    grammar = Grammar("multi edit ccr")
    if current_combined_rule_ccr != None:
        grammar.add_rule(create_repeat_rule(current_combined_rule_ccr))
#         if current_combined_rule_nonccr != None:
#             grammar.add_rule(current_combined_rule_nonccr)
        grammar.load()

def initialize_ccr():
    #utilities.remote_debug('seta')#selfif ( should format self.)
    try:
        for r in settings.SETTINGS["ccr"]["modes"]:
            if settings.SETTINGS["ccr"]["modes"][r]:
                set_active(r)
    except Exception:
        utilities.simple_log()
    refresh()
    
def set_active(ccr_mode=None):
    global rule_pairs, current_combined_rule_ccr, current_combined_rule_nonccr
    new_rule_ccr = None
    incompatibility_found=False
    
    
    if ccr_mode!=None:
        # add mode
        ccr_mode = str(ccr_mode)
#     new_rule_nonccr = None
        # obtain rule: either retrieve it or generate it
        
        target_rule_pair = None
        for rule_name in rule_pairs:
            '''here for forced reload'''
            if rule_name == ccr_mode:
                target_rule_pair = rule_pairs[rule_name]
        if target_rule_pair == None:
            target_rule_pair = generate_language_rule_pair(settings.SETTINGS["paths"]["GENERIC_CONFIG_PATH"] + "/config" + ccr_mode + ".txt")
            rule_pairs[ccr_mode] = target_rule_pair
         
        # determine compatibility
        if merge_copy_compatible(target_rule_pair[0], current_combined_rule_ccr):
            new_rule_ccr = merge_copy(target_rule_pair[0], current_combined_rule_ccr, None)
#             if target_rule_pair[1]!=None and merge_copy_compatible(target_rule_pair[01], current_combined_rule_nonccr):
#                 print 'enabling '+ccr_mode+' nccr'
#                 new_rule_nonccr = merge_copy(target_rule_pair[1], current_combined_rule_ccr, None)
        else:
            # handling incompatibility
            for r in settings.SETTINGS["ccr"]["modes"]:
                if settings.SETTINGS["ccr"]["modes"][r] and not merge_copy_compatible(target_rule_pair[0], rule_pairs[r][0]):
                    settings.SETTINGS["ccr"]["modes"][r] = False
                    incompatibility_found=True
                    # add disabled rule to common section of settings
                    
        settings.SETTINGS["ccr"]["modes"][ccr_mode] = True
    
    if ccr_mode==None or incompatibility_found:
        # delete mode or incompatibility_found
        for r in settings.SETTINGS["ccr"]["modes"]:
            if settings.SETTINGS["ccr"]["modes"][r]:
                new_rule_ccr = merge_copy(rule_pairs[r][0], new_rule_ccr, None)
#                 if rule_pairs[r][1]!=None:
#                     new_rule_nonccr = merge_copy(rule_pairs[r][1], new_rule_nonccr, None)    
    
    current_combined_rule_ccr = new_rule_ccr
#     current_combined_rule_nonccr = new_rule_nonccr
    
def set_active_command(enable_disable, ccr_mode):
    ccr_mode=str(ccr_mode)
    if int(enable_disable)==1:
        set_active(ccr_mode)
    else:

        settings.SETTINGS["ccr"]["modes"][ccr_mode]=False
        set_active()
        
    # activate and save
    settings.save_config()
    refresh()

# Unload function which will be called at unload time.
def unload():
    global grammar
    if grammar: grammar.unload()
    grammar = None
