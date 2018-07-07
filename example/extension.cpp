
#include <Python.h>

#include "mylib.h"

static
PyObject* call_foo(PyObject *junk)
{
    return PyUnicode_FromString(foo());
}

static
PyObject* call_bar(PyObject *junk)
{
    return PyUnicode_FromString(bar().c_str());
}

static struct PyMethodDef dtest_methods[] = {
    {"foo", (PyCFunction)call_foo, METH_NOARGS,
     "foo() -> unicode\n"
     "call foo"},
    {"bar", (PyCFunction)call_bar, METH_NOARGS,
     "bar() -> unicode\n"
     "call bar"},
    {NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef dtestymodule = {
  PyModuleDef_HEAD_INIT,
    "dsodemo.dtest",
    NULL,
    -1,
    dtest_methods,
};
#endif

#if PY_MAJOR_VERSION >= 3
#  define PyMOD(NAME) PyObject* PyInit_##NAME (void)
#else
#  define PyMOD(NAME) void init##NAME (void)
#endif

extern "C"
PyMOD(dtest)
{
#if PY_MAJOR_VERSION >= 3
        PyObject *mod = PyModule_Create(&dtestymodule);
#else
        PyObject *mod = Py_InitModule("dsodemo.dtest", dtest_methods);
#endif
        if(mod) {
        }
#if PY_MAJOR_VERSION >= 3
    return mod;
#else
    (void)mod;
#endif
}
