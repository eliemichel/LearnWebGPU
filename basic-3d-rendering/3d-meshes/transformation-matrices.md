Transformation matrices (WIP)
=======================

````{tab} With webgpu.hpp
*Resulting code:* [`step054`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step054-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054-vanilla)
````

TODO

A bit of theory here.

Linear algebra
--------------

Let's get back a moment to our 2D scene. Remember this part of the shader?

```rust
let offset = vec2<f32>(-0.6875, -0.463);
let position = vec2<f32>(in.position.x + offset.x, (in.position.y + offset.y) * ratio);
```

We could also write it this way:

```rust
let sceneTranslate = vec2<f32>(-0.6875, -0.463);
let viewportScale = vec2<f32>(1.0, 640.0 / 480.0);
let position = viewportScale * (in.position.xy + sceneTranslate);
```

Imagine we would also like to rotate the object.

```rust
let sceneTranslate = vec2<f32>(-0.6875, -0.463);
let viewportScale = vec2<f32>(1.0, 640.0 / 480.0);
let c = cos(uMyUniforms.time);
let s = sin(uMyUniforms.time);
let sceneRotate = mat2x2<f32>(c, s, -s, c);
let position = viewportScale * sceneRotate * (in.position.xy + sceneTranslate);
```

We can actually unify these transforms under a common formalism. First of all, we can see the scaling as a multiplication by a diagonal matrix:

```rust
let sceneTranslate = vec2<f32>(-0.6875, -0.463);
let viewportTransform = mat2x2<f32>(
	1.0, 1.0,
	1.0, 640.0 / 480.0
);
let c = cos(uMyUniforms.time);
let s = sin(uMyUniforms.time);
let sceneRotate = mat2x2<f32>(c, s, -s, c);
let position = viewportTransform * sceneRotate * (in.position.xy + sceneTranslate);
```

What about the translation? We add a special dimension!

GLM
---

The [GLM](https://github.com/g-truc/glm) library. Originally designed to be as close as possible to the GLSL syntax. It will look familiar compared to WGSL. Widely used, supported on multiple platforms, battlefield-tested, header-only (so easy to integrate). Stripped down version: [glm.zip](../../data/glm-0.9.9.8-light.zip) (392 KB, as opposed to the 5.5 MB of the official release), to be unzipped in your.

```C++
#include <glm/glm.hpp> // all types inspired from GLSL
#include <glm/ext/...> // utility extensions
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
*Resulting code:* [`step054`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step054-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054-vanilla)
````
