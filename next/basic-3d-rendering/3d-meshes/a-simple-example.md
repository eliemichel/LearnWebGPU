A simple example <span class="bullet">🟢</span>
================

```{lit-setup}
:tangle-root: 050 - A simple example - Next - vanilla
:parent: 043 - More uniforms - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 050 - A simple example - Next
:parent: 043 - More uniforms - Next
```

````{tab} With webgpu.hpp
*Resulting code:* [`step050-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step050-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-vanilla-next)
````

Let's dive into what you are quite likely here for: rendering **3D shapes**!

````{note}
I rolled back the part of the code about dynamic uniforms for now. I also set the `offset` to `vec2f(0.0)`;

```{lit} rust, Vertex shader (replace, also for tangle root "Vanilla")
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	let ratio = 640.0 / 480.0;
	var offset = vec2f(0.0, 0.0);
	out.position = vec4f(in.position.x + offset.x, (in.position.y + offset.y) * ratio, 0.0, 1.0);
	out.color = in.color;
	return out;
}
```
````

Switching to 3D data
--------------------

### Data file

The first thing we need is a **3rd column** in our point position! We stick with our ad-hoc file format for now and simply add a "z" attribute.

Here is a simple shape that you can save in `resources/pyramid.txt` and which corresponds to a simple pyramid shape whose tip has a different color:

```{lit} C++, file: resources/pyramid.txt (also for tangle root "Vanilla")
# In file resources/pyramid.txt
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

Of course we need to adapt our `loadGeometry` function to **handle this extra dimension**. I added a `int dimensions` argument that should be either 2 or 3 depending on whether we are in 2D or 3D:

```C++
bool ResourceManager::loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData,
	int dimensions // <-- new argument
) {
	// [...]

	// Get x, y, z, r, g, b
	for (int i = 0; i < dimensions + 3; ++i) {
	//                  ^^^^^^^^^^^^^^ This was a 5

	// [...]
}
```

```{lit} C++, Declaration of ResourceManager::loadGeometry (hidden, replace, also for tangle root "Vanilla")
/**
 * Load a file from `path` using our ad-hoc format and populate the `pointData`
 * and `indexData` vectors.
 */
static bool loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData,
	int dimensions // <-- new argument
);
```

```{lit} C++, Implementation of ResourceManager::loadGeometry (hidden, replace, also for tangle root "Vanilla")
bool ResourceManager::loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData,
	int dimensions // <-- new argument
) {
	std::ifstream file(path);
	if (!file.is_open()) {
		std::cerr << "Could not load geometry!" << std::endl;
		return false;
	}

	pointData.clear();
	indexData.clear();

	enum class Section {
		None,
		Points,
		Indices,
	};
	Section currentSection = Section::None;

	float value;
	uint16_t index;
	std::string line;
	while (!file.eof()) {
		getline(file, line);
		
		// overcome the `CRLF` problem
		if (!line.empty() && line.back() == '\r') {
			line.pop_back();
		}
		
		if (line == "[points]") {
			currentSection = Section::Points;
		}
		else if (line == "[indices]") {
			currentSection = Section::Indices;
		}
		else if (line[0] == '#' || line.empty()) {
			// Do nothing, this is a comment
		}
		else if (currentSection == Section::Points) {
			std::istringstream iss(line);
			// Get x, y, z, r, g, b
			for (int i = 0; i < dimensions + 3; ++i) {
			    //              ^^^^^^^^^^^^^^ This was a 5
				iss >> value;
				pointData.push_back(value);
			}
		}
		else if (currentSection == Section::Indices) {
			std::istringstream iss(line);
			// Get corners #0 #1 and #2
			for (int i = 0; i < 3; ++i) {
				iss >> index;
				indexData.push_back(index);
			}
		}
	}
	return true;
}
```

We can now load the geometry in `Application::InitializeBuffers()` with an extra `dimensions` argument:

```{lit} C++, Load geometry data from file (replace, also for tangle root "Vanilla")
std::vector<float> pointData;
std::vector<uint16_t> indexData;

bool success = ResourceManager::loadGeometry(
	RESOURCE_DIR  "/pyramid.txt", // <-- switch to the pyramid
	pointData,
	indexData,
	3 /* dimensions */ // <-- new argument
);
if (!success) return false;

m_indexCount = static_cast<uint32_t>(indexData.size());
```

### Vertex buffer

As a consequence of this new dimension, we need to **update the vertex buffer description**.

First we **change the format of the position attribute** from `Float32x2` to `Float32x3`:

````{tab} With webgpu.hpp
```{lit} C++, Describe the position attribute (replace)
// Position attribute
vertexAttribs[0].shaderLocation = 0; // @location(0)
vertexAttribs[0].format = VertexFormat::Float32x3;
//                                              ^ This was a 2
vertexAttribs[0].offset = 0;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe the position attribute (replace, for tangle root "Vanilla")
// Position attribute
vertexAttribs[0].shaderLocation = 0; // @location(0)
vertexAttribs[0].format = WGPUVertexFormat_Float32x3;
//                                                 ^ This was a 2
vertexAttribs[0].offset = 0;
```
````

This offsets all the attributes coming after! So we **change the offset of the color attribute**:

````{tab} With webgpu.hpp
```{lit} C++, Describe the color attribute (replace)
// Color attribute
vertexAttribs[1].shaderLocation = 1; // @location(1)
vertexAttribs[1].format = VertexFormat::Float32x3;
vertexAttribs[1].offset = 3 * sizeof(float);
//                        ^ This was a 2
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe the color attribute (replace, for tangle root "Vanilla")
// Color attribute
vertexAttribs[1].shaderLocation = 1; // @location(1)
vertexAttribs[1].format = WGPUVertexFormat_Float32x3;
vertexAttribs[1].offset = 3 * sizeof(float);
//                        ^ This was a 2
```
````

And since the overall size of our attribtues changed, we need to reflect this in the **vertex buffer byte stride**:

````{tab} With webgpu.hpp
```{lit} C++, Describe buffer stride and step mode (replace)
// The buffer stride
vertexBufferLayout.arrayStride = 6 * sizeof(float);
//                               ^ This was a 5
vertexBufferLayout.stepMode = VertexStepMode::Vertex;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Describe buffer stride and step mode (replace, for tangle root "Vanilla")
// The buffer stride
vertexBufferLayout.arrayStride = 6 * sizeof(float);
//                               ^ This was a 5
vertexBufferLayout.stepMode = WGPUVertexStepMode_Vertex;
```
````

### Vertex shader

And don't forget to update the vertex input struct in the **shader**!

```{lit} rust, Define VertexInput struct (replace, also for tangle root "Vanilla")
struct VertexInput {
	@location(0) position: vec3f,
	//                        ^ This was a 2
	@location(1) color: vec3f,
};
```

Now it kinda works, we can guess a pyramid is here, but I wouldn't call it 3D yet. And adding `in.position.z` to `out.position.z` does not change anything so far:

```{figure} /images/pyramid-base.png
:align: center
:class: with-shadow
The pyramid... seen from above, with no perspective.
```

```{note}
I intentionally set a different color for the tip of the pyramid so that we can see better. This will be better addressed when introducing a basic **shading**.
```

Basic transform
---------------

*This is a gentle introduction to **trigonometry**. If you are familiar with the concept, you may jump ahead.*

Seen from above, this pyramid boringly looks like an square. Could we **rotate** this? A very basic way to change the view angle is to **swap axes**:

```{lit} rust, Set vertex out position (also for tangle root "Vanilla")
var position = vec3f(
	in.position.x,
	in.position.z, // swap axis Y and Z
	in.position.y,
);
out.position = vec4f(position.x, position.y * ratio, 0.0, 1.0);
```

````{admonition} Where to insert this?
:class: foldable

We place this in the **vertex shader**:

```{lit} Vertex shader (replace, also for tangle root "Vanilla")
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	let ratio = 640.0 / 480.0;
	{{Set vertex out position}}
	out.color = in.color;
	return out;
}
```
````

```{figure} /images/pyramid-side.png
:align: center
:class: with-shadow
The pyramid seen from the side (still no perspective).
```

What about in-between rotations? The idea is to **mix axes**, adding a little bit of z in the y coordinates and a little bit of y in the z coordinates.

```{lit} rust, Set vertex out position (replace, also for tangle root "Vanilla")
var position = vec3f(
	in.position.x,
	in.position.y + 0.5 * in.position.z, // add a bit of Z in Y...
	in.position.z + 0.5 * in.position.y, // ...and a bit of Y in Z.
);
out.position = vec4f(position.x, position.y * ratio, 0.0, 1.0);
```

```{figure} /images/pyramid-tilted.png
:align: center
:class: with-shadow
The pyramid from a tilted view angle.
```

Of course at some point we have to remove some of `in.position.y` from Y so that after a quarter of turn we reach `Y = 0.0 * in.position.y + 1.0 * in.position.z`, as in the example above. So **more generally** our transform writes like this, where `alpha` and `beta` depend on the **rotation angle**:

```rust
let angle = uMyUniforms.time; // you can multiply it go rotate faster
let alpha: f32 = /* ??? */;
let beta: f32 = /* ??? */;
var position = vec3f(
	in.position.x,
	alpha * in.position.y + beta * in.position.z,
	alpha * in.position.z - beta * in.position.y,
);
out.position = vec4f(position.x, position.y * ratio, 0.0, 1.0);
```

```{note}
If you pay close attention to the snippet above, you can notice **a minus sign** `-` before the second `beta`. It is not visible on our pyramid because it is symmetrical but swapping axes also flips the object. To **counter-balance** this, we can change the sign of one of the dimensions. Hence the Z coordinate after a quarter of turn must be `-in.position.y` instead of `in.position.y`.
```

It turns out that these **weights** `alpha` and `beta` are not easy to express in terms of basic operations **with respect to the angle**. So mathematicians came up with a dedicated name for them: **cosine** and **sine**! And the good news is that these are **built-in operations** in WGSL:

```{lit} rust, Set vertex out position (replace, also for tangle root "Vanilla")
let angle = uMyUniforms.time; // you can multiply it go rotate faster
let alpha = cos(angle);
let beta = sin(angle);
var position = vec3f(
	in.position.x,
	alpha * in.position.y + beta * in.position.z,
	alpha * in.position.z - beta * in.position.y,
);
out.position = vec4f(position.x, position.y * ratio, 0.0, 1.0);
```

<figure class="align-center">
	<video autoplay loop muted inline nocontrols style="width:100%;height:auto;max-width:642px">
		<source src="../../../_static/pyramid-ryz.mp4" type="video/mp4">
	</video>
	<figcaption>
		<p><span class="caption-text">Rotation in the YZ plane</span></p>
	</figcaption>
</figure>

```{themed-figure} /images/trigo-{theme}.svg
:align: center

A side-view of the pyramid. The (signed) length of the green vertical and horizontal lines give the value of `alpha` and `beta` respectively.
```

Congratulations, you have learned most of what there is to know about **trigonometry** for computer graphics!

```{hint}
**If you cannot remember** which one is the $cos$ and which one is the $sin$ among `alpha` and `beta` (don't worry! It happens to everyone), **just take an example** with very simple rotation: `angle = 0`. In such a case, we need `alpha = 1` and `beta = 0`. If you look at a plot of the $sin$ and $cos$ functions you'll quickly see that $cos(0) = 1$ and $sin(0) = 0$
```

```{important}
The argument of trigonometric functions is an **angle**, but be aware that it must be expressed in **radians**. There is a total of $2\pi$ radians for a full turn, which leads to the following elementary cross-multiplication rule:

$$
\frac{r \text{ radians}}{d \text{ degrees}} = \frac{2\pi \text{ radians}}{360 \text{ degrees}}
$$

So to convert an angle $d$ in **degrees** into its equivalent $r$ in **radians**, we simply do:

$$
r = d \times \frac{\pi}{180}
$$
```

Conclusion
----------

We have a beginning of something. With this rotation, it starts looking like 3D, but there remains some important points to be concerned about:

 - **Depth fighting:** As highlighted in the image below, the triangles do not overlap in the correct order.
 - **Transform:** We have the basics, but it is a bit manual, and there is still **no perspective**!
 - **Shading:** The trick of setting the tip of the pyramid to a darker color was good for a start, but we can do much better.

These points are, in this order, the topic of the next 4 chapters (transforms are split in 2 chapters).

```{figure} /images/pyramid-zissue.png
:align: center
:class: with-shadow
There is something wrong with the depth.
```

````{tab} With webgpu.hpp
*Resulting code:* [`step050-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step050-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step050-vanilla-next)
````
