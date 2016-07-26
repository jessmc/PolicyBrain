from collections import namedtuple
import numbers
import os
import pandas as pd
import dropq
import string
import sys
import time
import six

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys

from ..taxbrain.helpers import (make_bool, convert_val,
                                is_wildcard, int_to_nth,
                                is_number, is_string,
                                string_to_float, string_to_float_array,
                                same_version, arrange_totals_by_row,
                                round_gt_one_to_nearest_int, expand_1D,
                                expand_2D, expand_list, leave_name_in,
                                TaxCalcField)

import btax

MOCK_MODULES = ['numba', 'numba.jit', 'numba.vectorize', 'numba.guvectorize',
                'matplotlib', 'matplotlib.pyplot', 'mpl_toolkits',
                'mpl_toolkits.mplot3d', 'pandas']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

PYTHON_MAJOR_VERSION = sys.version_info.major

BTAX_BITR = ['btax_bitr_corp',
             'btax_bitr_pass',
             'btax_bitr_entity_Switch']
BTAX_DEPREC = ['btax_depr_allyr', 'btax_depr_3yr', 'btax_depr_5yr',
               'btax_depr_7yr', 'btax_depr_10yr',
               'btax_depr_15yr','btax_depr_20yr', 'btax_depr_25yr',
               'btax_depr_27_5yr', 'btax_depr_39yr']
BTAX_OTHER = ['btax_other_hair', 'btax_other_corpeq',
              'btax_other_proptx','btax_other_invest']
BTAX_ECON = ['btax_econ_nomint', 'btax_econ_inflat',]


# TODO remove this when btax package
# has versioneer
from argparse import Namespace
btax._version = Namespace(get_versions=lambda: {'version': '0.1', 'full': '0.1'})
BTAX_VERSION_INFO = btax._version.get_versions()
BTAX_VERSION = ".".join([BTAX_VERSION_INFO['version'], BTAX_VERSION_INFO['full'][:6]])

#
# Prepare user params to send to DropQ/Taxcalc
#
class BTaxField(TaxCalcField):

    pass


def package_up_vars(user_values):

    return {k: v for k, v in user_values.items()
            if k in BTAX_DEFAULTS}


class BTaxParam(object):

    """
    A collection of TaxCalcFields that represents all configurable details
    for one of TaxCalc's Parameters
    """
    coming_soon = False
    inflatable = False
    def __init__(self, param_id, attributes):
        self.__load_from_json(param_id, attributes)

    def __load_from_json(self, param_id, attributes):
        # TODO does /btax need to handle
        # budget year /start year logic
        # as in /taxbrain. If so, see
        # TaxCalcParam for changes to
        # make here
        self.start_year = first_budget_year = 2015

        values_by_year = attributes['value']
        col_labels = attributes['col_label']

        self.tc_id = param_id
        self.nice_id = param_id[1:] if param_id[0] == '_' else param_id
        self.name = attributes['long_name']
        self.info = " ".join([
            attributes['description'],
            attributes.get('notes') or ""     # sometimes this is blank
            ]).strip()

        # normalize single-year default lists [] to [[]]
        if not isinstance(values_by_year[0], list):
            values_by_year = [values_by_year]

        # organize defaults by column [[A1,B1],[A2,B2]] to [[A1,A2],[B1,B2]]
        values_by_col = [list(x) for x in zip(*values_by_year)]

        # create col params
        self.col_fields = []

        if len(col_labels) == 1:
            self.col_fields.append(TaxCalcField(
                self.nice_id,
                col_labels[0],
                values_by_col[0],
                self,
                first_budget_year
            ))
        else:
            for col, label in enumerate(col_labels):
                self.col_fields.append(TaxCalcField(
                    label,
                    label,
                    values_by_col[col],
                    self,
                    first_budget_year
                ))

        # we assume we can CPI inflate if first value isn't a ratio
        first_value = self.col_fields[0].values[0]

        validations_json =  attributes.get('validations')
        if validations_json:
            self.max = validations_json.get('max')
            self.min = validations_json.get('min')
        else:
            self.max = None
            self.min = None

        # Coax string-formatted numerics to floats and field IDs to nice IDs
        if self.max:
            if is_string(self.max):
                try:
                    self.max = string_to_float(self.max)
                except ValueError:
                    if self.max[0] == '_':
                        self.max = self.max[1:]

        if self.min:
            if is_string(self.min):
                try:
                    self.min = string_to_float(self.min)
                except ValueError:
                    if self.min[0] == '_':
                        self.min = self.min[1:]

# Create a list of default policy
def get_btax_defaults():

    TAXCALC_DEFAULT_PARAMS = {}
    for k in (BTAX_BITR + BTAX_OTHER + BTAX_ECON):
        param = BTaxParam(k,
                         {'col_label': [''],
                          'value': [[.986]],
                          'description': 'description',
                          'long_name': '',
                          'notes': 'notes',
                          'irs_ref': 'irs_ref',
                          'cpi_inflated': False})
        TAXCALC_DEFAULT_PARAMS[param.nice_id] = param
    for k in BTAX_DEPREC:
        fields = ['{}_{}_Switch'.format(k, tag)
                     for tag in ('gds','ads',  'tax')]
        fields += ['{}_{}'.format(k, 'exp')]

        for field in fields:
            param = BTaxParam(field,
                                 {'col_label': [''],
                                  'value': [True,] ,
                                  'description': 'description',
                                  'long_name': '',
                                  'notes': 'notes' + field,
                                  'name': 'name',
                                  'info': 'info'})
            TAXCALC_DEFAULT_PARAMS[param.nice_id] = param


    return TAXCALC_DEFAULT_PARAMS

BTAX_DEFAULTS = get_btax_defaults()


def group_args_to_btax_depr(taxcalc_default_params, asset_yr_str):
    depr_field_order = ('gds', 'ads', 'exp', 'tax')
    depr_argument_groups = []
    for yr in ['all'] + asset_yr_str:
        gds_id = 'btax_depr_{}yr_gds_Switch'.format(yr)
        ads_id = 'btax_depr_{}yr_ads_Switch'.format(yr)
        tax_id = 'btax_depr_{}yr_tax_Switch'.format(yr)
        exp_id = 'btax_depr_{}yr_exp'.format(yr)
        radio_group_name = 'btax_depr_gds_{}yr_ads'.format(yr)
        field3_cb = 'btax_depr__{}yr_exp'.format(yr)
        field4_cb = 'btax_depr_{}yr_tax'.format(yr)

        if yr == 'all':
            pretty = "Check all"
            is_check_all = True
            label = ''
            td_style_class = 'table-check-all-item'
            tr_style_class = 'tr-check-all'
        else:
            td_style_class = ''
            is_check_all = False
            label = ''
            tr_style_class = ''
            pretty = '{}-year'.format(yr.replace('_', '.'))
        depr_argument_groups.append(
            dict(param1=taxcalc_default_params[gds_id],
                 field1=gds_id,
                 param2=taxcalc_default_params[ads_id],
                 field2=ads_id,
                 param3=taxcalc_default_params[tax_id],
                 field3=tax_id,
                 param4=taxcalc_default_params[exp_id],
                 field4=exp_id,
                 radio_group_name=radio_group_name,
                 asset_yr_str=yr,
                 tr_style_class=tr_style_class,
                 pretty_asset_yr_str=pretty,
                 field3_cb=field3_cb,
                 field4_cb=field4_cb,
                 is_check_all=is_check_all,
                 label=label,
                 td_style_class="table-check-all-item" if yr == 'all' else '')

            )
    return depr_argument_groups

