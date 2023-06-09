


import eppy_multi
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import pathlib
from shapely.geometry import Point
import pandas as pd
import numpy as np
import os
import glob
import geopandas as gpd
import sys
# import cartopy.crs as ccrs
import json
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)

project_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
if sys.platform == 'win32':
    module_path = r"C:\Users\Justin\Documents\GitHub\IPV_Workbench"
else:
    module_path = "/Users/jmccarty/Data/221205_ipv_workbench/github/IPV_Workbench"
sys.path.insert(0, module_path)
from ipv_workbench.utilities import utils


def get_scenario_colors(category):
    color_dict = {}
    with open(os.path.join('input_data', 'IPCC Style Scenarios.json'), 'r') as json_file:
        data = json.load(json_file)
    for entry in data[category]:
        scenario = entry['scenario']
        color_dict[scenario] = entry['hex']
    return color_dict


def round_down(num, divisor):
    return num - (num % divisor)


def myround(x, base=5):
    rounded = base * round(x/base)
    if rounded == 0:
        rounded = base
    return rounded


def find_file(file_list, key):
    return [f for f in file_list if key in f][0]


def get_year_bands(year, formatted=True):
    if formatted:
        year_bands = f'{year-15}-{year+15}'
    else:
        year_bands = (year-15, year+15)
    return year_bands


def get_years():
    return [2020, 2035, 2050, 2065, 2080]


def get_vintages():
    return [('new', 'New2004'), ('post1980', 'Post1980'), ('pre1980', 'Pre1980')]


def get_scenarios():
    return ['historical', 'ssp126', 'ssp245', 'ssp585']


def get_project_dir():
    return pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent


def get_cz_list():
    cz_list = ['1a', '2a', '2b', '3a', '3b', '3bc', '3c', '4a',
               '4b', '4c', '5a', '5b', '6a', '6b', '7a', '8a']
    return cz_list


def compile_sim_code(all_dict, vintage, cz, scen_year, bldg_type):
    return f"{all_dict['vintage'][vintage]}_{all_dict['cz'][cz]}_{all_dict['scen_year'][scen_year]}_{all_dict['bldg_type'][bldg_type]}"


def reverse_sim_code(all_dict, sim_code):
    sim_el = sim_code.split("_")
    sim_el = [int(e) for e in sim_el]
    vintage = all_dict['vintage_r'][sim_el[0]]
    cz = all_dict['cz_r'][sim_el[1]]

    scen_year = all_dict['scen_year_r'][sim_el[2]].replace("_", "-")
    scenario = scen_year.split("-")[0]
    year = scen_year.split("-")[1]
    bldg_type = all_dict['bldg_type_r'][sim_el[3]]

    return f"{vintage}_{cz}_{scenario}_{year}_{bldg_type}"


def get_color_dict():
    cz_color_dict = {}
    with open(os.path.join('input_data', 'IECC Climate Zones Colors.json'), 'r') as json_file:
        data = json.load(json_file)
    for entry in data['colors']:
        zone_code = entry['zone']
        cz_color_dict[zone_code] = entry['hex']
    return cz_color_dict


def get_cz_names():

    cz_names = {'1a': 'Very Hot Humid',
                '2a': 'Hot Humid',
                '2b': 'Hot Dry',
                '3a': 'Warm Humid',
                '3b': 'Warm Dry',
                '3bc': 'Warm Dry Marine',
                '3c': 'Warm Marine',
                '4a': 'Mixed Humid',
                '4b': 'Mixed Dry',
                '4c': 'Mixed Marine',
                '5a': 'Cool Humid',
                '5b': 'Cold Dry',
                '5c': 'Cool Marine',
                '6a': 'Cold Humid',
                '6b': 'Cold Dry',
                '7a': 'Very Cold',
                '8a': 'Subarctic/Arctic'}

    return cz_names


def get_location_dict():
    project_dir = get_project_dir()
    location_dict = {}

    for cz in get_cz_list():
        epw_file = glob.glob(os.path.join(
            project_dir, 'weather_files', 'tmy3', f'{cz}*'))[0]
        location = utils.tmy_location(epw_file)
        lat = location['lat']
        lon = location['lon']
        location_dict[cz] = (lon, lat)

    return location_dict


def build_lgd(colors, labels, element_type='patch', marker='o'):
    lgd_el = []
    if element_type == 'patch':
        for c, l in zip(colors, labels):
            el = Patch(facecolor=c, edgecolor=None,
                       label=l)
            lgd_el.append(el)
    elif element_type == 'marker':
        for c, l in zip(colors, labels):
            el = Line2D([0], [0], marker=marker, color='white', label=l,
                        markerfacecolor=c[0], markeredgecolor=c[1], markersize=10)
            lgd_el.append(el)
    return lgd_el


def plot_us_map_heatmap(zones, plot_col, lgd_label, lgd=False, ax=None, lgd_kw=None, vmin=None, vmax=None, cmap='cividis', norm=None, plot_points=True, save=False):
    if lgd_kw is None:
        lgd_kw = {'location': 'right',
                  'pad': -0.02,
                  'shrink': 0.75,
                  'extend': 'neither',
                  'spacing': 'uniform',
                  'label': lgd_label,
                  }
    cz_list = get_cz_list()
    cz_names = get_cz_names()
    cz_color_dict = get_color_dict()
    location_dict = get_location_dict()

    this_dir = os.path.dirname(os.path.realpath(__file__))
    state_lines = gpd.read_file(os.path.join(
        this_dir, 'input_data', 'us-states.json')).to_crs(epsg=2163)

    # create an axis with 2 insets − this defines the inset sizes
    if ax is None:
        fig, ax = plt.subplots(figsize=(20, 10))
    continental_ax = ax
    alaska_ax = continental_ax.inset_axes([.01, .01, .20, .28])
    hawaii_ax = continental_ax.inset_axes([.21, .01, .15, .19])

    if vmin is None:
        vmin = -zones[plot_col].max()

    if vmax is None:
        vmax = zones[plot_col].max()

    cont = zones[(zones['State'] != 'Alaska') & (zones['State'] != 'Hawaii')]
    alaska = zones[zones['State'] == 'Alaska']
    hawaii = zones[zones['State'] == 'Hawaii']

    cont.plot(ax=continental_ax, column=plot_col, cmap=cmap, norm=norm,
              antialiased=False,
              vmin=vmin, vmax=vmax,
              legend=lgd,
              legend_kwds=lgd_kw,
              )
    alaska.plot(ax=alaska_ax, column=plot_col, cmap=cmap, norm=norm,
                edgecolor='face', lw=0, antialiased=False,
                vmin=vmin, vmax=vmax)
    hawaii.plot(ax=hawaii_ax, column=plot_col, cmap=cmap, norm=norm,
                edgecolor='face', lw=0, antialiased=False,
                vmin=vmin, vmax=vmax)

    # remove ticks
    for ax in [continental_ax, alaska_ax, hawaii_ax]:
        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_frame_on(False)

    cont_lines = state_lines[(state_lines['name'] != 'Alaska') & (
        state_lines['name'] != 'Hawaii') & (state_lines['name'] != 'Puerto Rico')]
    alaska_line = state_lines[state_lines['name'] == 'Alaska']
    hawaii_line = state_lines[state_lines['name'] == 'Hawaii']

    cont_lines.plot(ax=continental_ax, facecolor="none",
                    edgecolor='black', lw=0.7)
    alaska_line.plot(ax=alaska_ax, facecolor="none", edgecolor='black', lw=0.7)
    hawaii_line.plot(ax=hawaii_ax, facecolor="none", edgecolor='black', lw=0.7)

    if plot_points is True:
        # plot_locations
        plot_points_a = []
        plot_points_b = []
        for cz in cz_list:
            if cz == '8a':
                plot_points_b.append(Point(location_dict[cz]))
            else:
                plot_points_a.append(Point(location_dict[cz]))

        gpd.GeoSeries(plot_points_a).set_crs('EPSG:4326').to_crs('EPSG:2163').plot(ax=continental_ax,
                                                                                   markersize=75, color='white', marker='o',
                                                                                   edgecolor='k', lw=1, zorder=3, antialiased=True)

        gpd.GeoSeries(plot_points_b).set_crs('EPSG:4326').to_crs('EPSG:2163').plot(ax=alaska_ax,
                                                                                   markersize=75, color='white', marker='o',
                                                                                   edgecolor='k', lw=1, zorder=3, antialiased=True)

        lgd_el_tmy = build_lgd(
            [('white', 'k')], ['Simulation Location'], element_type='marker')
    if lgd is True:
        continental_ax.legend(handles=lgd_el_tmy, loc='lower right', frameon=False, title='',
                              fontsize=8)

    plt.tight_layout()

    if save == False:
        pass
    else:
        plt.savefig(save, dpi=200)
    return ax


def test():
    print(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent)


bldg_types = ['RefBldgFullServiceRestaurant',
              'RefBldgHospital',
              'RefBldgLargeHotel',
              'RefBldgLargeOffice',
              'RefBldgMediumOffice',
              'RefBldgMidriseApartment',
              'RefBldgOutPatient',
              'RefBldgPrimarySchool',
              'RefBldgQuickServiceRestaurant',
              'RefBldgSecondarySchool',
              'RefBldgSmallHotel',
              'RefBldgSmallOffice',
              'RefBldgStand-aloneRetail',
              'RefBldgStripMall',
              'RefBldgSuperMarket',
              'RefBldgWarehouse']
map_bldg_type = dict(zip(bldg_types, np.arange(0, len(bldg_types))))


def reverse_dict(my_dict):
    return dict(zip(my_dict.values(), my_dict.keys()))


map_cz = dict(zip(get_cz_list(), np.arange(0, len(get_cz_list()))))
scen_years = eppy_multi.build_scen_years()
scen_years = [f'{a}_{b}' for a, b in eppy_multi.build_scen_years()]
map_scen_years = dict(zip(scen_years, np.arange(0, len(scen_years))))
vintages = ['pre1980', 'post1980', 'new']
map_vintages = dict(zip(vintages, [0, 1, 2]))


all_dict = {'vintage': map_vintages,
            'vintage_r': reverse_dict(map_vintages),
            'cz': map_cz,
            'cz_r': reverse_dict(map_cz),
            'scen_year': map_scen_years,
            'scen_year_r': reverse_dict(map_scen_years),
            'bldg_type': map_bldg_type,
            'bldg_type_r': reverse_dict(map_bldg_type)}

map_perf_metrics = {'hs_el_kwh': '13',
                    'hs_ng_kwh': '14',
                    'cs_el_kwh': '15',
                    'fan_el_kwh': '16',
                    'fac_ng_kwh': '17',
                    'fac_el_kwh': '18',
                    'geff_irrad_kwh': '19',
                    'cell_temp_degc': '20',
                    'pv_yield_kwh': '21',
                    'fac_el_net_kwh': '22',
                    'pv_consumed_kwh': '23',
                    'pv_excess_kwh': '24',
                    'self_suff_pct': '25',
                    'self_consume_pct': '26',
                    'op_em_kgco2': '27',
                    'op_em_pv_kgco2': '28',
                    'mit_pot_kgco2': '29'}

tables_of_interest = ['Discomfort-weighted Exceedance OccupiedHours',
                      'Comfort and Setpoint Not Met Summary',
                      'Heat Index OccupiedHours',
                      'Unmet Degree-Hours']

annual_comfort_metrics = {
    'Discomfort-weighted Exceedance OccupiedHours': {
        'Very-cold Exceedance OccupantHours [hr]': '0',
        'Cool Exceedance OccupantHours [hr]': '1',
        'Warm Exceedance OccupantHours [hr]': '2',
        'Very-hot Exceedance OccupantHours [hr]': '3'},
    'Comfort and Setpoint Not Met Summary': {
        'Time Setpoint Not Met During Occupied Heating': '4',
        'Time Setpoint Not Met During Occupied Cooling': '5'},
    'Heat Index OccupiedHours': {
        'Safe (≤ 26.7°C) [hr]': '6',
        'Caution (> 26.7°C, ≤ 32.2°C) [hr]': '7',
        'Extreme Caution (> 32.2°C, ≤ 39.4°C) [hr]': '8',
        'Danger (> 39.4°C, ≤ 51.7°C) [hr]': '9',
        'Extreme Danger (> 51.7°C) [hr]': '10'},
    'Unmet Degree-Hours': {
        'Cooling Setpoint Unmet Occupied Degree-Hours [°C·hr]': '11',
        'Heating Setpoint Unmet Occupied Degree-Hours [°C·hr]': '12'}
}

annual_comfort_metrics_lite = {'Very-cold Exceedance OccupantHours [hr]': '0',
                               'Cool Exceedance OccupantHours [hr]': '1',
                               'Warm Exceedance OccupantHours [hr]': '2',
                               'Very-hot Exceedance OccupantHours [hr]': '3',
                               'Time Setpoint Not Met During Occupied Heating': '4',
                               'Time Setpoint Not Met During Occupied Cooling': '5',
                               'Safe (≤ 26.7°C) [hr]': '6',
                               'Caution (> 26.7°C, ≤ 32.2°C) [hr]': '7',
                               'Extreme Caution (> 32.2°C, ≤ 39.4°C) [hr]': '8',
                               'Danger (> 39.4°C, ≤ 51.7°C) [hr]': '9',
                               'Extreme Danger (> 51.7°C) [hr]': '10',
                               'Cooling Setpoint Unmet Occupied Degree-Hours [°C·hr]': '11',
                               'Heating Setpoint Unmet Occupied Degree-Hours [°C·hr]': '12'}

all_kpi = {'Very-cold Exceedance OccupantHours [hr]': '0',
           'Cool Exceedance OccupantHours [hr]': '1',
           'Warm Exceedance OccupantHours [hr]': '2',
           'Very-hot Exceedance OccupantHours [hr]': '3',
           'Time Setpoint Not Met During Occupied Heating': '4',
           'Time Setpoint Not Met During Occupied Cooling': '5',
           'Safe (≤ 26.7°C) [hr]': '6',
           'Caution (> 26.7°C, ≤ 32.2°C) [hr]': '7',
           'Extreme Caution (> 32.2°C, ≤ 39.4°C) [hr]': '8',
           'Danger (> 39.4°C, ≤ 51.7°C) [hr]': '9',
           'Extreme Danger (> 51.7°C) [hr]': '10',
           'Cooling Setpoint Unmet Occupied Degree-Hours [°C·hr]': '11',
           'Heating Setpoint Unmet Occupied Degree-Hours [°C·hr]': '12',
           'hs_el_kwh': '13',
           'hs_ng_kwh': '14',
           'cs_el_kwh': '15',
           'fan_el_kwh': '16',
           'fac_ng_kwh': '17',
           'fac_el_kwh': '18',
           'geff_irrad_kwh': '19',
           'cell_temp_degc': '20',
           'pv_yield_kwh': '21',
           'fac_el_net_kwh': '22',
           'pv_consumed_kwh': '23',
           'pv_excess_kwh': '24',
           'self_suff_pct': '25',
           'self_consume_pct': '26',
           'op_em_kgco2': '27',
           'op_em_pv_kgco2': '28',
           'mit_pot_kgco2': '29'}

code_names = {'0': 'vintage',
              '1': 'climate_zone',
              '2': 'scenario',
              '3': 'year',
              '4': 'bldg_type'}


def dict_key_to_int(in_dict):
    new_keys = [int(k) for k in in_dict.keys()]

    return dict(zip(new_keys, in_dict.values()))


def expand_code_idx_to_df(df, all_dict, code_names):
    df_cols = df.index.to_series().apply(lambda x: reverse_sim_code(all_dict,
                                                                    x)).str.split("_",
                                                                                  expand=True).rename(columns=dict_key_to_int(code_names))
    return df_cols


def get_kpi_descriptions():
    with open(os.path.join('input_data', 'kpi_descriptions.json'), 'r') as json_file:
        data = json.load(json_file)
    return data


def filter_delta_df(all_dict, df, vintage, cz, scen_year, bldg_type):
    code = compile_sim_code(all_dict, vintage, cz, scen_year, bldg_type)
    return df.loc[code]


def combine_result_to_zones(all_dict, code_names, zones, delta_df, col, vintage, scen_year, bldg_type):
    match_codes = []
    for cz in get_cz_list():
        match_codes.append(compile_sim_code(all_dict, vintage, cz, scen_year, bldg_type))
    result = delta_df[[col]].loc[match_codes]
    result = result.join(expand_code_idx_to_df(result, all_dict, code_names))
    result = result.set_index('climate_zone')
    data_dict = result[col].to_dict()
    new_series = zones['climate_zone'].map(data_dict)
    return new_series
