#ifndef MYLIB_H
#define MYLIB_H

#ifdef _WIN32
# ifdef BUILD_MYLIB
#  define MYLIB_API __declspec(dllexport)
# else
#  define MYLIB_API __declspec(dllimport)
# endif
#elif __GNUC__ >= 4
/* allow use of -fvisibility=hidden -fvisibility-inlines-hidden */
# define MYLIB_API __attribute__ ((visibility("default")))
#else
# define MYLIB_API
#endif

#ifdef __cplusplus

#include <string>

extern "C" {
#endif

MYLIB_API extern int myvar;

MYLIB_API const char* foo(void);

#ifdef __cplusplus
}

MYLIB_API std::string bar(void);

#endif

#endif
