import os
import pycparser
from parsers.parser import *
from pycparser.c_ast import For
import pickle
from parsers.visitors.visitors import *
from parsers.visitors.detailed_visitor import *
from functools import reduce
from parsers.fake_headers import fake
from parsers.parsing_utils import utils
import re
import json
from multiprocessing import Process, Manager
import tempfile
import shutil


dest_folder = 'temp_folder'


def handle_error(file_path, err, code):
    '''
    Extracts from a given error message the undefined type
    '''
    err_pattern = {'*': r'(\w+)\W*$',
                   '=': r'^\W*(\w+)'}

    match = re.search(r'.*:(\d+):(\d+): before: (.*)', err)
    code_buf = code.split('\n')

    if match is None:
        return
    
    line, pos, param = int(match.group(1)), int(match.group(2)), match.group(3)
    sub_line = code_buf[line-1][: pos-1]
    param = param.strip()

    code_segment = "\n".join(code_buf[line-2:line+1])
    utils.log('more_errors.txt', f'{file_path}\n{err}\n{code_segment}\n =========================\n')

    if param in err_pattern:
        match = re.search(err_pattern[param], sub_line)

        if match is not None:
            return match.group(1)

        
class CLoopParser(Parser):
    def __init__(self, repo_path, parsed_path):
        super().__init__(repo_path, parsed_path, ['.c'])

    def save(self, file_path, sample):
        self.id2path[self.data_indexer] = file_path
        self.data_indexer += 1

        with open(os.path.join(file_path, 'metadata.pkl'), 'wb') as f:
            pickle.dump(sample, f)

        with open(os.path.join(file_path, 'code.c'), 'w') as f:
            f.write(str(sample))

        if len(sample.pragma) > 0:
            with open(os.path.join(file_path, 'pragma.c'), 'w') as f:
                f.write(sample.pragma)


    def load(self, file_path):

        with open(os.path.join(file_path, 'metadata.pkl'), 'rb') as f:
            sample = pickle.load(f)

        return sample


    def is_empty_loop(self, node):
        '''
        precondition - node is a For struct
        '''
        children = dict(node.children())

        try:
            # if there is no 'block_items' attribute than it's another compound struct
            temp = children['stmt'].block_items
        except:
            return False

        if children['stmt'].block_items is None:
            return True
        elif all(type(child) is For for child in children['stmt'].block_items):
             # return true if one of the for loops is empty
            return any(self.is_empty_loop(child) for child in children['stmt'].block_items)
        else:
            return False


    def create_ast(self, file_path, code, result):
        with open('ENV.json', 'r') as f:
            vars = json.loads(f.read())

        repo_name = file_path[len(self.repo_path) + 2:]
        repo_name = repo_name[:repo_name.find('/') ]
        cpp_args = ['-nostdinc', '-w', '-E', r'-I' + vars["FAKE_DIR"]]
        _, headers, _ = fake.get_headers(vars['REPOS_DIR'], repo_name)

        if os.path.exists(dest_folder):
            shutil.rmtree(dest_folder)

        # create empty headers
        os.makedirs(dest_folder)
        fake.create_empty_headers(file_path, dest_folder)
        cpp_args.append(r'-I' + dest_folder)

        for header in list(headers)[:50]:
            cpp_args.append(r'-I' + os.path.join(vars['REPOS_DIR'], repo_name, header))
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.c', mode='w+') as tmp:    
                tmp.write(code)
                tmp.seek(0)
                ast = pycparser.parse_file(tmp.name, use_cpp=True, cpp_path='mpicc', cpp_args = cpp_args)
                result['ast'] = ast

                print(ast)

        except pycparser.plyparser.ParseError as e:  
            # utils.log('error_logger.txt', f'Parser Error: {file_path} ->\n {e}\n')
            handle_error(file_path, str(e), code)

        except Exception as e:
            # utils.log('error_logger.txt', f'Unexpected Error: {file_path} ->\n {e}\n')
            pass

        finally:
            shutil.rmtree(dest_folder)

    def parse(self, file_path, code_buf):
        manager = Manager()
        return_dict = manager.dict()
        t = Process(target=self.create_ast, args=(file_path, code_buf, return_dict), daemon=True)

        t.start()
        t.join(120.0)

        if t.is_alive():
            t.terminate()
            try:
                shutil.rmtree(dest_folder)
            except:
                return
        elif 'ast' in return_dict:
            # print(return_dict['ast'])
            return return_dict['ast']
        
    def parse_file(self, root_dir, file_name, exclusions):
        '''
        Parse the given file into ast and extract the loops associated with omp pargma (or without)
        '''
        indexer = 0
        pos, neg = 0, 0
        pragma_found = 0
        count_no_pragma = 0
        error = 'missing pragmas'

        file_path = os.path.join(root_dir, file_name)
        log('files.txt', file_path)
        _, pragma_amount = utils.count_for(file_path)
        save_dir = os.path.join(self.parsed_path, root_dir[self.split_idx: ])
        name = os.path.splitext(file_name)[0]

        func_extractor = FunctionExtractor()
        verify_loops = ForLoopChecker()

        # ### DEBUG ###
        # exist_samples = []
        # for dir_path, dir_names, file_names in os.walk('/home/talkad/LIGHTBITS_SHARE/c_loops_detailed'):
        #     if not dir_names:
        #         path = dir_path[len('/home/talkad/LIGHTBITS_SHARE/c_loops_detailed/'):]
        #         path = path[:path.rfind('/')]
        #         exist_samples.append(path)

        # # print(exist_samples)
        # ### DEBUG ###

        with open(file_path, 'r+') as f:
        #     ### DEBUG ###
        #     if any([path in file_path for path in exist_samples]):
        #         utils.log("skipped.txt", f'{file_path}\n')
        #         return 0, 0, False
        #     ### DEBUG ###

            try:
                code = f.read()
            except UnicodeDecodeError:
                utils.log("fail_pragma.txt", f'{file_path}\nUnicodeDecodeError\nfound {pragma_found} | there are {pragma_amount}\n===================')
                return 0, 0, False
            
            code = utils.update_code_pipline(code)    # remove unparsable code
            # asts = list(map(lambda code_permutation: self.parse(file_path, code_permutation), utils.get_if_permutations(code)))
            asts = [self.parse(file_path, code)]

            for copy_idx, ast in enumerate(asts):
                if ast is None:                 # file parsing failed
                    error = 'failed to parse'
                    continue
                
                functions = func_extractor.extract(ast)
                extractor = LoopExtractor(functions)

                for func_name, function in functions.items():

                    extractor.reset()
                    samples = extractor.extract(func_name, function)

                    for sample in samples:
                        verify_loops.reset()

                        generator = pycparser.c_generator.CGenerator()

                        try:
                            code = generator.visit(sample.for_node)
                            verify_loops.visit(sample.for_node)
                        except:
                            continue

                        if code in self.memory and copy_idx > 0 and len(sample.pragma) > 0:
                            pragma_found -= 1
                            continue

                        if verify_loops.found:  # undesired tokens found
                            exclusions['bad_case'] += 1
                            continue

                        if code in self.memory:
                            exclusions['duplicates'] += 1
                            continue

                        if self.is_empty_loop(sample.for_node):
                            exclusions['empty'] += 1
                            continue
                
                        saving_path = os.path.join(save_dir, name, str(indexer))
                        # self.create_directory(saving_path) 
                        # self.memory.append(code)

                        # self.save(saving_path, sample)
                        indexer += 1

                        if len(sample.pragma) == 0:
                            neg += 1
                        else:
                            pos += 1

                if pragma_found < pragma_amount:
                    utils.log("fail_pragma.txt", f'{file_path}\n{error}\nfound {pragma_found} | there are {pragma_amount}\n===================')

            return pos, neg, True


 