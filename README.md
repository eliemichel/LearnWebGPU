Learn WebGPU
============

![Fancy logo](images/webgpu-dark.svg#gh-dark-mode-only)
![Fancy logo](images/webgpu-light.svg#gh-light-mode-only)

This is the source files of the website learnwgpu.com.

Building
--------

Building the website requires Python.

1. It is recommended, but not mandatory, to set up a virtual Python environment:

```
$ virtualenv venv
$ venv/Scripts/activate
```

2. Then install Python packages

```
pip install -r requirements.txt
```

2. And finally build the website by running:

```
make html
```
