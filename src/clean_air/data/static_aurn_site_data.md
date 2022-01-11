# Static AURN Site Data
The Automatic Urban and Rural Network (AURN) is a network of air quality 
sensors across the UK managed by the Environment Agency on behalf of DEFRA. 
See https://uk-air.defra.gov.uk/networks/network-info?view=aurn for more details

Details about AURN Sites are accessible via `clean_air.data.storage.AURNSiteDataStore`.

The underlying data is stored in a CSV file, stored on an AWS S3 compatible object store.

## Accessing the data
```python
from typing import List
import boto3
from clean_air.data.storage import AURNSiteDataStore, create_aurn_datastore, AURNSite

# get a datastore instance with default read-only configuration, 
# i.e. access the Clean Air Framework object store
aurn_datastore = create_aurn_datastore()
aurn_sites: List[AURNSite] = list(aurn_datastore.all())

# If you have write credentials, use anon=False to use them.
# They'll be loaded using boto3's config mechanism, 
#   refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
aurn_datastore_with_write_access = create_aurn_datastore(anon=False)

# Have your own object store? You can customise the bucket, location of the CSV file,
# and AWS endpoint you're using.
customised_datastore = create_aurn_datastore(
    bucket_name="mybucket", data_file_path="path/to/CSV/in/bucket/file.csv", endpoint_url="https://s3.amazonaws.com")
# This datastore instance is configured to use a custom bucket on AWS, rather than the default JASMIN cloud

# The most fine-grained control can be achieved by creating a datastore instance directly, 
# passing in a boto3 S3 object instance
# This permits customisation beyond what is offered by create_aurn_datastore()
static_data_obj = boto3.resource("s3").Bucket("mybucket").Object("path/to/CSV/in/bucket/file.csv")
AURNSiteDataStore(static_data_obj)
```

## Data
The data is sourced from ???

### Storage Format
The data is stored in a comma-separated value (CSV) format file on a bucket in the object store.

The fields of the CSV (in order) are:

| Field Name | Description | Example |
| ---------- | ----------- | ------- |
| `Code` | Alphanumeric code that uniquely identifies the site | `ABD7` |
| `Name` | Descriptive name for the site (Alphanumeric with underscores replacing spaces) | `Aberdeen_Union_St_Roadside` |
| `Type` | Environment type classification (see https://uk-air.defra.gov.uk/networks/site-types) | One of the following: <ul><li>`RURAL_BACKGROUND`</li><li>`URBAN_INDUSTRIAL`</li><li>`SUBURBAN_INDUSTRIAL`</li><li>`URBAN_TRAFFIC`</li><li>`SUBURBAN_BACKGROUND`</li><li>`URBAN_BACKGROUND`</li></ul> |
| `Latitude` | Latitude in decimal degrees | `57.14455500` |
| `Longitude` | Longitude in decimal degrees | `-2.106472000` |
| `Date_Opened` | a string with the format `YYYYMMDD` | `19990918` means 18/09/1999 | 
| `Date_Closed` | `0` if the site is still open OR a string with the format `YYYYMMDD` | `19990918` means 18/09/1999 <br/> `0` if site is still operating |
| `Species` | Comma separated list of chemical species identifiers, which are strings. <br/>Yes, this is a comma-separated list within a comma-separated file | `"NO,NO2,NOx"` |

#### Example File Contents
Here is the first few rows (including the header row) af a valid data file
```
Code,Name,Type,Latitude,Longitude,Date_Opened,Date_Closed,Species
ABD,Aberdeen,URBAN_BACKGROUND,57.15736000,-2.094278000,19990918,0,"CO,NO,NO2,NOx,O3,PM10,PM2p5,SO2,nvPM10,nvPM2p5,vPM10,vPM2p5"
ABD7,Aberdeen_Union_St_Roadside,URBAN_TRAFFIC,57.14455500,-2.106472000,20080101,0,"NO,NO2,NOx"
ABD8,Aberdeen_Wellington_Road,URBAN_TRAFFIC,57.13388800,-2.094198000,20160209,0,"NO,NO2,NOx"
```

### Deployment
The CSV data file needs to be uploaded to an S3 compatible object store.  
The bucket name and object key for the file are required.

The defaults, which are for data hosted on the Clean Air Framework object store in the Jasmin cloud,
 are stored in the default arguments for the `clean_air.data.storage.create_aurn_datastore` function:

|                 | Default Value |
|-----------------|---------------|
| Bucket Name     | `aurn`        |
| Object Key      | `AURN_Site_Information.csv` |
| S3 Endpoint URL | `clean_air.data.storage.JasminEndpointUrls.EXTERNAL` (`"https://caf-o.s3-ext.jc.rl.ac.uk"`) |

When deploying the Clean Air Framework in the Jasmin cloud environment, the AURN data file needs to be uploaded to the 
default location.