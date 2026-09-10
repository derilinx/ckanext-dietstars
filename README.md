# ckanext-dietstars

Show an Openness score using 0 to 5 stars depending on the openness of the metadata.

CKAN versions supported: 2.9 to 2.12


The extension uses the license and resource formats to compute the score. Check `plugin.py` for the actual logic.

The information is indexed in the dataset metadata in the `qa` property with the following format:

```
{'openness_score_reason': 'xx', 'openness_score': 0}
```

This is used to display the relevant stars in the frontend, in the following templates:

* Search facets (`facet_list.html`)
* Dataset items in lists (e.g. search results) (`package_item.html`)
* Dataset page (`package/read_base.html`)

## Configuration

Enable the `dietstars` plugin


> [!IMPORTANT]
> If used alongside ckanext-psbthemealt, the dietstars plugin needs to be loaded first:
>
>     ckan.plugins = ... dietstars psbthemealt



