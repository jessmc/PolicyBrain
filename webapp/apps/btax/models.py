import re

from django.db import models
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User

from uuidfield import UUIDField
from jsonfield import JSONField
import datetime

from ..taxbrain.models import (SeparatedValuesField,
                               OutputUrl, convert_to_floats,
                               CommaSeparatedField)


class BTaxSaveInputs(models.Model):
    """
    This model contains all the parameters for the tax model and the tax
    result.

    For filing status fields:
    _0 = Single, _1 = Married filing Jointly, _2 = Married filing Separately,
    _3 = Head of Household (example: _SS_thd50_0 is the Single filing
    status for Income Threshold 1 in the Social Security Tax section.)
    The exception to this rule is for EITC, where:
    _0 = 0 Kids, _1 = 1 Kid, _2 = 2 Kids, & _3 = 3+ Kids
    """

    btax_bitr_corp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_bitr_entity_Switch = models.NullBooleanField(default=None, blank=True, null=True)
    btax_bitr_pass = CommaSeparatedField(default=None, blank=True, null=True)

    btax_depr_allyr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_3yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_5yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_7yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_10yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_15yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_20yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_25yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_27_5yr = CommaSeparatedField(default=None, blank=True, null=True)
    btax_depr_39yr = CommaSeparatedField(default=None, blank=True, null=True)

    btax_depr_allyr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_3yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_5yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_7yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_10yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_15yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_20yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_25yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_39yr_gds_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)

    btax_depr_allyr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_3yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_5yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_7yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_10yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_15yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_20yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_25yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_39yr_ads_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)

    btax_depr_allyr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_3yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_5yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_7yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_10yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_15yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_20yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_25yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)
    btax_depr_39yr_tax_Switch = models.CharField(default="True", blank=True, null=True, max_length=50)

    btax_depr_allyr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_3yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_5yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_7yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_10yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_15yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_20yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_25yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_27_5yr_exp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_depr_39yr_exp = CommaSeparatedField(default=None, null=True, blank=True)


    btax_other_hair = CommaSeparatedField(default=None, null=True, blank=True)
    btax_other_corpeq = CommaSeparatedField(default=None, null=True, blank=True)
    btax_other_proptx = CommaSeparatedField(default=None, null=True, blank=True)
    btax_other_invest = CommaSeparatedField(default=None, null=True, blank=True)
    btax_econ_nomint = CommaSeparatedField(default=None, null=True, blank=True)
    btax_econ_inflat = CommaSeparatedField(default=None, null=True, blank=True)


    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
    jobs_not_ready = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)

    # Result
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))


    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )

