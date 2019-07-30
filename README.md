Syditest
========

Syditest is an integration testing system for Matrix Identity servers, similar
to sytest (although using python rather than perl).

To launch the IS server, it attempts to import
`syditest_subject.launcher.SyditestLauncher`. This must be provided separately
for the specific ID server implementation to be tested. See sydent's implementation
for an example of how this works.

Sydent supplies its syditest launcher in the project directory, so to launch
syditest on sydent you would run:

```
PYTHONPATH="/path/to/sydent" trial syditest
```

...which puts the launcher on the PYTHONPATH and invokes trial on syditest (which
is assumed to already be on sys.path).
