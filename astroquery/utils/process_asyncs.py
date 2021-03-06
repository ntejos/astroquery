# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Process all "async" methods into direct methods.
"""

from .class_or_instance import class_or_instance
import textwrap
import functools
from .docstr_chompers import remove_returns


def async_to_sync(cls):
    """
    Convert all query_x_async methods to query_x methods

    (see
    http://stackoverflow.com/questions/18048341/add-methods-to-a-class-generated-from-other-methods
    for help understanding)
    """

    def create_method(async_method_name):

        @class_or_instance
        def newmethod(self, *args, **kwargs):
            if 'verbose' in kwargs:
                verbose = kwargs.pop('verbose')
            else:
                verbose = False
            response = getattr(self,async_method_name)(*args,**kwargs)
            result = self._parse_result(response, verbose=verbose)
            self.table = result
            return result

        return newmethod

    methods = cls.__dict__.keys()

    for k in list(methods):
        newmethodname = k.replace("_async","")
        if 'async' in k and newmethodname not in methods:

            newmethod = create_method(k)

            newmethod.fn.__doc__ = async_to_sync_docstr(getattr(cls,k).__doc__)
            #newmethod.__doc__ = async_to_sync_docstr(getattr(cls,k).__doc__) # for using decorator module

            newmethod.fn.__name__ = newmethodname
            newmethod.__name__ = newmethodname

            functools.update_wrapper(newmethod, newmethod.fn)

            setattr(cls,newmethodname,newmethod)

    return cls


def async_to_sync_docstr(doc, returntype='table'):
    """
    Strip of the "Returns" component of a docstr and replace it with "Returns a
    table" code
    """

    object_dict = {'table':'astropy.table.Table',
                   'fits':'astropy.io.fits.PrimaryHDU',
                   'dict':'dict'}

    firstline = "Queries the service and returns a {rt} object.\n".format(rt=returntype)

    vowels = 'aeiou'
    vowels += vowels.upper()
    n = 'n' if object_dict[returntype][0] in vowels else ''

    returnstr = """
                Returns
                -------
                A{n} `{ot}` object
                """.format(n=n,ot=object_dict[returntype]).lstrip('\n')

    # all docstrings have a blank first line
    # strip it out, so that we can prepend
    outlines = remove_returns(doc.lstrip('\n'))

    # then the '' here is to add back the blank line
    newdoc = "\n".join(['',firstline] + outlines + [textwrap.dedent(returnstr)])

    return newdoc
