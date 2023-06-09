from optparse import OptionParser
from git_clone import loader, extractor
from parsers import cParser, cppParser, cbeParser, cParser # fortranParser
# from visualization import visualization
from datetime import datetime
import os
import json


def load_repos(script_path, dates_str, repos_dir):
    '''
    Load github repositories in a given range of dates
    '''
    dates_list = dates_str.split('..')
    
    if len(dates_list) != 2:
        print('load failed: wrong date format')
        return

    try:
        dates = list(map(lambda date_str: datetime.strptime(date_str, '%d-%m-%Y').date(), dates_list))
    except:
        print('load failed: wrong date format')
        return

    loader.load(script_path, start_date=dates[0], end_date=dates[1])
    extractor.scan_dir(repos_dir)


def show_stats(omp_dir):
    '''
    show omp statistics
    '''
    pass
    # visualization.show_stats(omp_dir)


def parse(omp_dir, prog_lang):
    '''
    parse code into AST
    '''
    assert prog_lang.startswith('(') and prog_lang.endswith(')')

    save_dir = '/home/talkad/LIGHTBITS_SHARE'

    for lang in prog_lang[1:][:-1].lower().split('|'):
        if lang == 'c':
            # parser = cbeParser.CBELoopParser(omp_dir, os.path.join(save_dir, 'cbe_loops'))
            # parser = cParser.CLoopParser(omp_dir, os.path.join(save_dir, 'c_loops'))
            print(omp_dir)
            parser = cParser.CLoopParser(omp_dir, os.path.join(save_dir, 'temp'))

        elif lang == 'cpp':
            parser = cppParser.CppLoopParser(omp_dir, os.path.join(save_dir, 'example'))
        elif lang == 'fortran':
            continue
            # parser = fortranParser.FortranLoopParser(omp_dir, os.path.join(save_dir, 'fortran_loops'))
        else: 
            continue

        parser.scan_dir()


def main():
    # load environment variables
    with open('ENV.json', 'r') as f:
        vars = json.loads(f.read())

    # define UI
    parser = OptionParser(usage="usage: python %prog [options]",
                          version="%prog 1.0")
    parser.add_option("-l", "--load",
                      dest="dates",
                      help="load omp repositories from github in range of dates [dd-MM-yyyy]. example -l 1-1-2012..31-12-2022")
    parser.add_option("-s", "--stats",
                      action="store_true",
                      default=False,
                      help="show statistical usage of openMP")                     
    parser.add_option("-p", "--parse",
                      dest="prog_lang",
                      help="parse the given programming languages. example: -p \"(c|cpp)\"")
    (options, args) = parser.parse_args()

    if options.dates is not None:
        load_repos(vars['SCRIPT_PATH'], options.dates, vars['REPOS_DIR'])
    
    if options.stats:
        show_stats(vars['REPOS_OMP_DIR'])
        
    if options.prog_lang is not None:
        parse(vars['REPOS_OMP_DIR'], options.prog_lang)


if __name__ == '__main__':
    main()


        