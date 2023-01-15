Projection matrix (WIP)
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step055`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step055-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055-vanilla)
````

Now that we are familiar with the concept of matrices, we see how they are used to represent projections, although a **perspective projection** is neither a linear nor an affine transform so it is not exactly what matrices are supposed to represent, mathematically speaking.

Normalized Device Coordinate
----------------------------

TODO NDC

Orthographic projection
-----------------------

TODO

Let's focus on the viewport transform. SO far it looks like this:

```rust
out.position = vec4<f32>(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
```

This can obviously be represented as a matrix:

```rust
let P = transpose(mat4x4<f32>(
	1.0,  0.0,  0.0, 0.0,
	0.0, ratio, 0.0, 0.0,
	0.0,  0.0,  0.5, 0.5,
	0.0,  0.0,  0.0, 1.0,
));

let homogeneous_position = vec4<f32>(position, 1.0);
out.position = P * homogeneous_position;
```

This matrix represents a particular case of **orthographic projection**, namely a basic projection along the XY plane combined with a remapping of the Z coordinate in the range $(0,1)$.

```{note}
The coefficients $0.5$ in the matrix above come from the fact that we want to remap Z coordinate from the $(-1,1)$ to the $(0,1)$ range. In general, if $Z$ coordinates are in range $(n,f)$, we get $z_{\text{out}} = (z - n) / (f - n) = z / (f - n) - n / (f - n)$ and so the coefficients become $p_{zz} = 1 / (f - n)$ and $p_{zw} = - n / (f - n)$.
```

```{caution}
The expected range for the output Z coordinate differs with the graphics API. All modern APIs (DirectX 12, Metal, Vulkan, WebGPU) use $(0,1)$ but OpenGL and WebGL expect $(-1,1)$. The projection matrices have thus slightly different definitions.
```

Perspective projection
----------------------

TODO

GLM
---

TODO

In practice we precompute transforms on CPU.

The [GLM](https://github.com/g-truc/glm) library. Originally designed to be as close as possible to the GLSL syntax. It will look familiar compared to WGSL. Widely used, supported on multiple platforms, battlefield-tested, header-only (so easy to integrate). Stripped down version: [glm.zip](../../data/glm-0.9.9.8-light.zip) (392 KB, as opposed to the 5.5 MB of the official release), to be unzipped in your.

```C++
#define GLM_FORCE_DEPTH_ZERO_TO_ONE // configure depth range (0,1) instead of OpenGL default
#include <glm/glm.hpp> // all types inspired from GLSL
#include <glm/ext.hpp> // utility extensions
```

```CMake
target_include_directories(App PRIVATE .)
```

```{seealso}
The GLM library is focused on vector and matrices up to the 4th dimension. For linear algebra of higher dimensions, I usually turn to the [Eigen](https://eigen.tuxfamily.org) library instead, but we won't need it here.
```

```{caution}
For some reason the developers of the WebGPU standard [deemed the assignments to *swizzles* as "unnecessary"](https://github.com/gpuweb/gpuweb/issues/737), so we cannot compactly write `position.yz = ...`, we need to use this temporary `tmp` variable. I personally find this **very annoying**, and quite limiting for productivity, I hope they might change that eventually...
```

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step055`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step055-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055-vanilla)
````
