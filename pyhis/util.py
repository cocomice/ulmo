"""
    pyhis.util
    ~~~~~~~

    Set of utility functions that help pyhis do its thing.
"""
from datetime import datetime

import numpy as np
import pandas
from shapely.geometry import Point, Polygon

import pyhis


def _shapely_geometry_from_geolocation(geolocation):
    """returns a shapely object given a suds WaterML geolocation element"""

    if geolocation.geogLocation.__class__.__name__ == 'LatLonPointType':
        return Point(geolocation.geogLocation.longitude,
                     geolocation.geogLocation.latitude)

    else:
        raise NotImplementedError(
            "Don't know how to convert location type: '%s'" %
            geolocation.geogLocation.__class__.__name__)


def _site_from_wml_siteInfo(site, client):
    """returns a PyHIS Site instance from a suds WaterML siteInfo element"""
    if len(site.siteInfo.siteCode) > 1:
        raise NotImplementedError(
            "Multiple site codes not currently supported")

    site_code = site.siteInfo.siteCode[0]

    return pyhis.Site(
        name=site.siteInfo.siteName,
        code=site_code.value,
        id=site_code._siteID,
        network=site_code._network,
        location=site.siteInfo.geoLocation,
        client=client)


def _variable_from_wml_variableInfo(variable_info):
    """returns a PyHIS Variable instance from a suds WaterML variableInfo
    element"""
    if len(variable_info.variableCode) > 1:
        raise NotImplementedError(
            "Multiple variable codes not currently supported")

    return pyhis.Variable(
        name=variable_info.variableName,
        code=variable_info.variableCode[0].value,
        id=variable_info.variableCode[0]._variableID,
        vocabulary=variable_info.variableCode[0]._vocabulary,
        units=_units_from_wml_units(variable_info.units),
        no_data_value=variable_info.NoDataValue)


def _timeseries_from_wml_series(series, site):
    """returns a PyHIS series instance from a suds WaterML series element"""
    datetime_fmt = "%Y-%d-%m %H:%M:%S"

    return pyhis.TimeSeries(
        variable=_variable_from_wml_variableInfo(series.variable),
        count=series.valueCount,
        method=series.Method.MethodDescription,
        quality_control_level=series.QualityControlLevel._QualityControlLevelID,
        begin_datetime=series.variableTimeInterval.beginDateTime,
        end_datetime=series.variableTimeInterval.endDateTime,
        site=site)


def _pandas_series_from_wml_TimeSeriesResponseType(timeseries_response):
    """returns a tuple where the first element is a pandas.Series
    object representing a timeseries and the second element is the
    python quantity that corresponds the unit for the variable. Takes
    a suds WaterML TimeSeriesResponseType object.
    """
    unit_code = timeseries_response.timeSeries.variable.units._unitsCode
    quantity = pyhis.variable_quantities[unit_code]

    values = timeseries_response.timeSeries.values.value
    dates = np.array([value._dateTime for value in values])
    data = np.array([float(value.value) for value in values])

    series = pandas.Series(data, index=dates)
    return series, quantity


def _units_from_wml_units(units):
    """returns a PyHIS Units instance from a suds WaterML units element"""
    return pyhis.Units(
        name=units.value,
        abbreviation=units._unitsAbbreviation,
        code=units._unitsCode)