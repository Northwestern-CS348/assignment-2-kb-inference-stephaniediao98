import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[]):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

    def _get_fact(self, fact):
        """INTERNAL USE ONLY
        Get the fact in the KB that is the same as the fact argument

        Args:
            fact (Fact): Fact we're searching for

        Returns:
            Fact: matching fact
        """
        for kbfact in self.facts:
            if fact == kbfact:
                return kbfact

    def _get_rule(self, rule):
        """INTERNAL USE ONLY
        Get the rule in the KB that is the same as the rule argument

        Args:
            rule (Rule): Rule we're searching for

        Returns:
            Rule: matching rule
        """
        for kbrule in self.rules:
            if rule == kbrule:
                return kbrule

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB
        Args:
            fact_rule (Fact|Rule) - the fact or rule to be added
        Returns:
            None
        """
        printv("Adding {!r}", 1, verbose, [fact_rule])
        if isinstance(fact_rule, Fact):
            if fact_rule not in self.facts:
                self.facts.append(fact_rule)
                for rule in self.rules:
                    self.ie.fc_infer(fact_rule, rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.facts.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.facts[ind].supported_by.append(f)
                else:
                    ind = self.facts.index(fact_rule)
                    self.facts[ind].asserted = True
        elif isinstance(fact_rule, Rule):
            if fact_rule not in self.rules:
                self.rules.append(fact_rule)
                for fact in self.facts:
                    self.ie.fc_infer(fact, fact_rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.rules.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.rules[ind].supported_by.append(f)
                else:
                    ind = self.rules.index(fact_rule)
                    self.rules[ind].asserted = True

    def kb_assert(self, fact_rule):
        """Assert a fact or rule into the KB

        Args:
            fact_rule (Fact or Rule): Fact or Rule we're asserting
        """
        printv("Asserting {!r}", 0, verbose, [fact_rule])
        self.kb_add(fact_rule)

    def kb_ask(self, fact):
        """Ask if a fact is in the KB

        Args:
            fact (Fact) - Statement to be asked (will be converted into a Fact)

        Returns:
            listof Bindings|False - list of Bindings if result found, False otherwise
        """
        print("Asking {!r}".format(fact))
        if factq(fact):
            f = Fact(fact.statement)
            bindings_lst = ListOfBindings()
            # ask matched facts
            for fact in self.facts:
                binding = match(f.statement, fact.statement)
                if binding:
                    bindings_lst.add_bindings(binding, [fact])

            return bindings_lst if bindings_lst.list_of_bindings else []

        else:
            print("Invalid ask:", fact.statement)
            return []

    def kb_retract(self, fact_or_rule):
        """Retract a fact from the KB

        Args:
            fact (Fact) - Fact to be retracted

        Returns:
            None
        """
        printv("Retracting {!r}", 0, verbose, [fact_or_rule])
        ####################################################
        # --- if fact_or_rule is a fact ---
        if isinstance(fact_or_rule, Fact):
            if fact_or_rule not in self.facts:
                print("Fact was not found in the KB")
                return
            fr = self._get_fact(fact_or_rule)
            if not fact_or_rule:
                return
        # --- if fact_or_rule is a rule ---
        elif isinstance(fact_or_rule, Rule):
            if fact_or_rule not in self.rules:
                print("Rule was not found in the KB")
                return
            fr = self._get_rule(fact_or_rule)
            if not fact_or_rule: 
                return
        else: 
            print("That wasn't a fact or a rule. :( Try again!")
            return
        
        # --- removing facts ---
        if isinstance(fr, Fact):
            # case 1: fact is asserted and supported --> change its assertion flag
            if fr.asserted == True and len(fr.supported_by) > 0:
                fr.asserted = False
                return
            # case 2: fact is not asserted but is supported --> do nothing
            elif fr.asserted == False and len(fr.supported_by) > 0:
                return
            # case 3: fact is asserted but not supported or fact is not asserted and not supported --> remove it and then delete its dependents
            else:
                self.facts.remove(fr)

        # --- removing rules ---
        elif isinstance(fr, Rule): 
            # case 1: rule is asserted --> do nothing
            if fr.asserted == True: 
                return
            # case 2: rule is supported --> do nothing
            elif len(fr.supported_by) > 0:
                return 
            # case 3: rule is not asserted or is not supported or both --> remove it and delete its dependents
            else:
                self.rules.remove(fr)
                
        # --- dealing with dependents (facts and rules that are supported by fr) ---
        # supported facts
        supported_facts = fr.supports_facts
        for fact in supported_facts:
            for f in fact.supported_by:
                if fact_or_rule in f:
                    self._get_fact(fact).supported_by.remove(f)
            self.kb_retract(fact)
        # supported rules
        supported_rules = fr.supports_rules
        for rule in supported_rules:
            for r in rule.supported_by:
                if fact_or_rule in r:
                    self._get_rule(rule).supported_by.remove(r)
            self.kb_retract(rule)

    # def kb_retract(self, fact_or_rule):
    #     """Retract a fact from the KB

    #     Args:
    #         fact (Fact) - Fact to be retracted

    #     Returns:
    #         None
    #     """
    #     printv("Retracting {!r}", 0, verbose, [fact_or_rule])
    #     ####################################################
    #     # --- fact ---
    #     if isinstance(fact_or_rule, Fact):
    #         if fact_or_rule not in self.facts:
    #             return
    #         fact = self._get_fact(fact_or_rule)
    #         if not fact:
    #             return
    #         self.kb_delete_fact(fact)
    #     # --- rule ---
    #     elif isinstance(fact_or_rule, Rule):
    #         if fact_or_rule not in self.rules:
    #             return
    #         rule = self._get_rule(fact_or_rule)
    #         if not rule: 
    #             return
    #         self.kb_delete_rule(rule)
    #     else: 
    #         print("Not a fact or rule. Try again. :(")
    #         return

    # def kb_delete_fact(self, fact):
    #     if fact.asserted == True and len(fact.supported_by) > 0:
    #         fact.asserted = False
    #         return
    #     elif fact.asserted == False and len(fact.supported_by) > 0:
    #         return 
    #     self.facts.remove(fact)
    #     self.kb_delete_dependents

    # def kb_delete_rule(self, rule):
    #     if rule.asserted == True or len(rule.supported_by) > 0:
    #         return  
    #     self.rules.remove(rule)
    #     self.kb_delete_dependents

    # def kb_delete_dependents(self, fr):
    #     supported_facts = fr.supports_facts
    #     for fact in supported_facts:
    #         facts_list = []
    #         for f in fact.supported_by:
    #             if fr in f:
    #                 fact_list.append(f)
    #         fact = self._get_fact(fact)
    #         fact.supported_by.remove(fact_list[0])
    #         self.kb_retract(fact)
    #     supported_rules = fr.supports_rules
    #     for rule in supported_rules:
    #         rule_list = []
    #         for r in rule.supported_by:
    #             if fr in r:
    #                 rule_list.append(r)
    #         rule = self._get_rule(rule)
    #         rule.supported_by.remove(rule_list[0])
    #         self.kb_retract(rule)


class InferenceEngine(object):
    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing            
        """
        printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            [fact.statement, rule.lhs, rule.rhs])
        ####################################################
        # 2 cases:
        # 1) lhs of rule only has 1 element --> we assert a fact because that one element is all that is needed to assert the fact
        # 2) lhs of rule has more than one element -->  we assert a rule based on the bindings from the first element on the lhs 

        lhs = rule.lhs[0]                                       
        bindings = match(lhs, fact.statement)                  
        if bindings != False:

            # --- inferring a fact (when there is only one statement on the lhs of the rule) ---
            # 1) check the fact against the lhs of rule
            # 2) if there is a match, instantiate rhs of rule
            # 3) assert the resulting fact into kb 
            if len(rule.lhs) == 1: 
                new_statement = instantiate(rule.rhs, bindings)    
                support = [(fact, rule)]                              
                new_fact = Fact(new_statement, support)             
                fact.supports_facts.append(new_fact)               
                rule.supports_facts.append(new_fact)
                kb.kb_assert(new_fact)     
                # print("inferred a new fact. yay!")                         

            # --- inferring rules (more than one statement on the lhs of the rule) ---
            # 1) check the first element of the lhs against the facts in the kb (we already did that above)
            # 2) go through all the remaining elements on the lhs of the rule
            # 3) instantiate the lhs elements
            elif len(rule.lhs) > 1:
                lhs = []                                            
                for l in rule.lhs[1:]:                 
                    lhs.append(instantiate(l, bindings))           
                rhs = instantiate(rule.rhs, bindings)               
                support = [(fact, rule)]                              
                new_rule = Rule([lhs, rhs], support)                      
                fact.supports_rules.append(new_rule)                
                rule.supports_rules.append(new_rule)               
                kb.kb_assert(new_rule)  
                # print("inferred a new rule. yay!")                              




