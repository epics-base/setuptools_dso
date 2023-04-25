#include <Python.h>

#include "mylib.h"

static
PyObject* call_dsodemo_foo(PyObject *junk)
{
    return PyUnicode_FromString(foo());
}

static
PyObject* call_dsodemo_bar(PyObject *junk)
{
    return PyUnicode_FromString(bar().c_str());
}

static struct PyMethodDef use_dsodemo_methods[] = {
    {"dsodemo_foo", (PyCFunction)call_dsodemo_foo, METH_NOARGS,
     "dsodemo_foo() -> unicode\n"
     "call foo"},
    {"dsodemo_bar", (PyCFunction)call_dsodemo_bar, METH_NOARGS,
     "dsodemo_bar() -> unicode\n"
     "call bar"},
    {NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef use_dsodemo_module = {
  PyModuleDef_HEAD_INIT,
    "use_dsodemo.ext",
    NULL,
    -1,
    use_dsodemo_methods,
};
#endif

#if PY_MAJOR_VERSION >= 3
#  define PyMOD(NAME) PyObject* PyInit_##NAME (void)
#else
#  define PyMOD(NAME) void init##NAME (void)
#endif

extern "C"
PyMOD(ext)
{
#if PY_MAJOR_VERSION >= 3
        PyObject *mod = PyModule_Create(&use_dsodemo_module);
#else
        PyObject *mod = Py_InitModule("use_dsodemo.ext", use_dsodemo_methods);
#endif
        if(mod) {
        }
#if PY_MAJOR_VERSION >= 3
    return mod;
#else
    (void)mod;
#endif
}
