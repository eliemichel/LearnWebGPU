Texture mapping
===============

````{tab} With webgpu.hpp
*Resulting code:* [`step065`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step065)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step065-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step065-vanilla)
````

In the previous chapter we used the screen pixel coordinate to decide which texel from the image to load (`in.position` in the fragment shader is the fragment's screen coordinates).

If our geometry is no longer a full screen quad, this is not really what we expect. Let us switch back to a perspective projection, and use the handy `glm::lookAt` function to get an interesting point of view:

```C++
uniforms.modelMatrix = mat4x4(1.0);
uniforms.viewMatrix = glm::lookAt(vec3(-0.5f, -2.5f, 2.0f), vec3(0.0f), vec3(0, 0, 1)); // the last argument indicates our Up direction convention
uniforms.projectionMatrix = glm::perspective(45 * PI / 180, 640.0f / 480.0f, 0.01f, 100.0f);
```

```{figure} /images/wrong-mapping.png
:align: center
:class: with-shadow
The texture does not "follow" the geometry.
```

Texel coordinates
-----------------

How to address this? By computing **texel coordinates** in the vertex shader and letting the rasterizer interpolate it for each fragment.

```rust
struct VertexOutput {
	// [...]
	@location(2) texelCoords: vec2<f32>,
};

fn vs_main(in: VertexInput) -> VertexOutput {
	// [...]

	// In plane.obj, the vertex xy coords range from -1 to 1
	// and we remap this to (0, 256)
	out.texelCoords = (in.position.xy + 1.0) * 128.0;
	return out;
}

fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let color = textureLoad(gradientTexture, vec2<i32>(in.texelCoords), 0).rgb;
	// [...]
}
```

```{note}
It is important that the conversion to integers (`vec2<i32>`) is done in the fragment shader rather than in the vertex shader, because integer vertex output do not get interpolated by the rasterizer.
```

```{figure} /images/fixed-mapping.png
:align: center
:class: with-shadow
A much better texture mapping.
```

UV coordinates
--------------

The texture coordinates are in practice expressed in the range $(0,1)$, so that they do not depend on the resolution of the texture, instead of explicitly giving texel indices. We call these normalized coordinates the **UV coordinates**.

We can make our code independent on the texture size using the `textureDimensions` function:

```rust
struct VertexOutput {
	// [...]
	@location(2) uv: vec2<f32>,
};

fn vs_main(in: VertexInput) -> VertexOutput {
	// [...]
	// In plane.obj, the vertex xy coords range from -1 to 1
	// and we remap this to (0, 1)
	out.uv = in.position.xy * 0.5 + 0.5;
	return out;
}

fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	let texelCoords = vec2<i32>(in.uv * vec2<f32>(textureDimensions(gradientTexture)));
	let color = textureLoad(gradientTexture, texelCoords, 0).rgb;
	// [...]
}
```

Loading from file
-----------------

UV coordinates are a very common thing, and there are UVs in the OBJ file I have been sharing with you, including this plane. We can add a **new attribute** like we did with normals to provide the UVs from the OBJ file up to the shader:

```C++
using glm::vec2;

struct VertexAttributes {
	vec3 position;
	vec3 normal;
	vec3 color;
	vec2 uv;
};

// [...]

requiredLimits.limits.maxVertexAttributes = 4;

// [...]

std::vector<VertexAttribute> vertexAttribs(4);

// [...]

// UV attribute
vertexAttribs[3].shaderLocation = 3;
vertexAttribs[3].format = VertexFormat::Float32x2;
vertexAttribs[3].offset = offsetof(VertexAttributes, uv);

// [...]
```

Note when loading UV coordinates from the file that we need to do a little conversion on the V axis.

```{image} /images/uv-coords-light.svg
:align: center
:class: only-light
```

```{image} /images/uv-coords-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>Modern graphics APIs use a different UV coordinate system than the OBJ file format.</em></span>
</p>

```C++
bool loadGeometryFromObj(const fs::path& path, std::vector<VertexAttributes>& vertexData) {
	// [...]

	vertexData[offset + i].uv = {
		attrib.texcoords[2 * idx.texcoord_index + 0],
		1 - attrib.texcoords[2 * idx.texcoord_index + 1]
	};

	// [...]
}
```

And in the shader:

```rust
struct VertexInput {
	@location(0) position: vec3<f32>,
	@location(1) normal: vec3<f32>,
	@location(2) color: vec3<f32>,
	@location(3) uv: vec2<f32>,
};

// [...]

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	// [...]
	out.uv = in.uv;
	return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    let texelCoords = vec2<i32>(in.uv * vec2<f32>(textureDimensions(gradientTexture)));
    let color = textureLoad(gradientTexture, texelCoords, 0).rgb;
    // [...]
}
```

For the plane this should not change anything, but if you try with [cube.obj](../../data/cube.obj) for instance it also works nicely!

```{figure} /images/textured-cube.png
:align: center
:class: with-shadow
A textured cube, seen from location $(-2, -3, 2)$.
```

Conclusion
----------

We are now able to load textures coordinates to map textures onto 3D meshes, but as you might have noticed, there is **a lot of aliasing** in the way we are getting texel data in the fragment shader.

The next chapter hence presents **the proper way of sampling** textures!

````{tab} With webgpu.hpp
*Resulting code:* [`step065`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step065)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step065-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step065-vanilla)
````
