import copy
import json


import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
import ckan.lib.helpers as h


open_licenses = ['cc-by-4.0', 'psi', 'cc-by', 'cc-by-3.0', 'cc-by-2.0', 'cc-zero', 'cc0', 'gfdl', 'pddl', 'odc-by', 'uk-ogl']
five_star_formats = ['rdf', 'n3', 'sparql', 'ttl', 'rdf-xml', 'jsonld']
four_star_formats = []
three_star_formats = ["kml", "wcs", "netcdf", "tsv", "wfs", "kmz", "qgis", "ods", "json", "odb", "odf",
                      "odg", "xml", "ods", "wms", "wmts", "svg", "jpeg", "csv", "csv.zip", "csv / zip",
                      "atom feed", "xyz", "png", "rss", "geojson", "iati", "ics", "api", "json-stat",
                      "jsonstat", "gtfs", "shp / zip", "shp.zip", "tab", 'shp', 'gml', 'hdf5']

two_star_formats = ["xls", "mdb", "arcgis map service", "bmp", "tiff", "xlsx", "gif", "e00", "mrsid",
                    "arcgis map preview", "mop", "esri rest", "dbase"]


def get_qa_dict(pkg_dict):
    # we'll use the same format the ckanext-qa extension uses
    qa_dict = {'openness_score_reason': '', 'openness_score': 0}

    license_id = pkg_dict.get('license_id')
    
    if license_id is None:
        return {'openness_score': 0, 'openness_score_reason': "No license supplied"}
    
    # pretty easy - first check if the license is open
    register = model.Package.get_license_register()
    if (not register.get(license_id) or register.get(license_id).isopen() == False) and license_id.lower() not in open_licenses:
        qa_dict['openness_score_reason'] = 'The dataset license is not in our list of Open Licenses.'
        return qa_dict
    

    # now it's at least 1-star
    qa_dict['openness_score'] = 1
    qa_dict['openness_score_reason'] = 'The dataset license is an open license'

    # now we pretty much just compare formats
    resource_formats = [r.get('format').lower() for r in pkg_dict.get('resources')]

    share_elements = lambda a, b: not set(a).isdisjoint(set(b))

    if (share_elements(resource_formats, five_star_formats)):
        qa_dict['openness_score'] = 5
        qa_dict['openness_score_reason'] = 'One of the resource formats is 5-star data - linked data.'
    elif (share_elements(resource_formats, four_star_formats)):
        qa_dict['openness_score'] = 4
        qa_dict['openness_score_reason'] = 'One of the resource formats is 4-star data - data that uses URIs.'
    elif (share_elements(resource_formats, three_star_formats)):
        qa_dict['openness_score'] = 3
        qa_dict['openness_score_reason'] = 'One of the resource formats is 3-star data - machine-readable data in an open format.'
    elif (share_elements(resource_formats, two_star_formats)):
        qa_dict['openness_score'] = 2
        qa_dict['openness_score_reason'] = 'One of the resource formats is 2-star data - machine-readable data in a proprietary format.'

    return qa_dict


def qa_openness_stars_resource_html(resource):
    qa = resource.get('qa')
    if not qa:
        return toolkit.literal('<!-- No qa info for this resource -->')
    if not isinstance(qa, dict):
        return toolkit.literal('<!-- QA info was of the wrong type -->')

    # Take a copy of the qa dict, because weirdly the renderer appears to add
    # keys to it like _ and app_globals. This is bad because when it comes to
    # render the debug in the footer those extra keys take about 30s to render,
    # for some reason.
    extra_vars = copy.deepcopy(qa)
    return toolkit.literal(
        toolkit.render('qa/openness_stars.html',
                  extra_vars=extra_vars))


def qa_openness_stars_dataset_html(dataset):
    qa = dataset.get('qa')
    if not qa:
        return toolkit.literal('<!-- No qa info for this dataset -->')
    if not isinstance(qa, dict):
        return toolkit.literal('<!-- QA info was of the wrong type -->')
    extra_vars = copy.deepcopy(qa)
    return toolkit.literal(
        toolkit.render('qa/openness_stars_brief.html',
                  extra_vars=extra_vars))


class DietStarsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        try:
            toolkit.requires_ckan_version("2.9")
            toolkit.add_template_directory(config_, 'templates')
        except toolkit.CkanVersionException:
            toolkit.add_template_directory(config_, 'templates_28')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'qa_openness_stars_resource_html': qa_openness_stars_resource_html,
            'qa_openness_stars_dataset_html': qa_openness_stars_dataset_html,
            'get_qa_dict': get_qa_dict
        }

    # IPackageController

    def before_dataset_index(self, search_dict):
        # we add the QA dict here so we can facet
        # print pkg_dict
        pkg_dict = json.loads(search_dict['data_dict'])
        search_dict['openness_score'] = get_qa_dict(pkg_dict)['openness_score']
        search_dict.pop('qa', None)
        return search_dict
    before_index = before_dataset_index

    # add the QA dict here so we can show it :)
    def before_dataset_view(self, pkg_dict):
        pkg_dict['qa'] = get_qa_dict(pkg_dict)
        return pkg_dict
    before_view = before_dataset_view

    def after_dataset_show(self, context, pkg_dict):
        pkg_dict['qa'] = get_qa_dict(pkg_dict)
        return pkg_dict
    after_show = after_dataset_show

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        if (package_type == 'dataset'):
            facets_dict['openness_score'] = plugins.toolkit._('Openness')
        return facets_dict
