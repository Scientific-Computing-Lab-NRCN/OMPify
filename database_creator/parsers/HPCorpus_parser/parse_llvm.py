import os
import json
from tqdm import tqdm
from pqdm.processes import pqdm
from joblib import Parallel, delayed
import preprocess
import parse_tools 
import shutil
import tempfile
import logging
from subprocess import Popen, PIPE


logging.basicConfig(filename='llvm.log', format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',datefmt='%d/%m/%Y %H:%M:%S',level=logging.INFO)
logger = logging.getLogger(__name__)


C_TO_IR_COMMAND = "clang -c -emit-llvm -S -g1 -Oz code.c -o code.ll -std=c17 -Xclang -disable-O0-optnone -Wno-narrowing"
CPP_TO_IR_COMMAND = "clang++ -c -emit-llvm -S -g1 -Oz code.c -o code.ll -std=c++17 -Xclang -disable-O0-optnone -Wno-narrowing"
Fortran_TO_IR_COMMAND = "flang" # not working

Code2IR = {
    "c": C_TO_IR_COMMAND,
    "cpp": CPP_TO_IR_COMMAND,
    "fortran": Fortran_TO_IR_COMMAND
}




class LLVMParser:
    def __init__(self, data_dir, save_dir, lang='c'):
        self.data_dir = data_dir
        self.save_dir = save_dir
        self.lang = lang

    def get_mem_usage(self, code):
        '''
        get the memory usage of a file containing @param:code
        '''
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = temp_file.name

            temp_file.write(bytes(code, 'utf-8'))
            temp_file.flush()

            mem_usage = os.path.getsize(file_path)

        return mem_usage

    def get_llvm_ir(self, code, lang):
        pass

    def convert_llvm(self, save_dir, lang='c'):
        '''
        Execute the clang compiler and save the intermediate representation
        '''
        os.chdir(save_dir)
        p = Popen(Code2IR[lang], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        _, error = p.communicate()

        if error:
            logger.error(f'{save_dir} error:\n{error}')
        else:
            logger.info(save_dir)

    def parse(self, repo, file, func_name, code):
        '''
        Remove irrelevant parts of code (comments and includes) and then parse it
        '''
        code = preprocess.remove_comments(code)
        code = preprocess.remove_headers(code)
        code = preprocess.add_headers(code, lang='c')

        save_dir = os.path.join(self.save_dir, repo, file, func_name)

        try:
            self.save(save_dir, code)
            self.convert_llvm(save_dir)
        except Exception as e:
            # shutil.rmtree(save_dir)
            logger.error(f'file at {save_dir} failed to parse\nerror: {e}')
    
    def iterate_corpus(self):
        '''
        Iterate over the HPCorpus and for each function save the following representations:
            1. username
            2. repo name
            3. path to file
            4. function name
            5. original code
            6. LLVM IR
            7. codes SHA-256
            8. memory usage 

            ---  AST - can be used to produce replaced-tokens, DFG, etc. (will be generated at training time)
        '''
        def parse_json(json_file, lang='c'): 
            dataset = []

            # read json and create process the data
            with open(os.path.join(self.data_dir, json_file), 'r') as f:
                for line in f:
                    js = json.loads(line.strip())

                    if 'content' not in js:
                        continue

                    repo = js['repo_name'].split('/')
                    file = js['path']

                    funcs = preprocess.extract_code_struct(js['content'])
                    print([a for a,b in funcs])

                    for curr_idx, func in enumerate(funcs):
                        func_name, func_code = func
                        logger.info(f'parse function {func_name} at {repo} - {file}')

                        # append all function declaration into the current function code
                        code = ''
                        for _, other_func in funcs[:curr_idx]+funcs[curr_idx+1:]:
                            code += preprocess.get_func_declaration(other_func) + '\n'
                        code += func_code

                        mem_usage = self.get_mem_usage(func_code)
                        llvm = self.get_llvm_ir(code, lang)

                        dataset.append({'username': repo[0],
                                        'repo': repo[1],
                                        'path': file,
                                        'function': func_name,
                                        'code': func_code,
                                        'llvm': None,
                                        'hash': preprocess.get_hash(func_code),
                                        'memory': mem_usage
                        })
                    break

            # write the dataset into json
            with open(os.path.join(self.save_dir, json_file), 'w') as data_f:
                for sample in dataset:
                    data_f.write(json.dumps(sample) + '\n')

        # parallel
        # pqdm(os.listdir(self.data_dir), parse_json, n_jobs=1)

        # sequential
        for json_file in tqdm(os.listdir(self.data_dir)):
            parse_json(json_file)


# parser = LLVMParser('/home/talkad/shared/nadavsc/c', '/home/talkad/LIGHTBITS_SHARE/studies/llvm/c')
# parser = LLVMParser('/home/talkad/shared/nadavsc/c', '/home/talkad/Downloads/thesis/data_gathering_script/database_creator/asd/c_llvm')
parser = LLVMParser('/home/talkad/OpenMPdb/tokenizer/HPCorpus', '/home/talkad/OpenMPdb/database_creator/asd')


parser.iterate_corpus()
