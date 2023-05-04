"""multiprocessing runs

using generators instead of a list
when you are running a 100 files you have to use generators"""

import os
import glob
import sys
from eppy.modeleditor import IDF
from eppy.runner.run_functions import runIDFs


def load_idf_list(vintages, project_root):
    all_idf = []
    for vintage in vintages:
        for par_dir in glob.glob(os.path.join(project_root, 'eplus_simulations', vintage, 'idf_files', 'v22_2','*v22_2')):
            idf_files = glob.glob(os.path.join(par_dir,'*.idf'))
            all_idf.append(idf_files)
    
    return [item for sublist in all_idf for item in sublist]

def build_scen_years():
    scenarios = ['historical', 'ssp126', 'ssp245', 'ssp585']
    years = [2020, 2035, 2050, 2065, 2080]

    scen_years = []

    for scenario in scenarios:
        for year in years:
            if scenario == 'historical':
                if year == 2020:
                    scen_years.append((scenario, year))
                else:
                    pass
            else:
                if year == 2020:
                    continue

                scen_years.append((scenario, year))

    return scen_years


def check_dir_create(dir_path):
    if os.path.exists(dir_path):
        pass
    else:
        os.mkdir(dir_path)


def get_year_bands(year, formatted=True):
    if formatted:
        year_bands = f'{year-15}-{year+15}'
    else:
        year_bands = (year-15, year+15)
    return year_bands


def get_epw_name(idf_fname, scenario, year, ptile=50):
    idf_details = decompose_idf_filename(idf_fname)
    project_root = idf_details['project_root']
    cz = idf_details['climate_zone']

    if scenario == 'historical':
        epw_path = glob.glob(os.path.join(
            project_root, 'weather_files', 'tmy3', f'{cz}*.epw'))[0]
    else:
        year_bands = get_year_bands(year, formatted=True)
        epw_path = os.path.join(project_root, 'weather_files', 'morphed',
                                cz, scenario, 'EPWs', f'{scenario}_{ptile}_{year_bands}.epw')
    return epw_path


def decompose_idf_filename(idf_file):
    sim_dir_split = idf_file.split("eplus_simulations")
    file_segments = sim_dir_split[1].split(os.sep)
    idf_segments = file_segments[-1].split("_")

    details = {'project_root': sim_dir_split[0],
               'vintage': file_segments[1],
               'version': file_segments[3],
               'building_type': idf_segments[0],
               'climate_zone': idf_segments[2].lower()
               }
    return details


def create_results_dir(idf, scenario, year):
    fname = idf.idfname
    idf_details = decompose_idf_filename(fname)

    version_dir = os.path.join(idf_details['project_root'],
                                    'eplus_simulations',
                                    idf_details['vintage'],
                                    'results',
                                    idf_details['version'])
    check_dir_create(version_dir)
    
    climate_zone_dir = os.path.join(version_dir,
                                    idf_details['climate_zone'],
                                    )
    check_dir_create(climate_zone_dir)

    results_pardir = os.path.join(climate_zone_dir, f'{scenario}_{year}')
    check_dir_create(results_pardir)

    results_dir = os.path.join(results_pardir, idf_details['building_type'])
    check_dir_create(results_dir)

    return results_dir


def make_eplaunch_options(idf, scenario, year):
    """Make options for run, so that it runs like EPLaunch on Windows
    notes: 
    idf (str) – Full or relative path to the IDF file to be run, or an IDF object.
    weather (str) – Full or relative path to the weather file.
    output_directory (str, optional) – Full or relative path to an output directory (default: ‘run_outputs)
    annual (bool, optional) – If True then force annual simulation (default: False)
    expandobjects (bool, optional) – Run ExpandObjects prior to simulation (default: False)
    readvars (bool, optional) – Run ReadVarsESO after simulation (default: False)
    output_prefix (str, optional) – Prefix for output file names (default: eplus)
    output_suffix (str, optional) – Suffix style for output file names (default: L);
                        L: Legacy (e.g., eplustbl.csv), C: Capital (e.g., eplusTable.csv), or D: Dash (e.g., eplus-table.csv)
    """
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    fname = idf.idfname
    options = {
        'ep_version': idfversionstr,  # runIDFs needs the version number
        'output_prefix': os.path.basename(fname).split('.')[0],
        'output_suffix': 'D',
        'output_directory': create_results_dir(idf, scenario, year),
        'readvars': True,
        'expandobjects': True,
        'annual': True
    }
    return options

def inner_loop(scen_year, fnames):
    scenario = scen_year[0]
    year = scen_year[1]
    idfs = (IDF(fname, get_epw_name(fname, scenario, year)) for fname in fnames)
    runs = []
    for idf in idfs:
        details = make_eplaunch_options(idf, scenario, year)
        runs.append((idf, details))
    return runs

def main():
    if sys.platform == 'darwin':
        iddfile = "/Applications/EnergyPlus-22-2-0/Energy+.idd"
        project_root = "/Users/jmccarty/GitHub/cmip6_and_buildings"

    elif sys.platform == 'win32':
        iddfile = r"C:\EnergyPlusV22-2-0\Energy+.idd"
        project_root = r"C:\Users\Justin\Documents\GitHub\cmip6_and_buildings"
    else:
        iddfile = "/Applications/EnergyPlus-22-2-0/Energy+.idd"
        project_root = "/Users/jmccarty/GitHub/cmip6_and_buildings"
    
    IDF.setiddname(iddfile)

    vintages = ['pre1980','post1980', 'new']
    scen_years = build_scen_years()
    
    fnames = load_idf_list(vintages, project_root)
    
    runs_all = []
    for scen_year in scen_years:
        inner_loop_list = inner_loop(scen_year, fnames)
        runs_all.append(inner_loop_list)
        

    num_CPUs = os.cpu_count() - 1
    runs_all  = [item for sublist in runs_all for item in sublist]
    # runIDFs(runs_all, num_CPUs)


if __name__ == '__main__':
    main()
