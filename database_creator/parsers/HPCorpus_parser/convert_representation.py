import re
import random
import pycparser
import tempfile
from dfg_parser import extract_dataflow
from ast_parser import generate_statement_xsbt, generate_naive_ast
import parse_tools


RE_NUMBERS = re.compile(r"(?<![_a-zA-Z])\b[0-9]+(?:\.[0-9]+)?(?:f)?\b(?![0-9.-])")
RE_HEXA = re.compile(r"0x[0-9a-fA-F]+")
RE_CHARS = re.compile(r"\'.\'")
RE_STR = re.compile(r"\"(?:\\.|[^\\\"])*\"")
RE_STR_MULTI_LINE = re.compile(r"\"(?:\\.|[^\"\\])*?\"")


VAR, ARR, FUNC, STRUCT, FIELD, TYPE, NUM, CHAR, STR = 1, 2, 3, 4, 5, 6, 7, 8, 9
replaced_prefixes = { VAR: 'var_',
                      ARR: 'arr_',
                      FUNC: 'func_',
                      STRUCT: 'struct_',
                      FIELD: 'field_',
                      TYPE: 'type_',
                      NUM: 'num_',
                      CHAR: 'char_',
                      STR: 'str_'             
                    }



def code2dfg(code, lang='c'):
    '''
    Convert code to DFG
    '''
    _, dfg = extract_dataflow(code, lang=lang)

    return dfg


def code2xsbt(code, lang='c'):
    '''
    Convert code to XSBT (Structured Based Traversal as presented in SPT-Code)
    '''
    tree = parse_tools.parse(code, lang=lang)
    node = tree.root_node
    xsbt_str = generate_statement_xsbt(node, lang)

    return xsbt_str


def code2ast(code, lang='c'):
    '''
    Convert code to AST
    '''
    tree = parse_tools.parse(code, lang=lang)
    node = tree.root_node
    ast = generate_naive_ast(node, lang)

    return ast


def prettify_xsbt(xsbt):
    tokens = xsbt.split()
    updated_xsbt = ''
    ident = 0

    for token in tokens:
        if token.endswith('__'):
            updated_xsbt += '\t'*ident + token + '\n'
            ident += 1
        elif token.startswith('__'):
            ident -= 1
            updated_xsbt += '\t'*ident + token + '\n'
        else:
            updated_xsbt += '\t'*ident + token + '\n'
            
    return updated_xsbt


def prettify_ast(ast):
    tokens = ast.split()
    updated_ast = ''
    ident = 0

    for token in tokens:
        if token.endswith('('):
            updated_ast += '\t'*ident + token + '\n'
            ident += 1
        elif token.startswith(')'):
            ident -= 1
            updated_ast += '\t'*ident + token + '\n'
        else:
            updated_ast += '\t'*ident + token + '\n'
            
    return updated_ast


def create_ast(code):
    '''
    Create AST for c codes using pycparser
    '''
    with tempfile.NamedTemporaryFile(suffix='.c', mode='w+') as tmp:    
        tmp.write(code)
        tmp.seek(0)
        ast = pycparser.parse_file(tmp.name)

    return ast


def count_newlines(code):
    counter = 0

    for letter in code:
        if letter == '\n':
            counter += 1
            continue

        return counter
    
    return counter


def replace_vars(code, var_mapping):
    '''
        Create replaced representation 
    '''
    updated_code = ''
    prev_idx = 0
    offset = count_newlines(code)
    updated_mappings = []
    var_offset = 0

    for old_var, new_var, start, end in var_mapping:
        updated_mappings.append((new_var, old_var, start-offset+var_offset, start-offset+var_offset+len(new_var)))
        var_offset += len(new_var)-len(old_var)
        updated_code += code[prev_idx:start-offset] + new_var
        prev_idx = end - offset

    updated_code += code[prev_idx:]

    return updated_code, updated_mappings


def get_identifiers(node, kind=''):
    '''
        Find identifiers names in code

        Parameters:
            node - declaration node in the AST
            kind - the type of  the sub node
        Return:
            list for each replaced variable kind (variable, array, function)
    '''
    # print(node.type, ':', node.text)
    if node.type == 'identifier':
        return ([],[],[(node.text, node.start_byte, node.end_byte)],[],[],[],[],[]) if kind=='func' else ([],[(node.text, node.start_byte, node.end_byte)],[],[],[],[],[],[]) if kind=='arr' else ([(node.text, node.start_byte, node.end_byte)],[],[],[],[],[],[],[])
    elif node.type == 'field_identifier':
        return ([],[],[],[(node.text, node.start_byte, node.end_byte)],[],[],[],[])
    elif node.type == 'type_identifier':
        return ([],[],[],[],[(node.text, node.start_byte, node.end_byte)],[],[],[])
    elif node.type == 'number_literal':
        return ([],[],[],[],[],[(node.text, node.start_byte, node.end_byte)],[],[])
    elif node.type == 'char_literal':
        return ([],[],[],[],[],[],[(node.text, node.start_byte, node.end_byte)],[])
    elif node.type == 'string_literal':
        return ([],[],[],[],[],[],[],[(node.text, node.start_byte, node.end_byte)])

    vars, arrays, funcs, fields, types, numbers, chars, strings = [], [], [], [], [], [], [], []
    for child in node.children:
        va, ar, fu, fi, ty, nu, ch, st = get_identifiers(child, kind=('arr' if child.type == 'array_declarator' else
                                                  'func' if child.type in ['call_expression', 'function_declarator'] else
                                                  '' if child.type in ['parameter_declaration', 'argument_list', 'field_expression', 'parameter_list', 'compound_statement'] else
                                                  'field' if child.type == 'field_identifier' else
                                                   kind if len(kind)>0 else  ''))

        vars, arrays, funcs, fields, types, numbers, chars, strings = vars+va, arrays+ar, funcs+fu, fields+fi, types+ty, numbers+nu, chars+ch, strings+st

    return vars, arrays, funcs, fields, types, numbers, chars, strings


def generate_serial_numbers(N):
    numbers = list(range(N))
    random.shuffle(numbers)

    return numbers


def generate_random_numbers(N):
    max_num = 1000

    if N > max_num:
        raise ValueError(f'N cannot be larger than {max_num}.')

    numbers = random.sample(range(max_num+1), N)

    return numbers


def replace_constants(code, replace_token, regex):
    '''
        Replace constatns in code with a given token

        Parameters:
            code - the original code to be updated
            replace_token - the token that will replace the constants
            regex - the regular expression that captures the constants
    '''
    matches = regex.finditer(code)

    offset = 0
    for match in matches:
        start = match.start() + offset
        end = match.end() + offset
        code = code[:start] + replace_token + code[end:]
        offset += len(replace_token) - len(match.group())

    return code


def update_var_names(ast, num_generator):
    name_map = {}
    vars, arrays, functions, fields, types, numbers, chars, strings = get_identifiers(ast)

    for type, identifiers in zip([VAR, ARR, FUNC, FIELD, TYPE, NUM, CHAR, STR], [vars, arrays, functions, fields, types, numbers, chars, strings]):
        unique_vars= list(set([var[0] for var in identifiers]))
        random_numbers_vars = num_generator(len(unique_vars))

        for var, num in zip(unique_vars, random_numbers_vars):
            name_map[var] = f'{replaced_prefixes[type]}{num}'

    # replace and sort the vars according to their location
    vs = fields+vars+arrays+functions+types+numbers+chars+strings

    vs.sort(key=lambda tup: tup[1])
    var_mapping = [(var.decode(), name_map[var], start, end) for var, start, end in vs]
    
    updated_code, updated_mappings = replace_vars(ast.text.decode(), var_mapping)

    return updated_code


def generate_replaced(code, num_generator=generate_random_numbers, lang='c'):
    '''
        Main funtion to create the replaced represrntation
    '''
    tree = parse_tools.parse(code.lstrip(), lang=lang)
    updated_code = ''

    try:
        updated_code = update_var_names(tree.root_node, num_generator)
    except ValueError as e: # N cannot be larger than 1000.
        print(e)

    return updated_code


