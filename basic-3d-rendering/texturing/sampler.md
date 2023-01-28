Sampler (WIP)
=======

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````

The `textureLoad` function that we used in our shader accesses the texture data almost as if it was a basic buffer. It does not benefit from the interpolation and mip level selection features that the GPU is capable of.

To **sample** values from a texture with all these capabilities, we define another resource called a **sampler**. We set it up to query the texture data in the way we'd like and then use the `textureSample` function in our shader.

Sampler creation
----------------

```C++

```

```C++
requiredLimits.limits.maxSampledTexturesPerShaderStage = 1;
requiredLimits.limits.maxSamplersPerShaderStage = 1;
```

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step070`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step070-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step070-vanilla)
````
