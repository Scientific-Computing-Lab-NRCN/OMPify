import matplotlib.pyplot as plt
from collections import Counter
from datetime import date
import pickle


def visualize_keywords(metadata_path):
    '''
    plot pi graph of all keywords

    {'mpi': 487, 'openmp': 1585, 'cuda': 341, 'cpp': 272, 'parallel-computing': 322, 'c': 325, 'parallel-programming': 237, 'hpc': 115, 'openmp-parallelization': 111, 'openmpi': 105, 'parallel': 142}
    {'c-plus-plus': 81, 'mpi': 487, 'openmp': 1585, 'cuda': 341, 'opencl': 81, 'cpp': 272, 'gpu': 74, 'parallel-computing': 322, 'fortran': 57, 'c': 325, 'parallel-programming': 237, 'hpc': 115, 'pthreads': 88, 'openmp-parallelization': 111, 'openmpi': 105, 'multithreading': 95, 'parallel': 142, 'python': 59, 'simd': 51, 'high-performance-computing': 65}
    '''
    keywords = []
    top_keywords = {}

    with open(metadata_path, 'rb') as f:
        data = pickle.load(f)

        for metadata in data:
            keywords += metadata['keywords']

    # return most used keywords
    for k, v in Counter(keywords).items():
        if v > 50 and len(k) > 0:
            top_keywords[k] = v

    return top_keywords


def lastUpdate_info(metadata_path):
    '''
    get last update rate
    (8908, 1436)
    '''
    total, last_update = 0, 0
    UPDATE_THRESHOLD = 6 * 30
    today_date = date.today()

    with open(metadata_path, 'rb') as f:
        data = pickle.load(f)

        for metadata in data:
            total += 1

            if (today_date - metadata['update_date']).days < UPDATE_THRESHOLD:
                last_update += 1

    return total, last_update


def count_lang(metadata_path):
    '''
    get the amount of use of each programming language

    {'C': 3556, 'Python': 164, 'C++': 3442, 'Shell': 157, 'FORTRAN': 40, 'Java': 74, 'JavaScript': 21, 'Cuda': 135, 'Fortran': 204, 'TeX': 69, 'Jupyter Notebook': 132, 'C#': 13, 'Makefile': 66, 'CMake': 40, 'R': 14, 'HTML': 39, 'Assembly': 13, 'Dockerfile': 50}
    '''
    langs = []
    langs_count = {}

    with open(metadata_path, 'rb') as f:
        data = pickle.load(f)

        for metadata in data:
            langs.append(metadata['lang'])

    # return most used keywords
    for k, v in Counter(langs).items():
        if v > 10 and len(k) > 0:
            langs_count[k] = v

    return langs_count


def count_users_info(metadata_path):
    '''
    Get company, location and email countings

    amount of national labs 33
    {'lanl.gov': 10, 'llnl.gov': 6, 'pnnl.gov': 5, 'olcf.ornl.gov': 3, 'bnl.gov': 3, 'sandia.gov': 2, 'mcs.anl.gov': 1, 'usgs.gov': 1, 'fnal.gov': 1, 'ornl.gov': 1}
    ({'Google': 17, 'Carnegie Mellon University': 15, 'Intel': 15, 'NVIDIA': 16, 'Microsoft': 39, 'Amazon': 11}, 
    {'Spain': 20, 'London': 32, 'Germany': 43, 'Boston, MA': 12, 'New York': 27, 'Chicago, IL': 11, 'China': 13, 'Singapore': 26, 'Berlin, Germany': 19, 'Paris, France': 18, 'Tokyo': 13, 'Poland': 29, 'Stockholm': 18, 'Seattle, WA': 20, 'UK': 15, 'Taiwan': 16, 'Beijing, China': 11, 'Santa Clara, CA': 12, 'Pittsburgh, PA': 13, 'Portugal': 12, 'France': 48, 'Berlin': 17, 'San Francisco': 19, 'Japan': 13, 'USA': 24, 'San Francisco, CA': 18, 'London, UK': 18, 'Italy': 31, 'Berkeley, CA': 12, 'Edinburgh, UK': 13, 'Austin, TX': 17, 'Moscow': 32, 'United States': 45, 'Dublin, Ireland': 23, 'Egypt': 15, 'Brazil': 60, 'Bangalore': 29, 'Bangalore, India': 15, 'Hsinchu, Taiwan': 13, 'Moscow, Russia': 31, 'Canada': 17, 'Greece': 29, 'Athens, Greece': 36, 'Barcelona': 23, 'Paris': 27, 'Melbourne': 13, 'Los Angeles': 12, 'India': 61, 'Brasil': 13, 'Bristol, UK': 14, 'Munich, Germany': 12, 'Thessaloniki, Greece': 17, 'New York, NY': 19, 'Israel': 14, 'Hyderabad': 18, 'Hong Kong': 15, 'United Kingdom': 14, 'Hyderabad, India': 15, 'Russia': 29, 'Beijing': 16, 'Dallas, TX': 12, 'United States of America': 18, 'Madrid, Spain': 11, 'Tokyo, Japan': 13, 'Istanbul': 11, 'Redmond, WA': 11, 'Karachi, Pakistan': 11}, 
    {'gmail': 1763, 'protonmail': 17, 'hotmail': 74, 'cs': 12, 'qq': 30, 'intel': 24, 'live': 15, 'outlook': 65, '163': 19, 'mail': 29, 'yahoo': 31, 'googlegroups': 18, 'yandex': 15, 'epcc': 11})
    '''
    national_labs = []
    keywords = []
    companies, locations, emails = [], [], []
    top_companies, top_locations, top_emails = {}, {}, {}

    with open(metadata_path, 'rb') as f:
        data = pickle.load(f)

        for metadata in data:
            companies.append(metadata['company'])
            locations.append(metadata['location'])
            email = '' if metadata['email'] is None else metadata['email']            
            email = email[email.find('@')+1:]
            emails.append(email[:email.find('.')])

            if metadata['email'] is not None and '.gov' in metadata['email']:
                national_labs.append(email)

    for top, count in zip([top_companies, top_locations, top_emails], [Counter(companies), Counter(locations), Counter(emails)]):
        for k, v in count.items():
            if k is not None and v > 10 and len(k) > 0:
                top[k] = v

    print(f'amount of national labs {len(national_labs)}')
    print(national_labs)
    return top_companies, top_locations, top_emails


# print(count_lang('/home/talkad/Downloads/thesis/data_gathering_script/visualization/metadata.pickle'))
print(count_users_info('/home/talkad/Downloads/thesis/data_gathering_script/visualization/metadata_user.pickle'))