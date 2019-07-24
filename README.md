Syditest
========

Syditest is an integrations testing system for Matrix Identity servers, similar
to sytest (although using python rather than perl).

Syditest is a standard set of python unit tests, although is intended to be run
with Twisted's Trial.

To launch the IS server, it attempts to import
`syditest_subject.launcher.SyditestLauncher`. This must be provided separately
for the specific ID server implementation to be tested. See sydent's implementation
for an example of how this works.

Sydent supplies its syditest launcher in the project directory, and so launches
syditest using:

```
PYTHONPATH="/path/to/sydent" trial syditest
```

...which puts the launcher on the PYTHONPATH and invokes trial on syditest (which
is assumed to already be on sys.path).
