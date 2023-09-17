Custom Extensions
=================

When using WebGPU in a non-Web context, there is no reason to be limited by the Web requirements. This chapter gives an overview of how to add support for new device features through WebGPU's extension mechanism.

```{note}
I do not use the [`webgpu.hpp`](https://github.com/eliemichel/WebGPU-Cpp) helper here as the extension file must define a C API. The `webgpu.hpp` wrapper can then easily be generalized to your own custom extension by using [`generator.py`](https://github.com/eliemichel/WebGPU-Cpp#custom-generation).
```

Contents
--------

```{toctree}
:titlesonly:

mechanism
with-wgpu-native
with-dawn
```
