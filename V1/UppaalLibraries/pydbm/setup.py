from distutils.core import setup, Extension

setup(
        name = 'pydbm',
        version = '0.1',
        package_dir = {'pydbm': ''},
        packages = ['pydbm'],
        ext_modules = [
            Extension("_udbm_int", 
            sources=["udbm_int.i"], 
            swig_opts=['-c++'],
            include_dirs=['/usr/local/uppaal/include'],
            libraries=['udbm'],
            library_dirs=['/usr/local/uppaal/lib'],
            extra_compile_args=["-fpermissive"]
            )
        ]

     )
