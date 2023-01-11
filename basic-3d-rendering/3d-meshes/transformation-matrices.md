Transformation matrices (WIP)
=======================

````{tab} With webgpu.hpp
*Resulting code:* [`step054`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step054-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step054-vanilla)
````

Here comes a bit of theory. Don't worry if you don't like math so much: giving a practical meaning to the transformation that we manipulate actually help understanding why we need the math the way it is.

Think of it as a way to learn math thanks to 3D and not the other way around!

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

<p class="align-center">
	<span class="caption-text"><em>The coefficient <span class="math notranslate nohighlight">\(m_{xy}\)</span> is the influence factor of <span class="math notranslate nohighlight">\(y\)</span> on the new coordinate <span class="math notranslate nohighlight">\(x\)</span>.</em></span>
</p>

The $i$-th row describes the $i$-th output coordinate. And on each row, the $j$-th coefficient tells how much of the input's $j$-th coordinate we must mix.

```{note}
The term "linearly" just means that we can only scale and add input coordinates. We cannot for instance multiply $x$ by $y$. In general linear coordinate mixes have the form $\alpha x + \beta y + \gamma z$ where $\alpha$, $\beta$ and $\gamma$ are predefined factors (coefficients of the matrix).
```

Let us see a simple example first: **scaling** a vector consists in applying a diagonal matrix, because the $i$-th coordinate of the scaled vector only depends on the $i$-th coordinate of the input one:

$$
M = \left(
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

// Option B, which is equivalent
let M = transpose(mat3x3<f32>(
// in x    y    z
	1.0,  0.0 , 0.0, // -> out x = 1.0 * x + 0.0 * y + 0.0 * z = x
	0.0, ratio, 0.0, // -> out y = ratio * y
	0.0,  0.0 , 0.5, // -> out z = 0.5 * z
));
position = M * position;
```

```{important}
WGSL (like GLSL and HLSL) expects the arguments of the `mat3x3` constructor to be given **column by column**, despite the fact that they **visually appear in rows** in our source code. Instead of always thinking in mirror, which is quite prone to error, I added a `transpose` operation after the creation of the matrix in order to **flip it along its diagonal**. It does not make a difference for a diagonal matrix like this one, but this is very important in general.
```

```{note}
This choice of notation results from the fact that this operation behaves in many ways **like a multiplication** between two numbers (more details later). But note however that it is **not fully the same**. In particular, we cannot swap the operand and write $x \times M$ (it is called *non-commutative*).
```

```{hint}
The matrix with 1.0 on the diagonal and 0.0 anywhere else is called the **identity matrix** $I$ and has a very special property: it changes nothing ($Ix = x$ for any vector $x$).
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
let R = transpose(mat3x3<f32>(
// in x    y    z
	1.0, 0.0, 0.0, // -> out x = 1.0 * x
	0.0,   c,   s, // -> out y =  c * y + s * z
	0.0,  -s,   c, // -> out z = -s * y + c * z
));
position = R * position;
```

Perfect, this formalism enable us to represent both scaling and rotation!

### Homogeneous coordinates

But what about the translation? There is **good and bad news**. The bad is that a $3 \times 3$ matrix **cannot encode a translation**. The good is that a $4 \times 4$ matrix can!

Let me explain, the matrix tells how to transform a vector by mixing its coordinate with each others. But it does **not allow to add** anything to the mix that is a **constant** value, which does not depend on a coordinate.

```{note}
A matrix represents what is known as a **linear transform**, which also gives its name to the whole field of **linear algebra** by the way. The combination of a linear transform with a translation is called an **affine transform**.
```

How do we address this? We add **an extra coordinate that is meant to always equal 1**. Adding a constant value $t$ now corresponds to adding $t$ times the 4th coordinate and is thus a "legal" mix:

```rust
// Option A
position = position + vec3<f32>(tx, ty, tz);

// Option B, which is equivalent (BUT won't work as-is, see bellow)
let M = transpose(mat4x3<f32>(
// in x    y    z   1.0
	1.0,  0.0, 0.0,  tx, // -> out x = 1.0 * x + tx * 1.0
	0.0,  1.0, 0.0,  ty, // -> out y = 1.0 * y + ty * 1.0
	0.0,  0.0, 1.0,  tz, // -> out z = 1.0 * z + tz * 1.0
));
position = M * vec4<f32>(position, 1.0);
```

```{caution}
Mathematically, the code above makes sense: we can have a non-square matrix that takes an input vector of size 4 and returns an output of size 3. However, **WGSL only supports square matrices** (and so do other shading languages).
```

There would anyway be only little use of non-square matrices, because this prevents us from **chaining transforms**. Instead of returning a vector $(x, y, z)$, we would rather return the vector $(x, y, z, 1.0)$ so that we may apply again another transform. This should be easy:

```rust
// Option A
position = position + vec3<f32>(tx, ty, tz);

// Option B, which is equivalent (and working, now)
let M = transpose(mat4x4<f32>(
// in x    y    z   1.0
	1.0,  0.0, 0.0,  tx, // -> out x = 1.0 * x + tx * 1.0
	0.0,  1.0, 0.0,  ty, // -> out y = 1.0 * y + ty * 1.0
	0.0,  0.0, 1.0,  tz, // -> out z = 1.0 * z + tz * 1.0
	0.0,  0.0, 0.0, 1.0, // -> out w = 1.0
));
position = (M * vec4<f32>(position, 1.0)).xyz;
```

```{note}
Notice how the upper-left $3 \times 3$ quadrant is the identity matrix. This part of the $4 \times 4$ matrix corresponds to the scale and/or rotation (and/or skew).
```

It is important to note that this 4th coordinate is **not just a hack** for storing the translation on top of the linear transform. Everything behaves as if there was a 4th dimension, so all the nice **mathematical properties** about matrices **still hold**.

As long as the last coordinate remains $1.0$, these vectors still represent 3D points. This is called the *homogeneous coordinate* of the point, and we'll understand why better when talking about perspective!

### Composition

The power of matrices gets even crazier when we start to compose them.

```rust
// Object transform
let objectScale = vec3<f32>(1.0, 1.0, 1.0);
let objectTranslate = vec3<f32>(0.25, 0.0, 0.0);
position = position * objectScale + objectTranslate;
```

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
