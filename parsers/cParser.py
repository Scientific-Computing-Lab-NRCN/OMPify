import os
import pycparser
from parser import Parser
from pycparser.c_ast import For
import pickle
from visitors import *
from functools import reduce
from fake_headers import fake
import re
import tempfile


class CLoopParser(Parser):
    def __init__(self, repo_path, parsed_path):
        super().__init__(repo_path, parsed_path, ['.c', '.h'])

    def join_funcDecl(self, code):
        '''
        Several c files define the function return type in separate line. For instance:
            int
            check_omp_lock (FILE * logFile) {...}
        pycparser fail to process this files. So we join this lines to proper func. declaration.
        '''
        return_types = ['char', 'short', 'int', 'long', 'float', 'double']

        return reduce(lambda acc, cur: f'{acc}\n{cur}' if cur.lstrip() in return_types else f'{acc} {cur}\n', code.split('\n'))

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

    def parse(self, file_path, code_buf):
        repo_name = file_path[len(self.repo_path + self.root_dir) + 2:]
        repo_name = repo_name[:repo_name.find('/') ]
        cpp_args = ['-nostdinc', '-w', '-E', r'-I' + os.path.join(self.root_dir, 'fake_headers', 'utils')]

        _, headers, _ = fake.get_headers(fake.REPOS_DIR, repo_name)
        for header in list(headers)[:150]:
            cpp_args.append(r'-I' + os.path.join(fake.REPOS_DIR, repo_name, header))

        try:
            return pycparser.parse_file(file_path, use_cpp=True, cpp_path='mpicc', cpp_args = cpp_args)
        except pycparser.plyparser.ParseError as e:  
            with open('error_logger.txt', 'a') as f:
                f.write(f'Parser Error: {file_path} ->\n {e}\n\n')
            print(f'{e}')
            return
        except Exception as e:  
            # print(f'Unexpected Error: {file_path} ->\n {e}')
            return

    def parse_file(self, root_dir, file_name, exclusions):
        '''
        Parse the given file into ast and extract to loops associated with omp pargma (or without)
        '''
        pos, neg = 0, 0
        file_path = os.path.join(root_dir, file_name)
        save_dir = os.path.join(self.parsed_path, root_dir[self.split_idx: ])
        name = os.path.splitext(file_name)[0]

        pfv = PragmaForVisitor()
        verify_loops = ForLoopChecker()
        func_call_checker = FuncCallChecker()

        with open(file_path, 'r+') as f:
            
            try:
                code = f.read()
            except UnicodeDecodeError:
                return 0, 0, False

            ast = self.parse(file_path, code)

            if ast is None:                 # file parsing failed
                return 0, 0, False

            pfv.visit(ast)
            pragmas = pfv.pragmas + len(pfv.neg_nodes) * [None]
            nodes = pfv.pos_nodes + pfv.neg_nodes

            for idx, (pragma, loop) in enumerate(zip(pragmas, nodes)):
                verify_loops.reset()
                func_call_checker.reset()

                verify_loops.visit(loop)
                if verify_loops.found:  # undesired tokens found
                    exclusions['bad_case'] += 1
                    continue

                code = str(loop)
                if code in self.memory:
                    exclusions['duplicates'] += 1
                    continue

                if self.is_empty_loop(loop):
                    exclusions['empty'] += 1
                    continue

                func_call_checker.visit(loop)
                if func_call_checker.found:
                    exclusions['func_calls'] += 1
                                   
                self.create_directory(save_dir) 
                self.memory.append(code)

                generator = pycparser.c_generator.CGenerator()
                self.save(os.path.join(save_dir, f"{name}{'_neg_' if pragma is None else '_pos_'}{idx}.pickle"), pragma, loop, generator.visit(loop))

                if pragma is None:
                    neg += 1
                else:
                    pos += 1

            return pos, neg, True

    def scan_dir(self):
        total_files, num_failed = 0, 0
        total_pos, total_neg = 0, 0
        omp_repo = os.path.join(self.root_dir, self.repo_path)
        exclusions = {'bad_case': 0, 'empty': 0, 'duplicates': 0, 'func_calls':0}

        # iterate over repos
        for idx, repo_name in enumerate(os.listdir(omp_repo)):
            # print('repo ', repo_name)
            fake.remove_utils()
            fake.create_fake_headers(repo_name)
            fake.create_not_exists_headers(omp_repo, repo_name)

            for root, dirs, files in os.walk(os.path.join(omp_repo, repo_name)):
                for file_name in files:
                    ext = os.path.splitext(file_name)[1].lower()
                    
                    if ext in self.file_extensions:
                        pos, neg, is_parsed = self.parse_file(root, file_name, exclusions)

                        if pos is not None:
                            total_pos += pos
                            total_neg += neg

                        if not is_parsed:
                            num_failed += 1
                        total_files += 1

            if idx % (10) == 0:
                with open('success_logger.txt', 'a') as f:
                    f.write("{:20}{:10}   |   {:20} {:10}\n\n".format("files processed: ", total_files, "failed to parse: ", num_failed))
                print("{:20}{:10}   |   {:20} {:10}".format("files processed: ", total_files, "failed to parse: ", num_failed))
                print("{:20}{:10}   |   {:20} {:10}".format("pos examples: ", total_pos, "neg examples: ", total_neg))
                print(f'exclusions: {exclusions}\n')

        return total_pos, total_neg, exclusions, total_files, num_failed


# parser = CLoopParser('../repositories_openMP', '../c_loops')
parser = CLoopParser('../asd', 'c_loops2')

# data = parser.load('/home/talkad/Downloads/thesis/data_gathering_script/c_parser/c_loops2/123/threadGauss_pos_0.pickle')
# ast = data.loop
# print(f'pragma: {data.omp_pragma}')
# print('code:\n')
# ast.show()

total = parser.scan_dir()
print(total)

# (5176, 6829, {'bad_case': 1988, 'empty': 131, 'duplicates': 53288, 'func_calls': 5907}, 21814, 10042)
