Normal mapping (🚧WIP)
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step110`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step110)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step110-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step110-vanilla)
````

We have seen that the **normal** of a surface (i.e., the direction perpendicular to it) plays a key role in the way the light bounces on it. **Normal mapping** consists in locally perturbing this normal depending on an input map (texture file) to **model the effect of very small geometric details**.

```{note}
These **micro details** could in theory be represented by subdividing the mesh a lot and slightly moving some vertices, but for the scale that normal maps model, this approach is really not tractable.
```

```{image} /images/normal-mapping-equiv-light.svg
:align: center
:class: only-light
```

```{image} /images/normal-mapping-equiv-dark.svg
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>Perturbing the normal of the original mesh is a way to represent micro-geometry without the need to refine the mesh.</em></span>
</p>

Normal map
----------

There are different ways to provide the perturbed normals:

 - Specify a perturbed normal at each vertex, and interpolate across the face. This is used to smooth out the boundaries between faces and thus create smooth surfaces, and we already have this.

 - Provide a texture that gives the perturbed normal. This is heavier but can bring a lot more details. This texture is called the **normal map**.

```{image} /images/normal-map-light.png
:align: center
:class: only-light
```

```{image} /images/normal-map-dark.png
:align: center
:class: only-dark
```

<p class="align-center">
	<span class="caption-text"><em>The color of each pixel of a <strong>normal map</strong> encodes a normal vector. There are two convention for this encoding, called "DirectX" and "OpenGL" because they relate to how these APIs used to require the format.</em></span>
</p>

```{note}
The conventions "DirectX" and "OpenGL" are no longer constraints from the graphics API because we will write ourselves in the shader how normal map pixels must be interpreted. These names comes from before we could write shaders.

For the rest of this document, **we will follow the OpenGL convention.**
```

In order to use such a normal map, we need to:

 1. Load the file as a texture and bind it to the shader.
 2. Sample the texel and decode it into a normal vector
 3. Transform this normal with respect to the orientation of the face

On a plane
----------

Let us first focus on steps 1. and 2. by using a simple plane (so that there is no need for step 3.).

### Setup

Switch the loaded object to the plane:

```C++
bool success = ResourceManager::loadGeometryFromObj(RESOURCE_DIR "/plane.obj", m_vertexData);
```

For this example we use the `cobblestone_floor_08` material from [PolyHaven](https://polyhaven.com/a/cobblestone_floor_08) (a nice source of materials that can be freely used by the way). We only look at the [diffuse](../../images/cobblestone_floor_08_diff_2k.jpg) and [normal](../../images/cobblestone_floor_08_nor_gl_2k.png) maps for now, and load them as textures:

```C++
if (!initTexture(RESOURCE_DIR "/cobblestone_floor_08_diff_2k.jpg")) return false;
if (!initTexture(RESOURCE_DIR "/cobblestone_floor_08_nor_gl_2k.png")) return false;
```

We also add this new binding to the shader (that `initTexture` set up on the C++ side), and note that this offsets the lighting uniform:

```rust
@group(0) @binding(4) var<uniform> uLighting: LightingUniforms;
//                 ^ This was a 3
// [...]
@group(0) @binding(3) var normalTexture: texture_2d<f32>;
```

Increase the specular hardness and play with the view point so that you can highlight the problem with this texture:

```{figure} /images/no-normal-mapping.png
:align: center
:class: with-shadow
Without normal mapping, the cobblestone texture feels completely flat, which is odd for this material.
```

### Sampling normals

The key moment where normal mapping intervenes is when evaluating the normal `N` in the **fragment shader**.

```rust
let N = normalize(in.normal);
```

Instead of using the input normal, we sample the normal from the normal map:

```rust
// Sample normal
let encodedN = textureSample(normalTexture, textureSampler, in.uv).rgb;
let N = normalize(encodedN - 0.5);
```

For each channel $r$, $g$ and $b$, the sampled value lies in range $(0,1)$, and we need to map it to range $(-x,x)$ to **decode** it. The value of $x$ does not really matter since we then normalize the vector.

```{note}
If you are using the **DirectX** convention, you also need to **flip** the $Y$ value (multiply by -1 after decoding).
```

```{figure} /images/with-normal-mapping.png
:align: center
:class: with-shadow
With normal mapping, the cobblestone material looks like it has a much more realistic relief.
```

Normal mapping is **a powerful trick**, but of course it is not fully equivalent to refining geometry. In particular, it **cannot change the silhouette** of the shape, so the illusion falls at grazing angles:

```{figure} /images/with-normal-mapping-grazing-angle.png
:align: center
:class: with-shadow
At grazing angles, the normal mapping is not enough to give the feeling of relief to the material. More complex methods like **relief mapping** are needed here.
```

````{note}
If you want to dim down the influence of the normal map, you can mix it with the original normal:

```rust
let normalMapStrength = 0.5; // could be a uniform
let N = normalize(mix(in.normal, encodedN - 0.5, normalMapStrength));
```
````

On a mesh
---------

### The problem

The orientation contained in the normal map is given **relatively** to the global normal of the face.

In the case of the plane, we could completely ignore the original normal `in.normal` because it matched the Z axis of the normal map. But for any non-horizontal face, we need to **rotate the sampled normal**.

You can for instance test with this [`cylinder.obj`](../../data/cylinder.obj) model:

```{figure} /images/wrong-normals.png
:align: center
:class: with-shadow
Wrong normals: When sampling normals from texture (right), the overall lighting is off and very different from the effect of the input normal (left).
```

The problem becomes even clearer when we display the computed normals:

```rust
// To debug normals, we map from range (-1,1) to (0,1).
let color = N * 0.5 + 0.5;
```

```{figure} /images/wrong-normals-debug.png
:align: center
:class: with-shadow
Wrong normals: The direction sampled from the normal map (right) should be rotated to be centered around the original surface normal (left).
```

Our key requirement for the rotation is that when the sampled normal is $(0,0,1)$, the end normal vector corresponds to `in.normal`. We thus know what the $Z$ axis of the normal space is, but still need to define a $X$ and a $Y$ to fully get a rotation.

### Tangents and bitangents

TODO

#### Vertex attributes

TODO

We add vertex attributes:

```C++
// In ResourceManager.h
struct VertexAttributes {
	vec3 position;

	// Texture mapping attributes represent the local frame in which
	// normals sampled from the normal map are expressed.
	vec3 tangent; // X axis
	vec3 bitangent; // Y axis
	vec3 normal; // Z axis

	vec3 color;
	vec2 uv;
};
```

```C++
// In Application.cpp
std::vector<VertexAttribute> vertexAttribs(6);
//                                         ^ This was a 4

// [...]

// Tangent attribute
vertexAttribs[4].shaderLocation = 4;
vertexAttribs[4].format = VertexFormat::Float32x3;
vertexAttribs[4].offset = offsetof(VertexAttributes, tangent);

// Bitangent attribute
vertexAttribs[5].shaderLocation = 5;
vertexAttribs[5].format = VertexFormat::Float32x3;
vertexAttribs[5].offset = offsetof(VertexAttributes, bitangent);
```

```rust
struct VertexInput {
	// [...]
	@location(4) tangent: vec3<f32>,
	@location(5) bitangent: vec3<f32>,
}
```

Don't forget to bump up the limits:

```C++
requiredLimits.limits.maxVertexAttributes = 6;
//                                          ^ This was a 4
```

#### Computation

TODO

We compute these tangent and bitangent vectors when loading the mesh, in a new `computeTextureFrameAttributes` private method of the `ResourceManager`:

```C++
// In ResourceManager.h
private:
	// Compute Tangent and Bitangent attributes from the normal and UVs.
	static void computeTextureFrameAttributes(std::vector<VertexAttributes>& vertexData);
```

```C++
// At the end of loadGeometryFromObj
computeTextureFrameAttributes(vertexData);
return true;
```

The exact procedure is once again a matter of **convention**, to be aligned to what authoring tools export.

```C++
void ResourceManager::computeTextureFrameAttributes(std::vector<VertexAttributes>& vertexData) {
	size_t triangleCount = vertexData.size() / 3;
	// We compute the local texture frame per triangle
	for (int t = 0; t < triangleCount; ++t) {
		VertexAttributes* v = &vertexData[3 * t];

		// Formulas from http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/

		vec3 deltaPos1 = v[1].position - v[0].position;
		vec3 deltaPos2 = v[2].position - v[0].position;

		vec2 deltaUV1 = v[1].uv - v[0].uv;
		vec2 deltaUV2 = v[2].uv - v[0].uv;

		float r = 1.0f / (deltaUV1.x * deltaUV2.y - deltaUV1.y * deltaUV2.x);
		vec3 tangent = (deltaPos1 * deltaUV2.y - deltaPos2 * deltaUV1.y) * r;
		vec3 bitangent = (deltaPos2 * deltaUV1.x - deltaPos1 * deltaUV2.x) * r;
		
		// We assign these to the 3 corners of the triangle
		for (int k = 0; k < 3; ++k) {
			vertexData[3 * t + k].tangent = tangent;
			vertexData[3 * t + k].bitangent = bitangent;
		}
	}
}
```

#### Usage

TODO

```rust
struct VertexOutput {
	// [...]
	@location(4) tangent: vec3<f32>,
	@location(5) bitangent: vec3<f32>,
}
```

In the vertex shader:

```rust
out.tangent = (uMyUniforms.modelMatrix * vec4<f32>(in.tangent, 0.0)).xyz;
out.bitangent = (uMyUniforms.modelMatrix * vec4<f32>(in.bitangent, 0.0)).xyz;
out.normal = (uMyUniforms.modelMatrix * vec4<f32>(in.normal, 0.0)).xyz;
```

In the fragment shader:

```rust
// Sample normal
let encodedN = textureSample(normalTexture, textureSampler, in.uv).rgb;
let localN = encodedN - 0.5;
let rotation = mat3x3<f32>(
	normalize(in.tangent),
	normalize(in.bitangent),
	normalize(in.normal),
);
let rotatedN = normalize(rotation * localN);
let N = mix(in.normal, rotatedN, uLighting.normalMapStrength);
```

```{figure} /images/fixed-normal-map.png
:align: center
:class: with-shadow
Fixed normal maps.
```

You can try with the fourareen boat using [`fourareen2K_normals.png`](../../data/fourareen2K_normals.png):

```{figure} /images/fourareen-normal-mapping.png
:align: center
:class: with-shadow
The Fourareen boat with normal mapping.
```

(TODO: investigate why we still see some cracks and fireflies)

Conclusion
----------

To recap when normal mapping is about:

 - We **perturbate** normals to **emulate micro details** without paying the cost of finer meshes.
 - We **sample** this perturbation from a **normal map**.
 - We need to **combine** this perturbation with the original normal by rotating the sampled value.

````{tab} With webgpu.hpp
*Resulting code:* [`step110`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step110)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step110-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step110-vanilla)
````
