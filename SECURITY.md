# Security Policy

## Supported versions

The latest stable release on the QGIS plugin repository is supported. Security
fixes are released as a new patch/minor version; published tags are never moved.

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

Report it privately to the maintainer via the contact in
[`metadata.txt`](metadata.txt) or GitHub's private vulnerability reporting for
<https://github.com/geociencio/freehand-digitize>.

Include:

- affected version and QGIS version;
- steps to reproduce;
- impact and any suggested fix;
- whether the issue is already public.

You will receive an acknowledgement and a coordination plan. Please allow time
for a fix before disclosure.

## Scope

The plugin has no network services and no runtime Python dependencies. Relevant
areas are file handling, QGIS edit operations, packaging and CI supply chain.
