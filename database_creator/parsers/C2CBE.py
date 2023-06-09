from clang.injector import Injector
from subprocess import Popen, PIPE
import shutil
import glob
import json
import os
from parsing_utils import utils
from fake_headers import fake
from tqdm import tqdm


class C2CBE:
    '''
    Convert c-like codes to llvm-IR and back to C
    '''
    def __init__(self, dir_path, meta_path, langs=['.c', '.h']):
        self.current_dir = os.getcwd()
        self.dir_path = dir_path
        self.langs = langs
        self.injector = Injector()
        self.metadata = self.read_metadata(meta_path)

    def read_metadata(self, meta_path):
        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        return metadata

    def inject_code(self, code):
        code = '#include \"patch.h\"\n' + code
        code = '#include \"_fake_typedefs.h\"\n#include \"_fake_defines.h\"\n' + code
        return self.injector.inject(code)

    def run_script(self, root, repo_name, file_name, stats):
        result = True
        full_path = os.path.join(root, file_name)
        original_path = self.metadata['original_repos'] + full_path[len(self.metadata['temp_dir']): -len(file_name)-1]

        name = file_name[:file_name.rfind('.')]
        cpp_args = ['-w', r'-I' + original_path, r'-I/home/talkad/OpenMPdb/parsers/fake_headers/utils_cbe']

        p = Popen([self.metadata['script_path'], root, ' '.join(cpp_args) , file_name, f'{name}.ll'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        res, err = p.communicate()

        err = err.decode("utf-8")

        if 'error' in err:
            utils.log('cbe_error.txt', f'{full_path}\n{err}\n=========================\n')
            # print(f'===\n{err}\n====')
            result = False
        
        if file_name.endswith('.cpp'):
            stats['total_cpp'] += 1
            if result:
                stats['cpp'] += 1
        else:
            stats['total_c'] += 1
            if result:
                stats['c'] += 1

        return result


    def create_env(self, repo_path, temp_path):
        shutil.copytree(repo_path, temp_path)

        for idx, (root, dirs, files) in enumerate(os.walk(temp_path)):
            for file in files:
                if file[file.rfind('.'):] not in self.langs:
                    os.remove(os.path.join(root, file))

        # copy the header patch into every inner directory
        shutil.copyfile(self.metadata['patch_path'], os.path.join(temp_path, 'patch.h'))
        # for idx, (root, dirs, files) in enumerate(os.walk(temp_path)):
        #     for d in dirs:
        #         onlyfiles = [f for f in os.listdir(os.path.join(root, d)) if os.path.isfile(os.path.join(root, d, f))]

        #         if len(onlyfiles) > 0: 
        #             shutil.copyfile(self.metadata['patch_path'], os.path.join(root, d, 'patch.h'))

    def keep_cbe(self, temp_path):
        shutil.move(temp_path, self.metadata['cbe_dir'])

        # remove unrelevant files
        for idx, (root, dirs, files) in enumerate(os.walk(self.metadata['cbe_dir'])):
            for file in files:
                if not file.endswith('.cbe.c'):
                    os.remove(os.path.join(root, file))

        # remove empty dirs
        for idx, (root, dirs, files) in enumerate(os.walk(self.metadata['cbe_dir'], topdown=False)):
            for d in dirs:
                if len(os.listdir(os.path.join(root, d))) == 0:
                    os.rmdir(os.path.join(root, d))



    def convert2cbe(self, repo_path, repo_name, stats):
        temp_path = os.path.join(self.metadata['temp_dir'], repo_name)

        # create repo env
        self.create_env(repo_path, temp_path)

        for idx, (root, dirs, files) in enumerate(os.walk(temp_path)):
            for file_name in files:

                ext = os.path.splitext(file_name)[1].lower()

                if ext in self.langs:
                    file_path = os.path.join(root, file_name)
                    utils.log('files_cbe.txt', f'{file_path}\n')
                    # print(file_path)

                    loop_amount, pragma_amount = utils.count_for(file_path)

                    with open(file_path, 'r+') as f:
                        original_code = f.read()
                        updated_code = self.inject_code(original_code)
                        f.truncate(0)
                        f.seek(0)
                        f.write(updated_code)

                    # compile
                    res = self.run_script(root, repo_name, file_name, stats)

                    # with open(file_path, 'w') as f:
                    #     f.truncate(0)
                    #     f.seek(0)
                    #     f.write(original_code)

                    if res:
                        stats['for'] += loop_amount
                        stats['pragma'] += pragma_amount

        # keep just the cbe.c files
        self.keep_cbe(temp_path)
        shutil.rmtree(self.metadata['temp_dir'])

    def scan_dir(self):
        idx = 0
        stats = {stat:0 for stat in ['pragma', 'for', 'total_cpp', 'cpp', 'total_c', 'c']}

        # create cbe directory 
        if os.path.exists(self.metadata['cbe_dir']):
            shutil.rmtree(self.metadata['cbe_dir'])
        os.mkdir(self.metadata['cbe_dir'])

        for repo in tqdm(os.listdir(self.dir_path)):
            # print('repo:', repo)
            utils.log('files_cbe.txt', f'\n==========\nRepo: {repo}\n')
            self.convert2cbe(os.path.join(self.dir_path, repo), repo, stats)
            
            idx += 1
            if idx%5 == 0:
                print(stats)

        print(stats)


# cc = C2CBE('/home/talkad/OpenMPdb/asd', '/home/talkad/OpenMPdb/parsers/clang/llvm_metadata.json', langs=['.cpp', '.c'])
cc = C2CBE('/home/talkad/OpenMPdb/repositories_openMP', '/home/talkad/OpenMPdb/parsers/clang/llvm_metadata.json', langs=['.cpp', '.c'])

cc.scan_dir()


# {'pragma': 137027, 'for': 253854, 'total_cpp': 12389, 'cpp': 6761, 'total_c': 19784, 'c': 12795}