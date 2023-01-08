A simple example (WIP)
================

````{tab} With webgpu.hpp
*Resulting code:* [`step050`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step050-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-vanilla)
````

Let's dive into what you are quite likely here for: rendering **3D shapes**!

```{note}
I rolled back the part of the code about dynamic uniforms for now. I also set the `offset` to `vec2<f32>(0.0)`;
```

Switching to 3D data
--------------------

The first thing we need is a 3rd column in our point position!

Here is a simple shape that you can save in `resources/pyramid.txt`:

```
[points]
# We add a Z coordinate
# x   y   z      r   g   b

# The base
-0.5 -0.5 -0.3    1.0 1.0 1.0
+0.5 -0.5 -0.3    1.0 1.0 1.0
+0.5 +0.5 -0.3    1.0 1.0 1.0
-0.5 +0.5 -0.3    1.0 1.0 1.0

# And the tip of the pyramid
+0.0 +0.0 +0.5    0.5 0.5 0.5

[indices]
# Base
 0  1  2
 0  2  3
# Sides
 0  1  4
 1  2  4
 2  3  4
 3  0  4
```

Of course we need to adapt our `loadGeometry` function to handle this extra dimension. I added a `int dimensions` argument that should be either 2 or 3 depending on whether we are in 2D or 3D:

```C++
bool loadGeometry(const fs::path& path, std::vector<float>& pointData, std::vector<uint16_t>& indexData, int dimensions) {
	// [...]

	// Get x, y, z, r, g, b
	for (int i = 0; i < dimensions + 3; ++i) {
	//                  ^^^^^^^^^^^^^^ This was a 5

	// [...]
}
```

We can now load the geometry as follows:

```C++
loadGeometry(RESOURCE_DIR "/pyramid.txt", pointData, indexData, 3 /* dimensions */);
```

As a consequence of this new dimension, we need to update the vertex buffer stride, the position attribute format and the color attribute offset:

```C++
// Position attribute
vertexAttribs[0].format = VertexFormat::Float32x3;
//                                              ^ This was a 2

// Color attribute
vertexAttribs[1].offset = 3 * sizeof(float);
//                        ^ This was a 2

// The buffer stride
vertexBufferLayout.arrayStride = 6 * sizeof(float);
//                               ^ This was a 5
```

And don't forget to update the vertex input struct in the **shader**!

```rust
struct VertexInput {
	@location(0) position: vec3<f32>,
	//                        ^ This was a 2
	@location(1) color: vec3<f32>,
};
```

Now it kinda works, we can guess a pyramid is here, but I wouldn't call it 3D yet. And adding `in.position.z` to `out.position.z` does not change anything so far:

```{figure} /images/pyramid-base.png
:align: center
:class: with-shadow
The pyramid... seen from above, with no perspective.
```

Basic transform
---------------

Before diving more properly into the *transform* process, let us convince ourselves that **we actually draw 3D data** with a simple rotation.

TODO

Rotation in the screen plane:

```rust
var position = in.position;
var c = cos(uMyUniforms.time);
var s = sin(uMyUniforms.time);
let tmp = mat2x2(c, s, -s, c) * position.xy;
position.x = tmp.x;
position.y = tmp.y;
out.position = vec4<f32>(position.x, position.y * ratio, 0.0, 1.0);
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/pyramid-rxy.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Rotation in the XY plane (the screen)</span></p>
	</figcaption>
</figure>

```{figure} /images/rotation.png
:align: center
:class: with-shadow
Rotation & trigonometry
```

Now let's rotate along a different axis, in the YZ plane instead of the XY:

```rust
let tmp = mat2x2(c, s, -s, c) * position.yz;
position.y = tmp.x;
position.z = tmp.y;
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/pyramid-ryz.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Rotation in the YZ plane</span></p>
	</figcaption>
</figure>

```{note}
I intentionally set a different color for the tip of the pyramid so that we can see better. This will be better addressed when introducing a basic **shading**.
```

```{caution}
For some reason the developers of the WebGPU standard [deemed the assignments to *swizzles* as "unnecessary"](https://github.com/gpuweb/gpuweb/issues/737), so we cannot compactly write `position.yz = ...`, we need to use this temporary `tmp` variable. I personally find this **very annoying**, and quite limiting for productivity, I hope they might change that eventually...
```

```{figure} /images/pyramid-zissue.png
:align: center
:class: with-shadow
There is something wrong with the depth.
```

Conclusion
----------

We thus see the 3 important things to address to switch to 3D:

 - Depth fighting
 - Better transform
 - Shading

````{tab} With webgpu.hpp
*Resulting code:* [`step050`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step050-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-vanilla)
````
