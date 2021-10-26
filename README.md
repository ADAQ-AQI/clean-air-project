# clean-air-project

The Clean Air Project is a collaboration between scientists and software engineers to create a website which will allow users to upload, access, process and download air quality data.
We will be using cutting edge technology and software to engineer a fully-functional, easy-to-use one-stop-shop for air quality data, including resources for researchers and decision-makers such as analysis pipelines and health impacts.

## Installation

Dependencies are intended to be installed using `conda`:

```
conda env create -f environment.yml
```

Then, install the `clean_air` package to this environment using `pip`:

```
conda activate cap_env
pip install .
```

Remember to use the `-e` option to `pip install` for development work.
