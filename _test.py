# coding: utf-8
from dragonfly import Grammar, MappingRule, Text, log


class MainRule(MappingRule):

    mapping = {
        u"D\xfcsseldorf":
            Text("Been there"),
        u"na\xefvet\xe9":
            Text("Bad trait"),
        u"naïve":
            Text("Gullible"),
        u"tête-à-tête":
            Text("Meeting")
    }

log.setup_log()

grammar = Grammar('sample')
grammar.add_rule(MainRule())
grammar.load()
