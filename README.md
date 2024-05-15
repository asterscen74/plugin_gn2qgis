# GeoNature 2 QGIS - QGIS Plugin

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


[![flake8](https://img.shields.io/badge/linter-flake8-green)](https://flake8.pycqa.org/)

## Generated options

### Plugin

| Cookiecutter option | Picked value |
| :-- | :--: |
| Plugin name | GeoNature 2 QGIS |
| Plugin name slugified | gn2qgis |
| Plugin name class (used in code) | Gn2Qgis |
| Plugin category | Database |
| Plugin description short | This plugin allow you to import data from GeoNature to QGIS |
| Plugin description long | Allow the user to extract data from multiple GeoNature instances. |
| Plugin tags | geonature, observations |
| Plugin icon | default_icon.png |
| Plugin with processing provider | False |
| Author name | Jules GRILLOT |
| Author organization | Asters - CEN74 |
| Author email | jules.grillot@cen-haute-savoie.org |
| Minimum QGIS version | 3.28 |
| Maximum QGIS version | 3.99 |
| Git repository URL | https://github.com/JulesGrillot/plugin_gn2qgis/ |
| Git default branch | main |
| License | GPLv2+ |
| Python linter | Flake8 |
| CI/CD platform | GitHub |
| IDE | VSCode |

### Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question
- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.  
Static code analisis is based on: Flake8

See also: [contribution guidelines](CONTRIBUTING.md).

## CI/CD

Plugin is linted, tested, packaged and published with GitHub.

If you mean to deploy it to the [official QGIS plugins repository](https://plugins.qgis.org/), remember to set your OSGeo credentials (`OSGEO_USER_NAME` and `OSGEO_USER_PASSWORD`) as environment variables in your CI/CD tool. 


### Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

- homepage: <https://github.com/JulesGrillot/plugin_gn2qgis/>
- repository: <https://github.com/JulesGrillot/plugin_gn2qgis/>
- tracker: <https://github.com/JulesGrillot/plugin_gn2qgis//issues>

----

## Next steps

### Set up development environment

> Typical commands on Linux (Ubuntu).

1. If you don't pick the `git init` option, initialize your local repository:

    ```sh
    git init
    ```

1. Follow the [embedded documentation to set up your development environment](./docs/development/environment.md)
1. Add all files to git index to prepare initial commit:

    ```sh
    git add -A
    ```

1. Run the git hooks to ensure that everything runs OK and to start developing on quality standards:

    ```sh
    pre-commit run -a
    ```

### Try to build documentation locally

1. Have a look to the [plugin's metadata.txt file](gn2qgis/metadata.txt): review it, complete it or fix it if needed (URLs, etc.).
1. Follow the [embedded documentation to build plugin documentation locally](./docs/development/environment.md)

----

## License

Distributed under the terms of the [`GPLv2+` license](LICENSE).
