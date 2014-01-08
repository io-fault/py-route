=======
Project
=======

Filesystem and Python module path interfaces.

Introduction
============

Routes provides a high-level interface for interacting with Python modules and the local
filesystem. It describes the concept of a "route" which is merely the sequence of
identifiers used to access the :term:`selection`.

Structure
=========

Routes implements two :py:class:`.abstract.Route` classes: the :py:class:`.lib.File`
and the :py:class:`.lib.Import`:

 File
  A pointer to a filesystem entity.

 Import
  A pointer to a Python module entity.

Conventions
===========

Route objects are a conflation of Route manipulation operations and :term:`selection`
interaction. In order to minimize confusion as to whether or not an attribute
works with the Selection or the Route, classes will tend to use the kind of attributes
according to:

 properties
  A property on a Route will only work with the Route. While they may create a new Route,
  no side effects in the :term:`Subject Space` or :term:`Selection` interaction will occur
  by accessing a property on a :py:class:`.abstract.Route`.

 classmethods
  Instantiation of Routes is normally performed through class methods. If the classmethod
  queries the :term:`Subject Space`, it will usually say so in the method's docstring.

 methods
  Almost always queries the :term:`Subject Space`. For :py:class:`.lib.File`
  instances, methods will usually request information about the :term:`Selection` from the
  kernel using standard Python interfaces.

Requirements
============

Routes only requires a Python interpreter that exposes access to the operating system's
filesystem and import facilities.

Defense
=======

File management and module hierarchy introspection is a pain using only the builtin tools.
