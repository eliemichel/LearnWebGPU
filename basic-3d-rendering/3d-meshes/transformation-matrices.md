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

### A common formalism

Let's summarize the various cases of transforms that we have seen so far:

```rust
var position = in.position;

// Offset the object
position.x += 0.25;

// Rotate the view point
position = vec3<f32>(
	position.x,
	cos(angle) * position.y + sin(angle) * position.z,
	cos(angle) * position.z - sin(angle) * position.y,
);

// Project on the XY plane and apply ratio
out.position = vec4<f32>(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
```

```{note}
There is not much difference between moving the object and moving the viewpoint. The line `position.x += 0.25` can be seen either as moving the object forward along the X axis or moving the viewpoint backwards along the X axis. But as soon as we have multiple objects, this distinction becomes relevant.
```

We can actually unify these transforms under a **common formalism**. First of all, we can see both the object and screen projection as a scaling plus a translation:

```rust
// Object transform
let objectScale = vec3<f32>(1.0, 1.0, 1.0);
let objectTranslate = vec3<f32>(0.25, 0.0, 0.0);
position = position * objectScale + objectTranslate;

// View transform
position = vec3<f32>( /* ... */ );

// Projection/Screen transform
let viewportScale = vec3<f32>(1.0, ratio, 0.5);
let viewportTranslate = vec3<f32>(0.0, 0.0, 0.5);
out.position = vec4<f32>(position * viewportScale + viewportTranslate, 1.0);
```

What about the rotation? We need a bit more than a vector scaling for this, because me mix multiple axes. And this is exactly what a **matrix** is for!

### Matrices

A matrix is a **double entry table** that describes a way to build a new vector by **linearly mixing** the coordinates of an input vector. **Each row** of the matrix lists the mixing coefficients to build one of the output coordinates.

```{image} /images/matrix-light.svg
:align: center
:class: only-light
```

```{image} /images/matrix-dark.svg
:align: center
:class: only-dark
```

The $i$-th row describes the $i$-th output coordinate. And on each row, the $j$-th coefficient tells how much of the input's $j$-th coordinate we must mix.

```{note}
The term "linearly" just means that we can only scale and add input coordinates. We cannot for instance multiply $x$ by $y$. In general linear coordinate mixes have the form $\alpha x + \beta y + \gamma z$ where $\alpha$, $\beta$ and $\gamma$ are predefined factors (coefficients of the matrix).
```

Let us see a simple example first: **scaling** a vector consists in applying a diagonal matrix, because the $i$-th coordinate of the scaled vector only depends on the $i$-th coordinate of the input one:

$$
\left(
\begin{array}{ccc}
1.0 & 0 & 0 \\
0 & \text{ratio} & 0 \\
0 & 0 & 0.5
\end{array}
\right)
$$

The application of the transform described by the matrix to a vector is denoted as a **product**: $b = M \times a$ or just $b = Ma$, and `M * a` in code.

```rust
// Option A
position = position * vec3<f32>(1.0, ratio, 0.5);

// Option B
let M = mat3x3<f32>(
	1.0,  0.0 , 0.0,
	0.0, ratio, 0.0,
	0.0,  0.0 , 0.5,
);
position = M * position;
```

```{note}
This choice of notation results from the fact that this operation behaves in many ways like a multiplication between two numbers (more details later), but note already that it is not fully the same. In particular, we cannot swap the operand and write $x \times M$ (it is called *non-commutative*).
```

For a simple scale, this seems a bit overkill, but it becomes interesting when we want to encode a rotation:

```rust
let c = cos(angle);
let s = sin(angle);

// Option A: Rotate the view point manually
position = vec3<f32>(
	position.x,
	c * position.y + s * position.z,
	c * position.z - s * position.y,
	// ^ beware that y and z are not in the same order here!
);

// Option B: Rotate the view point using a matrix
let R = mat3x3<f32>(
// in x    y    z
	1.0, 0.0, 0.0, // -> out x
	0.0,   c,   s, // -> out y
	0.0,  -s,   c, // -> out z
);
position = R * position;
```

### Homogeneous coordinates

What about the translation? We add a special dimension!

TODO

### Composition

TODO

GLM
---

TODO

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
