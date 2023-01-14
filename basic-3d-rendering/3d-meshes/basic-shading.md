Basic shading (WIP)
=============

````{tab} With webgpu.hpp
*Resulting code:* [`step056`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step056)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step056-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step056-vanilla)
````

TODO

Here we get an intuition about how to shade a scene, but do not follow a physically based approach.

To better see the impact of our shading, we give the same base color to the whole pyramid. In `pyramid.txt`, replace the color of the tip with the same white as other points (remember that the green color comes from the shader and its color uniform):

```
# And the tip of the pyramid
+0.0 +0.0 +0.5    1.0 1.0 1.0
                  ^^^^^^^^^^^ This was 0.5
```

Theory
------

Normal
------

We add a new attribute.

```
[points]
# We add normal vector (nx, ny, nz)
# x    y    z       nx   ny  nz     r   g   b

# The base
-0.5 -0.5 -0.3     0.0 -1.0 0.0    1.0 1.0 1.0
+0.5 -0.5 -0.3     0.0 -1.0 0.0    1.0 1.0 1.0
+0.5 +0.5 -0.3     0.0 -1.0 0.0    1.0 1.0 1.0
-0.5 +0.5 -0.3     0.0 -1.0 0.0    1.0 1.0 1.0

# Face sides have their own copy of the vertices
# because they have a different normal vector.
-0.5 -0.5 -0.3  0.0 -0.848 0.53    1.0 1.0 1.0
+0.5 -0.5 -0.3  0.0 -0.848 0.53    1.0 1.0 1.0
+0.0 +0.0 +0.5  0.0 -0.848 0.53    1.0 1.0 1.0

+0.5 -0.5 -0.3   0.848 0.0 0.53    1.0 1.0 1.0
+0.5 +0.5 -0.3   0.848 0.0 0.53    1.0 1.0 1.0
+0.0 +0.0 +0.5   0.848 0.0 0.53    1.0 1.0 1.0

+0.5 +0.5 -0.3   0.0 0.848 0.53    1.0 1.0 1.0
-0.5 +0.5 -0.3   0.0 0.848 0.53    1.0 1.0 1.0
+0.0 +0.0 +0.5   0.0 0.848 0.53    1.0 1.0 1.0

-0.5 +0.5 -0.3  -0.848 0.0 0.53    1.0 1.0 1.0
-0.5 -0.5 -0.3  -0.848 0.0 0.53    1.0 1.0 1.0
+0.0 +0.0 +0.5  -0.848 0.0 0.53    1.0 1.0 1.0

[indices]
# Base
 0  1  2
 0  2  3
# Sides
 4  5  6
 7  8  9
10 11 12
13 14 15
```

```
bool success = loadGeometry(RESOURCE_DIR "/pyramid.txt", pointData, indexData, 6);
                                                                               ^ This was a 3
```

```C++
/**
 * A structure that describes the data layout in the vertex buffer
 * We do not instantiate it but use it in `sizeof` and `offsetof`
 */
struct VertexAttributes {
	std::array<float, 3> position;
	std::array<float, 3> normal;
	std::array<float, 3> color;
};

// [...]

requiredLimits.limits.maxVertexAttributes = 3;
//                                          ^ This was a 2

// [...]

std::vector<VertexAttribute> vertexAttribs(3);
//                                         ^ This was a 2

// Position attribute
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = VertexFormat::Float32x3;
vertexAttribs[0].offset = offsetof(VertexAttributes, position);

// Normal attribute
vertexAttribs[1].shaderLocation = 1;
vertexAttribs[1].format = VertexFormat::Float32x3;
vertexAttribs[1].offset = offsetof(VertexAttributes, normal);

// Color attribute
vertexAttribs[2].shaderLocation = 2;
vertexAttribs[2].format = VertexFormat::Float32x3;
vertexAttribs[2].offset = offsetof(VertexAttributes, color);

// [...]

vertexBufferLayout.arrayStride = sizeof(VertexAttributes);
//                               ^^^^^^^^^^^^^^^^^^^^^^^^ This was 6 * sizeof(float)
```

```rust
struct VertexInput {
	@location(0) position: vec3<f32>,
	@location(1) normal: vec3<f32>,
	@location(2) color: vec3<f32>,
};
```

Shading
-------

### Light direction

Shading occurs in the **fragment shader**, so we need to forward the normal attribute:

```rust
struct VertexOutput {
	@builtin(position) position: vec4<f32>,
	@location(0) color: vec3<f32>,
	@location(1) normal: vec3<f32>, // <--- Add a normal output
};

// [...]

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	// [...]
	// Forward the normal
	out.normal = in.normal;
	return out;
}
```

Let's do some experiments with this normal:

```rust
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let color = in.color * in.normal.x;
	// [...]
}
```

```{figure} /images/pyramid-axis-lights.png
:align: center
:class: with-shadow
Multiplying the color by the normal axes creates axis-aligned directional lights.
```

To apply a lighting coming from an arbitrary direction, we again use a linear combination of the different axes:

```rust
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let shading = 0.5 * in.normal.x - 0.9 * in.normal.y + 0.1 * in.normal.z;
	let color = in.color * shading;
	// [...]
}
```

```{figure} /images/pyramid-first-light.png
:align: center
:class: with-shadow
Mixing multiple axes can create a directional light coming from any direction.
```

The coefficient $(0.5, -0.9, 0.1)$ are in fact the **light direction** This combination is called a **dot product**:

```rust
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let lightDirection = vec3<f32>(0.5, -0.9, 0.1);
	let shading = dot(lightDirection, in.normal);
	let color = in.color * shading;
	// [...]
}
```

```{note}
The term "direction" suggests that this is a **normalized** vector (i.e., a vector whose length is $1$. Here we actually encode the direction plus the **intensity** of the light, through the magnitude (i.e., length) of the vector.
```

### Multiple lights

Adding multiple light sources is as simple as summing the contribution of multiple directions. One important thing though:

```rust
let shading = max(0.0, dot(lightDirection, in.normal));
//            ^^^^^^^^ This clamps negative values to 0.0
```

```rust
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let lightDirection1 = vec3<f32>(0.5, 0.1, -0.9);
	let lightDirection2 = vec3<f32>(-0.2, 0.3, 0.4);
	let shading1 = max(0.0, dot(lightDirection1, in.normal));
	let shading2 = max(0.0, dot(lightDirection2, in.normal));
	let shading = shading1 + shading2;
	let color = in.color * shading;
	// [...]
}
```

```rust
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let lightColor1 = vec3<f32>(1.0, 0.9, 0.6);
	let lightColor2 = vec3<f32>(0.6, 0.9, 1.0);
	// [...]
	let shading = shading1 * lightColor1 + shading2 * lightColor2;
	let color = in.color * shading;
	// [...]
}
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/shading01.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Two colored lights.</span></p>
	</figcaption>
</figure>

Transform
---------

In the previous part, the light direction changes with the object's orientation. To apply a fixed global lighting, we need to transform the normal wrt. the model transform, but not the view transform (hence the distinction).

```rust
// in Vertex shader
out.normal = (modelMatrix * vec4<f32>(in.normal, 0.0)).xyz;

// [...]

// in Fragment shader
let normal = normalize(in.normal);
// (and replace in.normal with normal in shading1/shading2)
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../_static/shading02.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Fixed light direction.</span></p>
	</figcaption>
</figure>

Conclusion
----------

We will see a much more accurate material model in the [Lighting and material](/basic-3d-rendering/lighting-and-material.md) chapter.

````{tab} With webgpu.hpp
*Resulting code:* [`step056`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step056)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step056-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step056-vanilla)
````
