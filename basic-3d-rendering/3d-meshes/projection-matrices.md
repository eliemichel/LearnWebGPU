Projection matrices (WIP)
===================

````{tab} With webgpu.hpp
*Resulting code:* [`step055`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step055-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step055-vanilla)
````

Now that we are familiar with the concept of matrices, we see how they are used to represent projections, although a **perspective projection** is neither a linear nor an affine transform so it is not exactly what matrices are supposed to represent, mathematically speaking.

We also present in a second part the typical way of managing transform and projection matrices from the C++ code.

Orthographic projection
-----------------------

What have we been doing so far regarding the projection of the 3D scene onto our 2D screen? The $x$ and $y$ coordinates of the output position `out.position` is mapped to the window coordinates, and the $z$ coordinate does not affect the pixel position of our geometry, so this is **an orthographic projection along the Z axis**:

```rust
out.position = vec4<f32>(position.x, position.y * ratio, position.z * 0.5 + 0.5, 1.0);
```

Remember that we had to remap the $z$ coordinate to the range $(0,1)$, because anything outside this range is **clipped out**, the same way anything outside the range $(-1,1)$ along the $x$ and $y$ axes falls outside the window.

```{image} /images/clip-space-light.svg
:align: center
:class: only-light
```

```{image} /images/clip-space-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>The normalized clipping volume.</em></span>
</p>

We call this the **clipping volume**. Only the geometry that lies inside this volume after the vertex shader can produce visible fragments.

```{caution}
The expected range for the output $z$ coordinate differs with the graphics API. All modern APIs (DirectX 12, Metal, Vulkan, WebGPU) use $(0,1)$ but OpenGL and WebGL expect $(-1,1)$. The projection matrices have thus slightly different definitions.
```

Of course this orthographic projection can be easily represented as a matrix:

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

Note that the coefficients $0.5$ in the matrix above come from the fact that we want to remap Z coordinate from the range $(-1,1)$. In general, if the $z$ coordinates of our model are in range $(n,f)$, we get $z_{\text{out}} = \frac{z - n}{f - n} = \frac{z}{f - n} - \frac{n}{f - n}$ and so the coefficients become $p_{zz} = \frac{1}{f - n}$ and $p_{zw} = \frac{- n}{f - n}$.

We can also change the range of view by dividing the XY size of the scene to fit a larger part of it in the view frustum.

```rust
// A more generic expression of an orthographic projection matrix
let near = -1.0;
let far = 1.0;
let scale = 1.0;
let P = transpose(mat4x4<f32>(
	1.0 / scale,      0.0,           0.0,                  0.0,
	    0.0,     ratio / scale,      0.0,                  0.0,
	    0.0,          0.0,      1.0 / (far - near), -near / (far - near),
	    0.0,          0.0,           0.0,                  1.0,
));
```

Perspective projection
----------------------

A perspective projection is (more or less) the projection that occurs in a camera or a human eye. Instead of projecting the scene onto a plane, it **projects onto a single point**, called the **focal point**.

The pixels of the screen correspond to different **incoming directions** from which elements of geometry are projected.

```{image} /images/perspective-light.svg
:align: center
:class: only-light
```

```{image} /images/perspective-dark.svg
:align: center
:class: only-dark
```

Unfortunately, a perspective projection is **not a linear transform**: if we want to map the perspective view frustum to the normalized clip space described above, we **need to divide** the XY position by the $z$ coordinate:

```{image} /images/perspective2-light.svg
:align: center
:class: only-light
```

```{image} /images/perspective2-dark.svg
:align: center
:class: only-dark
```

The points $A$ and $C$ project along the same direction, so they should have the same $y_\text{out}$ coordinate. At the same time, the points $A$ and $B$ have the same input $y$ coordinate.

The thing is that they have **different depths**, and as we know **objects that are further away look smaller**. This is modeled by a division by the depth:

$$
y_\text{out} = \frac{y}{z}
$$

Since $A$ and $B$ have different $z$, they end up at different $y_\text{out}$ coordinates, which means we see them in slightly different directions (i.e., different pixels in the final image).

We can try this out:

```rust
// [...] apply model and view transform, but not the orthographic projection

// We move the view point so that all Z coordinates are > 0
// (this did not make a difference with the orthographic projection
// but does now.)
let z_eye = -2.0;
position.z = position.z - z_eye;

// We divide by the Z coord
position.x /= position.z;
position.y /= position.z;

// Apply the orthographic matrix for remapping Z and handling the ratio
let near = -1.0 - z_eye;
let far = 1.0 - z_eye;
let P = /* ... */;
out.position = P * vec4<f32>(position, 1.0);
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/perspective.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Our first perspective.</span></p>
	</figcaption>
</figure>

This works, but we can make it cleaner.

TODO

```rust
position.x /= 0.5 * position.z;
position.y /= 0.5 * position.z;
```

```{image} /images/perspective3-light.svg
:align: center
:class: only-light
```

```{image} /images/perspective3-dark.svg
:align: center
:class: only-dark
```

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
