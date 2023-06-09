import re
import code_tokenize as ctok
# from fortranformat import FortranFormat as ftok
import sys
import json
import os
from typing import List
from transformers import AutoTokenizer
from transformers import GPT2Tokenizer
from abc import ABC, abstractmethod

# sys.path.extend(['.','/home/talkad/Downloads/thesis/data_gathering_script/database_creator/parsers/HPCorpus_parser'])
sys.path.extend(['.','/home/talkad/OpenMPdb/database_creator/parsers/HPCorpus_parser'])

import parse_tools, preprocess
import convert_representation as cr
from convert_representation import code2xsbt, code2dfg, code2ast



class Tokenizer(ABC):

    @abstractmethod
    def tokenize(self, s: str, replaced: bool = False, lang: str = 'c') -> List[str]:
        '''
            convert string into sequence tokens

            Parameters:
                s: str -  input string to be tokenized
            Result:
                convert string into list of tokens
        '''
        pass

    @abstractmethod
    def encode(self, s: str) ->  List[int]:
        '''
            encode given string to ids

            Parameters:
                s: String - input string to be tokenized

            Result:
                list of token ids
        '''
        pass

    @abstractmethod
    def decode(self, t: List[int]) -> str:
        '''
            decode token ids to string

            Parameters:
                t: List[int] -  list of tokens ids

            Results:
                string represents the list of ids

        '''
        pass


class Tokompiler(Tokenizer):
    '''
        Compiler oriented tokenization
    '''
    def tokenize(self, s: str, replaced: bool = False, lang: str = 'c') -> List[str]:
        if len(s.strip()) == 0:
            return []

        # if replaced:
        #     s = cr.generate_replaced(s, num_generator=cr.generate_random_numbers, lang=lang)
        if lang == 'fortran':
            tokens = s.split()   # not the best solution, but sufficient one     
        else:
            tokens = ctok.tokenize(s, lang=lang, syntax_error="ignore")

        updated_tokens = []
        for token in tokens:
            try:
                str_token = token.text.strip()
            except:
                str_token = 'TOKEN'

            if replaced and any([str_token.startswith(prefix) for prefix in cr.replaced_prefixes.values()]):
                updated_tokens += list(str_token.split('_'))
            else:
                updated_tokens.append(str_token)
                                    
        return updated_tokens

    def encode(self, s: str) ->  List[int]:
        return []

    def decode(self, t: List[int]) -> str:
        return ''


class TokenizerBPE(Tokenizer):
    '''
        GPT2 BPE tokenization
    '''
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('NTUYG/DeepSCC-RoBERTa')

    def tokenize(self, s: str, replaced: bool = False, lang: str = 'c') -> List[str]:

        if replaced:
            s = parse_tools.generate_replaced(s, num_generator=parse_tools.generate_random_numbers, lang=lang)

        tokens = self.tokenizer.tokenize(s)
        updated_tokens = []

        for token in tokens:
            if token.startswith('Ċ') or token.startswith('Ġ'):
                updated_token = token[1:]

                if 'Ċ' in updated_token or 'Ġ' in updated_token:
                    continue
            else:
                updated_token = token

            if updated_token:
                updated_tokens.append(updated_token)

        return updated_tokens

    def encode(self, s: str) ->  List[int]:
        return []

    def decode(self, t: List[int]) -> str:
        return ''


class ASTokenizer(Tokenizer):
    '''
        convert AST representation into sequence XSBT
    '''
    def tokenize(self, s: str, replaced: bool = False, lang: str = 'c') -> List[str]:
        ast = code2xsbt(s, lang=lang)
        # ast = code2ast(s, lang=lang)
        ast = ast.split()
        updated_ast = []

        if replaced:
            for node in ast:
                if any([node.startswith(prefix) for prefix in cr.replaced_prefixes.values()]):
                    updated_ast += node.split('_')
                else:
                    updated_ast.append(node)
        else:
            updated_ast = ast

        return updated_ast

    def encode(self, s: str) ->  List[int]:
        return []

    def decode(self, t: List[int]) -> str:
        return ''
    

class DFGTokenizer(Tokenizer):
    '''
        convert DFG representation into sequence of tokens
    '''
    def tokenize(self, s: str, replaced: bool = False, lang: str = 'c') -> List[str]:
        dfg = code2dfg(s, lang=lang)
        updated_dfg = []

        if replaced:
            for cnt in dfg:
                sample = (tuple(cnt[0].split('_')), cnt[1], cnt[2], [tuple(var.split('_')) for var in cnt[3]], cnt[4])
                updated_dfg.append(sample)
        else:
            updated_dfg = dfg

        return updated_dfg

    def encode(self, s: str) ->  List[int]:
        return []

    def decode(self, t: List[int]) -> str:
        return ''
    
