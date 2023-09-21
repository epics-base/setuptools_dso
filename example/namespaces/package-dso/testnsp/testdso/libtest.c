
// Snippet more-or-less stolen from https://github.com/mdavidsaver/setuptools_dso/blob/master/example/src/dsodemo/lib/mylib.h
#ifdef _WIN32
#define EXPDECL __declspec(dllexport)
#elif __GNUC__ >= 4
#define EXPDECL __attribute__ ((visibility("default")))
#else
#define EXPDECL
#endif

EXPDECL int getZero(void) {
	return 0;
}

EXPDECL int getOne(void) {
	return 1;
}
