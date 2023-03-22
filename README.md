<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/eliemichel/LearnWebGPU/main/images/webgpu-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/eliemichel/LearnWebGPU/main/images/webgpu-light.svg">
    <img alt="Learn WebGPU Logo" src="images/webgpu-dark.svg" width="200">
  </picture>

  <a href="https://github.com/eliemichel/LearnWebGPU">LearnWebGPU</a> &nbsp;|&nbsp; <a href="https://github.com/eliemichel/WebGPU-Cpp">WebGPU-C++</a> &nbsp;|&nbsp; <a href="https://github.com/eliemichel/glfw3webgpu">glfw3webgpu</a> &nbsp;|&nbsp; <a href="https://github.com/eliemichel/WebGPU-binaries">WebGPU-binaries</a>
</div>

Learn WebGPU
============

This is the source files of the website [https://eliemichel.github.io/LearnWebGPU](https://eliemichel.github.io/LearnWebGPU).

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

3. And finally build the website by running:

```
make html
```
