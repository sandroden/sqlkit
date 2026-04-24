# -*- coding: utf-8 -*-
"""
.. _appypod:

OpenOffice Utils via ``appy.pod``
=================================

.. note:: Nuovo

   Questo modulo rimpiazza :ref:`ooutils`

Il modulo utilizza la libreria appy.pod_ per generare documenti a partire da
un template in formato ``.odt``.

Esempio d'uso::

    from django.http import HttpResponse

    from jmb.core.utils.appypod import AppyPodTemplate

    def example_view_pdf(request):
        context = dict(first_name="<name>", last_name="<last_name>")
        appy_pod_template = AppyPodTemplate('admin/fax/cover.odt', context)
        return HttpResponse(template.render(), mimetype="application/pdf")

    def example_view_odt(request):
        context = dict(first_name="<name>", last_name="<last_name>")
        appy_pod_template = AppyPodTemplate('admin/fax.cover.odt', context)
        return HttpResponse(template.render(file_type="odt"),
                            mimetype="application/vnd.oasis.opendocument.text")

conversion
----------

A conversion utility is provided that uses OpenOffice/LibreOffice to
convert among possible formats. Tipical usage allows to convert bunch
of documents toghether, passing both patterns of directory to
transverse and patterns::

   from jmb.core.utils import appypod

   appypod.convert(file_names='/tmp/report.odt', result_type='doc')
   appypod.convert(tree='/home/data/fax', file_names="*doc")


API
---

.. autoclass:: AppyPodTemplate
   :members:

.. autofunction:: convert

.. _appy.pod: http://appyframework.org/

"""
import os
import glob
import fnmatch
import logging
from tempfile import NamedTemporaryFile

import appy.pod
from appy.pod.converter import Converter, ConverterError
from appy.shared.utils import executeCommand
from appy.pod.renderer import Renderer

logger = logging.getLogger('sqlkit')

# inject_app_defaults does not work here.
PY_PATH = '/usr/bin/python3'
# PY_PATH = getattr(settings, 'JMB_OOO_UNO_PYTHON_PATH', None)
# OOO_PORT = getattr(settings, 'JMB_OOO_SERVER_PORT', 8100)

class AppyPodTemplate():

    """
    Interface to get handle templates in .odt, .ods
    """

    def __init__(self, template=None, context=None, port=8100, server='localhost'):
        """
        Object init function.

        :param template: (string) template file to render. Std django search is performed
        :param context: context to be used on template rendering
        :param port: the port to connect to soffice server (default: 8100)
        :param server: the server to connect to soffice server (currently unused)
        """
        self.set_template(template)
        self.context = context
        self.port = port
        self.server = server

    def set_template(self, template):
        """
        Set template

        :param template: (string) template file to render. Std django search is applied
        """
        assert os.path.isabs(template), "'%s' is not the path of a template"
        self.template = template

    def render(self, file_type="pdf"):
        """
        Instance render function.

        :param file_type: output file extension
        :return: generated file stream if created, else None
        """
        result = None
        output = None
        with NamedTemporaryFile('rwb', suffix='.%s' % file_type, delete=False) as f:
            output = f.name
            renderer = Renderer(
                self.template, self.context, output,
                ooPort=self.port,
                overwriteExisting=True,
                pythonWithUnoPath=PY_PATH,
            )
            renderer.run()
        result = open(output, 'rb').read()
        if output and os.path.exists(output):
            os.unlink(output)
        return result

    def save_as(self, output_path):
        """
        Save the template into file

        :arg output_path: the output path
        :return: the open handler of the generated file
        """
        file_type = os.path.splitext(output_path)[1].lstrip('.')
        f = open(output_path, 'w')
        f.write(self.render(file_type=file_type))
        f.flush()
        return f

    def close(self):
        return

def convert(name_pattern, result_type='pdf', tree=None):
    """Call LibreOffice in server mode to convert or update the result.

    :arg name_pattern: the file name to be converted. A list,
         a set, a tuple of filenames or a glob pattern is accepted. If `tree` is defined
         `name_pattern` is interpreted as a pattern.
    :arg file_type: the resul_type desired (default: pdf)
    :arg tree: if tree is defined the whole directory is traversed for pattern
         and name_pattern is interpreted as a pattern
    """

    if tree:
        file_names = recursive_glob(tree, name_pattern)
    elif not isinstance(name_pattern, (list, tuple, set)):
        if os.path.exists(name_pattern):
            file_names = [name_pattern]
        else:
            file_names = glob.glob(name_pattern)
    else:
        file_names = name_pattern

    output_files = []
    for file_name in file_names:
        name, ext = os.path.splitext(file_name)

        if not PY_PATH:
            try:
                Converter(file_name, result_type, OOO_PORT).run()
            except ConverterError, ce:
                raise PodError(CONVERT_ERROR % str(ce))
        else:
            if not os.path.isfile(PY_PATH):
                raise PodError(PY_PATH_NOT_FILE % PY_PATH)
            if file_name.find(' ') != -1:
                qResultName = '"%s"' % file_name
            else:
                qResultName = file_name
            convScript = '%s/converter.py' % os.path.dirname(appy.pod.__file__)
            if convScript.find(' ') != -1:
                convScript = '"%s"' % convScript
            cmd = '%s %s %s %s -p%d' % \
                  (PY_PATH, convScript, qResultName, result_type, OOO_PORT)
            loOutput = executeCommand(cmd)

        output_files += ["%s.%s" % (name, result_type)]
    return output_files

def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results
