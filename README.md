# clean-air-project

The Clean Air Project is a collaboration between scientists and software engineers to create a website which will allow users to upload, access, process and download air quality data.
We will be using cutting edge technology and software to engineer a fully-functional, easy-to-use one-stop-shop for air quality data, including resources for researchers and decision-makers such as analysis pipelines and health impacts.

## Installation

Software dependencies are intended to be installed using `conda`:
```bash
conda env create -f environment.yml
```

Then, install the `clean_air` package to this environment using `pip`:
```bash
conda activate cap_env
pip install .
```

Remember to use the `-e` option to `pip install` for development work.

## Credentials
Some code accesses resources held in an AWS S3 compatible object store.
Credentials must be provided by 
(TODO... we use boto3, so probably need the credentials stored in a way that boto3 will access)

## Deployment
Fully setting up the environment requires some steps beyond installing the code:
* See [Static AURN Site Data](clean_air/data/static_aurn_site_data.md)


# Development
## Running The Tests
Tests are run using `pytest`.  

They also require the sample data located in the `cap-sample-data` repository. 
This repo should be checked out to the same directory as this repo, so that the 2 repositories are peers.

The custom `--sampledir` option to the `pytest` command can also be used to change the default location the tests look
for the same data. E.g. `pytest --sampledir /path/to/sample/data/repo/root`