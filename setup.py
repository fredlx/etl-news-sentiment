# (DONE) setup.py
from setuptools import setup, Extension
from Cython.Build import cythonize

# $ python3 setup.py build_ext --inplace (to recompile .pyx files)
# will implement build/, .so and .c files

ext_modules = [
    Extension(
        name="transformers_project.resamplers.resample_sentiment_cython",
        sources=["transformers_project/resamplers/resample_sentiment_cython.pyx"],
    )
]

setup(
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={'language_level': "3"}
    )
)