
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

static
PyObject* call_check_myvar(PyObject *junk, PyObject *args, PyObject *kws)
{
    const char* names[] = {"address", NULL};
    unsigned long long addr;
    if(!PyArg_ParseTupleAndKeywords(args, kws, "K", (char**)names, &addr)) {
        return NULL;
    }
    if(addr==(size_t)&myvar) {
        Py_RETURN_NONE;
    } else {
        return PyErr_Format(PyExc_ValueError, "%p != %llu", &myvar, addr);
    }
}

static struct PyMethodDef dtest_methods[] = {
    {"foo", (PyCFunction)call_foo, METH_NOARGS,
     "foo() -> unicode\n"
     "call foo"},
    {"bar", (PyCFunction)call_bar, METH_NOARGS,
     "bar() -> unicode\n"
     "call bar"},
    {"check_myvar", (PyCFunction)call_check_myvar, METH_VARARGS | METH_KEYWORDS,
     "check_myvar(address=int)\n"
     "Check if address==&myvar"},
    {NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef dtestymodule = {
  PyModuleDef_HEAD_INIT,
    "dsodemo.ext.dtest",
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
        PyObject *mod = Py_InitModule("dsodemo.ext.dtest", dtest_methods);
#endif
        if(mod) {
        }
#if PY_MAJOR_VERSION >= 3
    return mod;
#else
    (void)mod;
#endif
}
