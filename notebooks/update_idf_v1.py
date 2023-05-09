import subprocess
from pathlib import Path
import glob
import os 
import string
import shutil
import math

def chunker_list(seq, size):
    return (seq[i::size] for i in range(size))

def chunk_into_n(lst, n):
    chunks = chunker_list(lst,n)
    return [list(c) for c in chunks]
#   size = math.ceil(len(lst) / n)
#   return list(
#     map(lambda x: lst[x * size:x * size + size],
#     list(range(n)))
#   )

def get_updater_dir(eplus_dir = r"C:\EnergyPlusV22-2-0"):
    return os.path.join(eplus_dir,'PreProcess','IDFVersionUpdater')

def get_updater_dict():
    return  {'V7-2-0':'Transition-V7-2-0-to-V8-0-0.exe',
                'V8-0-0':'Transition-V8-0-0-to-V8-1-0.exe',
                'V8-1-0':'Transition-V8-1-0-to-V8-2-0.exe',
                'V8-2-0':'Transition-V8-2-0-to-V8-3-0.exe',
                'V8-3-0':'Transition-V8-3-0-to-V8-4-0.exe',
                'V8-4-0':'Transition-V8-4-0-to-V8-5-0.exe',
                'V8-5-0':'Transition-V8-5-0-to-V8-6-0.exe',
                'V8-6-0':'Transition-V8-6-0-to-V8-7-0.exe',
                'V8-7-0':'Transition-V8-7-0-to-V8-8-0.exe',
                'V8-8-0':'Transition-V8-8-0-to-V8-9-0.exe',
                'V8-9-0':'Transition-V8-9-0-to-V9-0-0.exe',
                'V9-0-0':'Transition-V9-0-0-to-V9-1-0.exe',
                'V9-1-0':'Transition-V9-1-0-to-V9-2-0.exe',
                'V9-2-0':'Transition-V9-2-0-to-V9-3-0.exe',
                'V9-3-0':'Transition-V9-3-0-to-V9-4-0.exe',
                'V9-4-0':'Transition-V9-4-0-to-V9-5-0.exe',
                'V9-5-0':'Transition-V9-5-0-to-V9-6-0.exe',
                'V9-6-0':'Transition-V9-6-0-to-V22-1-0.exe',
                'V22-1-0':'Transition-V22-1-0-to-V22-2-0.exe',
                'V22-2-0':'None'}
    
def format_eplus_version(version):

    delims = [c for c in version if c in string.punctuation]
    for delim in delims:
        version = version.replace(delim,"-")
        version = version.replace("V","")
    return "V" + version
    
def detect_version(app_string):
    app_name = app_string.split(os.sep)[-1].split(".")[0]
    version = app_name.split("-to-")[-1]
    return app_name, version

def run_updater(updater_dir, transition_cmd, input_idf):
    """
    TRANSITION_CLI_DIR = Path(r'C:\EnergyPlusV22-2-0\PreProcess\IDFVersionUpdater')
    transition_exe = TRANSITION_CLI_DIR / 'Transition-V7-2-0-to-V22-2-0'
    subprocess.check_output([transition_exe, idf_file], cwd=TRANSITION_CLI_DIR)
    """
    transition_exe = Path(updater_dir) / transition_cmd
    subprocess.call([transition_exe, input_idf], cwd=updater_dir)
    
    return detect_version(transition_cmd)[1]

def wrap_updater(updater_dir, updater_dict, src_version, trgt_version, input_idf):
    src_list = list(updater_dict.keys())
    iterate_list = src_list[src_list.index(src_version):src_list.index(trgt_version)]
    for list_src_version in iterate_list:
        run_updater(updater_dir, updater_dict[list_src_version], input_idf)


def run_cz_conversion(input_tuple):  
    bldg_group, cz, run_bool = input_tuple
    project_root = r"C:\Users\Justin\Documents\GitHub\cmip6_and_buildings"
    bldg_group_dir = os.path.join(project_root, 'eplus_simulations', bldg_group)
    cz_dir = glob.glob(os.path.join(bldg_group_dir, 'idf_files', 'v7_2', f'*{cz}_*'))[0]
    
    src_version = "V7-2-0"
    trgt_version = "V22-2-0"
    updater_dict = get_updater_dict()
    updater_dir = get_updater_dir()
    
    dest_dir = os.path.join(bldg_group_dir,'idf_files','v22_2',f'{cz}_{bldg_group}_v22_2')
    temp_dir = os.path.join(bldg_group_dir,'idf_files','v7_2', f'temp_{cz}')
            
    idf_files = glob.glob(os.path.join(cz_dir,"*.idf"))
    missing_files = []
    for idf_fpath in idf_files:
        
        idf_fname = idf_fpath.split(os.sep)[-1].replace("v1.4_7.2",trgt_version)
        print(f"     -{idf_fname}")
        temp_file = os.path.join(temp_dir, idf_fname)
        if os.path.exists(temp_file):
            pass
        else:
            dest_file = os.path.join(dest_dir, idf_fname)
            if os.path.exists(dest_file):
                pass
            else:
                missing_files.append(dest_file)
                for new_dir in [dest_dir, temp_dir]:
                    if os.path.exists(new_dir):
                        pass
                    else:
                        os.mkdir(new_dir)
                if run_bool == True:
                    # copy to temp
                    shutil.copy(idf_fpath, temp_file)
                    
                    # run updater
                    wrap_updater(updater_dir, updater_dict, src_version, trgt_version, temp_file)

                    # move temp to final destination and rename
                    shutil.copy(temp_file, dest_file)
                    
                    # delete temp contents
                    shutil.rmtree(temp_dir, ignore_errors=False, onerror=None)
    return missing_files
            
def run_cz_conversion_patch(chunk):
    run_files = []
    for input_tuple in chunk:
        run_bool, idf_fpath, temp_dir, dest_dir = input_tuple
        src_version = "V7-2-0"
        trgt_version = "V22-2-0"
        updater_dict = get_updater_dict()
        updater_dir = get_updater_dir()
        
        idf_fname = idf_fpath.split(os.sep)[-1].replace("v1.4_7.2",trgt_version)
        print(f"     -{idf_fname}")
        temp_file = os.path.join(temp_dir, idf_fname)
        if os.path.exists(temp_file):
            
            pass
        else:
            dest_file = os.path.join(dest_dir, idf_fname)
            if os.path.exists(dest_file):
                

                pass
            else:
                for new_dir in [dest_dir, temp_dir]:
                    if os.path.exists(new_dir):
                        pass
                    else:
                        os.mkdir(new_dir)
                if run_bool == True:
                    # copy to temp
                    shutil.copy(idf_fpath, temp_file)
                    
                    # run updater
                    wrap_updater(updater_dir, updater_dict, src_version, trgt_version, temp_file)

                    # move temp to final destination and rename
                    shutil.copy(temp_file, dest_file)
                    
                    # delete temp contents
                    shutil.rmtree(temp_dir, ignore_errors=False, onerror=None)
                    
                run_files.append(idf_fpath)
    return run_files