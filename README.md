## Introduction

This projects implements a dashboard web-application for the results of clinical quality indicators which are produced in the INDICATE project.

## Requirements

* Python 3.10+ recommended

* Access to the INDICATE data exchange server

## Installation

```bash
pip install -r requirements.txt
```

## Usage

TODO: explain debug mode (once configuration is implemented)
TODO: explain data exchange server configuration (once configuration is implemented)

```bash
LISTEN_ADDRESS=127.0.0.1 LISTEN_PORT=5000 python app.py
# then open http://127.0.0.1:5000
```

## Licenses

Unless stated otherwise for specific files, the code in this repository is made available under the Apache 2.0 license - see `COPYING` for the license text.

This project uses the following libraries and assets:

* Javascript library simple-datatables

  Files from the simple-datatables library have been copied into this project as `static/SimpleDataTables.css` and `static/SimpleDataTables.js`.

  The simple-datatables library is made available under the LGPLv3 license at https://github.com/fiduswriter/simple-datatables.

* "monitoring-health" SVG icon

  The SVG image "monitoring-health" has been copied into this project as `static/favicon.svg`.

  The "monitoring-health" SVG image by Denali Design is made available under the MIT License at https://www.svgrepo.com/svg/445892/monitoring-health.
