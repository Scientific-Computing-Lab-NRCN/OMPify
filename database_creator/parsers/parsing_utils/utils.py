import re
import os
import copy
import json
import csv
import pandas as pd
from tqdm import tqdm
import itertools


redundant_ompts = re.compile("<ompts:testdescription>.*<\/ompts:testdescription>|<ompts:description>.*<\/ompts:description>|<ompts:version>.*<\/ompts:version>|<ompts:ompversion>.*<\/ompts:ompversion>|<ompts:directive>.*<\/ompts:directive>|<ompts:dependences>.*<\/ompts:dependences>|<ompts:.*?>|<\/ompts:.*>")
redundant_directives = re.compile("MAYBE_INLINE|TM_CALLABLE|__block|RESTRICT|__targetConst__|__targetHost__| __ |CC_CACHE_ALIGN")
redundant_includes = re.compile("^\W*#\W*include\W* <\.\..*|^\W*#\W*include\W* \"\.\..*", re.MULTILINE)
redundant_defines = re.compile("^\W*#\W*define\W* INIT().*", re.MULTILINE)
redundant_line_comments = re.compile("\/\/.*")
redundant_multiline_comments = re.compile("\/\*.*?\*\/", re.MULTILINE|re.DOTALL)

if_directive = re.compile("^\W*#\W*if\W(.*)|^\W*#\W*elif\W(.*)", re.MULTILINE)
ifdef_directive = re.compile("^\W*#\W*ifdef\W(.*)|^\W*#\W*ifndef\W(.*)", re.MULTILINE)

err_directive =  re.compile("^\s*#\s*error\s.*$")
extern_directive = re.compile("^\s*extern\s+.*$")


def log(file_name, msg):
    with open(file_name, 'a') as f:
        f.write(f'{msg}\n')


def is_for(line, lang='c'):
    '''
	Return true if the given line is the beggining of for-loop
	'''
    sub_line = line.lstrip() # remove redundant white spaces

    if lang == 'c':
        return sub_line.startswith('for') and sub_line[3:].lstrip().startswith('(')

    return sub_line.startswith('do ')


def is_for_pragma(line, lang='c'):
    '''
    Return true if the given line is for-pragma
    '''
    sub_line = line.lstrip() # remove redundant white spaces

    if lang == 'c':
        return sub_line.startswith('#pragma ') and ' omp ' in line and ' for' in line

    return sub_line.startswith('!$omp ') and ' do' in line and ' end' not in line


def count_for(file_path, lang='c'):
    '''
    Returns the amout of for-loops and pragmas exist in a given file
    '''
    loop_amount, pragma_amount = 0, 0

    with open(file_path, 'r') as f:
        try:
            code = f.read()
        except UnicodeDecodeError:
            return 0

        code = redundant_line_comments.sub("\n", code)
        code = redundant_multiline_comments.sub("\n", code)

        for line in code.split('\n'):
            l = line.lower()
			
            if is_for(l, lang=lang):
                loop_amount += 1

            if is_for_pragma(l, lang=lang):
                pragma_amount += 1

    return loop_amount, pragma_amount



def count_for_code(code, lang='c'):
    '''
    Returns the amout of for-loops and pragmas exist in a given file
    '''
    loop_amount, pragma_amount = 0, 0

    code = redundant_line_comments.sub("\n", code)
    code = redundant_multiline_comments.sub("\n", code)

    for line in code.split('\n'):
        l = line.lower()
        
        if is_for(l, lang=lang):
            loop_amount += 1

        if is_for_pragma(l, lang=lang):
                pragma_amount += 1

    return loop_amount, pragma_amount


def remove_redundants(code):
    '''
    remove lines containing namespace or #error
    '''
    code_buf = []

    for line in code.split('\n'):
        l = line.lower().split()

        if (len(l) > 2 and l[0] == 'using' and l[1] == 'namespace') or \
        line.lstrip().startswith('#error'):
            continue

        code_buf.append(line)

    return '\n'.join(code_buf)


def remove_paren(code):
    flag = False
    num_paren = 0
    idx = 0

    for letter in code:
        if flag and num_paren == 0:
            return code[idx: ]

        if letter == '(':
            flag = True
            num_paren += 1
        elif letter == ')':
            num_paren -= 1

        idx += 1

    return ''


def remove_attribute(code):
    splitted_code = re.split('__attribute__|__attribute', code)

    if len(splitted_code) == 1:
        return code

    updated_code = list(map(lambda code: remove_paren(code), splitted_code[1:]))
    return ''.join(list(splitted_code[0]) + updated_code)


def remove_ompt(code):
    '''
    Remove redundant compiler directives
    '''
    code = redundant_includes.sub("", code)
    code = redundant_directives.sub(" ", code)
    code = redundant_defines.sub("\n#define INIT()\n", code)

    return redundant_ompts.sub("", code)


def line_union(code):
    '''
    if the current line of code ends with a comma, concatenate this line with the following
    '''
    code_buf = []

    for line in code.split('\n'):
        if len(code_buf) == 0:
            code_buf.append(line)
        elif code_buf[-1].rstrip().endswith(','):
            code_buf[-1] += line
        else:
            code_buf.append(line)

    return '\n'.join(code_buf)


# def remove_if_directives(code):
#     code_buf = []

#     for line in code.split('\n'):
#         if any([line.lstrip().startswith(token) for token in ['#if', '#ifdef', '#ifndef', '#elif', '#else', '#endif']]):
#             continue
#         else:
#             code_buf.append(line)

#     return '\n'.join(code_buf)


def remove_err_directive(code):
    # code = extern_directive.sub("", code)
    ### SPEC-OMP ###
    code = code.replace("register ", " ")
    code = code.replace("MagickExport ", "")
    code = code.replace("ModuleExport", "")
    code = code.replace("WandExport", "")
    ###
    return err_directive.sub("", code)


def update_code_pipline(code):
    FAKE_TYPEDEFS = '_fake_typedefs.h'
    FAKE_DEFINES = '_fake_defines.h'

    code = remove_redundants(code)
    code = remove_attribute(code)
    code = remove_ompt(code)
    code = remove_err_directive(code)
    code = line_union(code)
    code = f'#include \"{FAKE_TYPEDEFS}\"\n#include \"{FAKE_DEFINES}\"\n{code}'

    return code


def clean_code_patches(code):
    code_buf = []
    pragma_for_func = 'omp_for_pragma_talkad7420'
    pragma_func = 'omp_pragma_talkad7420'
    for_func = 'for_loop_talkad7420'

    for line in code.split('\n'):
        if pragma_for_func in line or pragma_func in line or for_func in line:
            continue

        code_buf.append(line)

    return '\n'.join(code_buf)

def update_code_cbe_pipline(code):
    code = remove_redundants(code)
    code = remove_attribute(code)
    code = remove_ompt(code)
    code = clean_code_patches(code)

    return code


def is_if_directive(line):
	'''
	Returns true if the line is compiler-directive condition
    There are 19879 if-directives
	'''
	sub_line = line.strip().lower()
	return (sub_line.startswith("#if") or sub_line.startswith("#elif") or sub_line.startswith("#ifdef") or sub_line.startswith("#ifndef")) \
            and not sub_line.endswith("\\")


def remove_comment(line):
    '''
    Given a line of code, return a line without a comment (if exists)

    Precondition:
        line is compiler-condition ("#if"...)
    '''
    return redundant_line_comments.sub("", line)


def update_if_directive(line, stat):
    '''
    Return positive/negative form of line (which is a condition) according to stat
    '''
    if stat:
        return line

    match = re.search(if_directive, line)

    if match is not None:
        if '#elif' in line:
            return f'#elif !({remove_comment(match.group(2))})'
        else:
            return f'#if !({remove_comment(match.group(1))})'

    match = re.search(ifdef_directive, line)

    if match is not None:
        if '#ifdef' in line:
            return f'#ifndef {remove_comment(match.group(1))}'
        else:
            return f'#ifdef {remove_comment(match.group(2))}'

    return line


def get_if_permutations(code):
    '''
    for a given code segment return all possible permutations for conditions 
    '''
    limit = 7 # 2**7 = 128 permutations

    code_permutations = []
    code_buf = code.split('\n')
    if_amount = sum(list(map(is_if_directive, code_buf)))

    if if_amount == 0:
        return [code]

    if_idx = list(filter(lambda idx: is_if_directive(code_buf[idx]), range(len(code_buf))))[:limit]
    bool_permutations = [list(i) for i in itertools.product([True, False], repeat=min(if_amount, limit))]
    
    for permutation in bool_permutations:
        code_buf_copy = copy.deepcopy(code_buf)

        for idx, stat in zip(if_idx, permutation):
            code_buf_copy[idx] = update_if_directive(code_buf[idx], stat)

        code_permutations.append("\n".join(code_buf_copy))
    
    return code_permutations






def scan_dir(root_dir):
    neg, pos = 0, 0
	
    for idx, (root, dirs, files) in enumerate(os.walk(root_dir)):
        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
			
            if ext in ['.f90', '.f']:
                amount_loops, amount_pragma = count_for(os.path.join(root, file_name), lang='f')
                pos += amount_pragma
                neg += (amount_loops - amount_pragma)
			
        if idx % (10**3) == 0:
            print(f'total: {idx}')

    return neg, pos


def iterate_csv(csv_file):
    count_samples = 0
    num_loops, num_pragma = 0, 0
    df = pd.read_csv(csv_file)

    for index, row in tqdm(df.iterrows()):
        count_samples += 1
        loop_amount, pragma_amount = count_for_code(row['content'])

        num_loops += loop_amount
        num_pragma += pragma_amount

    print(f'num samples: {count_samples}')
    return num_loops, num_pragma


def iterate_jsons(json_dir):
    count_samples, total = 0, 0
    num_loops, num_pragma = 0, 0
    
    for json_file in tqdm(os.listdir(json_dir)):
        with open(os.path.join(json_dir, json_file), 'r') as f:

            for line in f:
                total += 1
                js = json.loads(line.strip())

                if 'content' not in js:
                    continue

                count_samples += 1
                loop_amount, pragma_amount = count_for_code(js['content'])

                num_loops += loop_amount
                num_pragma += pragma_amount

    print(f'num samples: {count_samples}/{total}')
    return num_loops, num_pragma



def iterate_jsons_cuda(json_dir):
    cuda, total = 0, 0

    for json_file in tqdm(os.listdir(json_dir)):
        with open(os.path.join(json_dir, json_file), 'r') as f:

            for line in f:
                total += 1
                js = json.loads(line.strip())

                if 'content' not in js:
                    continue

                if 'cuda.h' in js['content'] or 'cuda_runtime.h' in js['content']:
                    cuda += 1

    return cuda, total


# res = scan_dir("/home/talkad/Downloads/thesis/data_gathering_script/repositories_openMP")
# print(res)

# c -> (82253, 49888)
# cpp -> (98132, 124656)
# fortran -> (46279, 20833)


print(iterate_jsons('/home/talkad/LIGHTBITS_SHARE/dataset_gal_fortran/f90'))


# print(iterate_jsons('/home/talkad/shared/nadavsc/c'))
# num samples: 4735196/4737762
# (19868390, 89480)

# (28618243, 39459)


# print(iterate_jsons_cuda('/home/talkad/shared/nadavsc/c'))
# print(iterate_jsons_cuda('/home/talkad/LIGHTBITS_SHARE/dataset_gal_cpp/cpp'))
# cpp - (3508, 4737762)
# c - (2091, 5946252)