#! python2.7
'''
main Caster module
Created on Jun 29, 2014
'''

import datetime, os, time, sys
start_time = datetime.datetime.now()
from castervoice.lib import settings  # requires nothing
print("\n*- Starting " + settings.SOFTWARE_NAME + " -*")

import logging
logging.basicConfig()

from dragonfly import get_engine
engine = get_engine("kaldi",
    model_dir='kaldi_model_zamia',
    # tmp_dir='kaldi_tmp',  # default for temporary directory
    # vad_aggressiveness=3,  # default aggressiveness of VAD
    # vad_padding_ms=300,  # default ms of required silence surrounding VAD
    # input_device_index=None,  # set to an int to choose a non-default microphone
    auto_add_to_user_lexicon=True,  # set to True to possibly use cloud for pronunciations
    # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
)

# Call connect() now that the engine configuration is set.
engine.connect()
import time, socket, os
from dragonfly import Function, Grammar, Playback, Dictation, Choice, Pause, RunCommand
from castervoice.lib.ccr.standard import SymbolSpecs

_NEXUS = None

settings.WSR = __name__ == "__main__"
from castervoice.lib import utilities  # requires settings
if settings.WSR:
    SymbolSpecs.set_cancel_word("escape")
from castervoice.lib import control
_NEXUS = control.nexus()
from castervoice.lib.ctrl.dependencies import find_pip, update
from castervoice.lib import navigation
navigation.initialize_clipboard(_NEXUS)

from castervoice.apps import __init__
from castervoice.lib.ccr import *
from castervoice.lib.ccr.recording import bringme, again, history
# import castervoice.lib.dev.dev
# from castervoice.asynch.sikuli import sikuli

from castervoice.lib.actions import Key
from castervoice.lib.terminal import TerminalCommand
from castervoice.lib.dfplus.state.short import R
from castervoice.lib.dfplus.additions import IntegerRefST
from castervoice.lib.dfplus.merge.mergepair import MergeInf
from castervoice.lib.dfplus.merge.mergerule import MergeRule

if not globals().has_key('profile_switch_occurred'):
    # Load user rules
    _NEXUS.process_user_content()
    _NEXUS.merger.update_config()
    _NEXUS.merger.merge(MergeInf.BOOT)


def change_monitor():
    if settings.SETTINGS["sikuli"]["enabled"]:
        Playback([(["monitor", "select"], 0.0)]).execute()
    else:
        print("This command requires SikuliX to be enabled in the settings file")

class MainRule(MergeRule):
    @staticmethod
    def generate_ccr_choices(nexus):
        choices = {}
        for ccr_choice in nexus.merger.global_rule_names():
            choices[ccr_choice] = ccr_choice
        return Choice("name", choices)

    @staticmethod
    def generate_sm_ccr_choices(nexus):
        choices = {}
        for ccr_choice in nexus.merger.selfmod_rule_names():
            choices[ccr_choice] = ccr_choice
        return Choice("name2", choices)


    mapping = {
        # update management
        # "update caster":
        #     R(DependencyUpdate([pip, "install", "--upgrade", "castervoice"])),
        # "update dragonfly":
        #     R(DependencyUpdate([pip, "install", "--upgrade", "dragonfly2"])),

        # hardware management
        "volume <volume_mode> [<n>]":
            R(Function(navigation.volume_control, extra={'n', 'volume_mode'})),
        "change monitor":
            R(Key("w-p") + Pause("100") + Function(change_monitor)),

        # window management
        'minimize':
            R(Playback([(["minimize", "window"], 0.0)])),
        'maximize':
            R(Playback([(["maximize", "window"], 0.0)])),
        "remax":
            R(Key("a-space/10,r/10,a-space/10,x")),

        # passwords

        # mouse alternatives
        "legion [<monitor>]":
            R(Function(navigation.mouse_alternates, mode="legion", nexus=_NEXUS)),
        "rainbow [<monitor>]":
            R(Function(navigation.mouse_alternates, mode="rainbow", nexus=_NEXUS)),
        "douglas [<monitor>]":
            R(Function(navigation.mouse_alternates, mode="douglas", nexus=_NEXUS)),

        # ccr de/activation
        "<enable> <name>":
            R(Function(_NEXUS.merger.global_rule_changer(), save=True)),
        "<enable> <name2>":
            R(Function(_NEXUS.merger.selfmod_rule_changer(), save=True)),
        "enable caster":
            R(Function(_NEXUS.merger.merge, time=MergeInf.RUN, name="numbers")),
        "disable caster":
            R(Function(_NEXUS.merger.ccr_off)),
    }
    extras = [
        IntegerRefST("n", 1, 50),
        Dictation("text"),
        Dictation("text2"),
        Dictation("text3"),
        Choice("enable", {
            "enable": True,
            "disable": False
        }),
        Choice("volume_mode", {
            "mute": "mute",
            "up": "up",
            "down": "down"
        }),
        generate_ccr_choices.__func__(_NEXUS),
        generate_sm_ccr_choices.__func__(_NEXUS),
        IntegerRefST("monitor", 1, 10)
    ]
    defaults = {"n": 1, "nnv": 1, "text": "", "volume_mode": "setsysvolume", "enable": -1}


control.non_ccr_app_rule(MainRule(), context=None, rdp=False)

# if globals().has_key('profile_switch_occurred'):
#     reload(sikuli)
# else:
#     profile_switch_occurred = None

print("Startup time {}".format(datetime.datetime.now() - start_time))
if settings.WSR:
    try:
        # Loop forever
        engine.do_recognition()
    except KeyboardInterrupt:
        pass
