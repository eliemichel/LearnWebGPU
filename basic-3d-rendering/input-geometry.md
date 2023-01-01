Input Geometry (WIP)
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step041`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step041)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step041-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step041-vanilla)
````

Vertex Attribute Buffer
-----------------------

### Position attribute

Instead of hard-coding the position of vertices in the shader, we fetch them from a buffer.

TODO

```C++
std::vector<VertexAttribute> vertexAttribs(1);
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = VertexFormat::Float32x2;
vertexAttribs[0].offset = 0;

VertexBufferLayout vertexBufferLayout;
vertexBufferLayout.arrayStride = 2 * sizeof(float);
vertexBufferLayout.attributeCount = static_cast<uint32_t>(vertexAttribs.size());
vertexBufferLayout.attributes = vertexAttribs.data();
vertexBufferLayout.stepMode = VertexStepMode::Vertex;

pipelineDesc.vertex.bufferCount = 1;
pipelineDesc.vertex.buffers = &vertexBufferLayout;
```

```C++
requiredLimits.limits.maxVertexAttributes = 1;
requiredLimits.limits.maxVertexBuffers = 1;
```

```C++
// Define geometry
std::vector<float> vertexData = {
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5
};
int vertexCount = static_cast<int>(vertexData.size() / 2);

// Create vertex buffer
bufferDesc.size = vertexData.size() * sizeof(float);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Vertex;
bufferDesc.mappedAtCreation = false;
Buffer vertexBuffer = device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
queue.writeBuffer(vertexBuffer, 0, vertexData.data(), bufferDesc.size);
```

```C++
renderPass.setPipeline(pipeline);

// Set vertex buffer while encoding the render pass
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexData.size() * sizeof(float));

renderPass.setBindGroup(0, bindGroup, 0, nullptr);
renderPass.draw(vertexCount, 1, 0, 0);
```

```rust
@vertex
fn vs_main(@location(0) in_position: vec2<f32>) -> @builtin(position) vec4<f32> {
	var p = in_position + 0.3 * vec2<f32>(cos(uTime), sin(uTime));
	return vec4<f32>(p, 0.0, 1.0);
}
```

Let's change the input geometry:

```C++
std::vector<float> vertexData = {
	-0.5, -0.5,
	+0.5, -0.5,
	+0.0, +0.5,

	-0.55f, -0.5,
	-0.05f, +0.5,
	-0.55f, +0.5
};
```

![Two triangles](/images/two-triangles.png)

````{tab} With webgpu.hpp
*Resulting code:* [`step040`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step040-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step040-vanilla)
````

Multiple Attributes
-------------------

Let's add a color attribute.

```C++
requiredLimits.limits.maxVertexAttributes = 2;
```

### Option A: Interleaved attributes

```C++
std::vector<float> vertexData = {
	// x, y, r, g, b
	-0.5, -0.5, 1.0, 0.0, 0.0,
	+0.5, -0.5, 0.0, 1.0, 0.0,
	+0.0, +0.5, 0.0, 0.0, 1.0,

	-0.55f, -0.5, 1.0, 1.0, 0.0,
	-0.05f, +0.5, 1.0, 0.0, 1.0,
	-0.55f, +0.5, 0.0, 1.0, 1.0
};
int vertexCount = static_cast<int>(vertexData.size() / 5);
```

```C++
// We now have 2 attributes
std::vector<VertexAttribute> vertexAttribs(2);

// Position attribute
vertexAttribs[0].shaderLocation = 0;
vertexAttribs[0].format = VertexFormat::Float32x2;
vertexAttribs[0].offset = 0;

// Color attribute
vertexAttribs[1].shaderLocation = 1;
vertexAttribs[1].format = VertexFormat::Float32x3;
vertexAttribs[1].offset = 2 * sizeof(float);

// [...]

vertexBufferLayout.arrayStride = 5 * sizeof(float);
```

### Option B: Multiple buffers


### Shader

```rust
@vertex
fn vs_main(@location(0) in_position: vec2<f32>, @location(1) in_color: vec3<f32>) -> @builtin(position) vec4<f32> {
	// [...]
}
```

```rust
struct VertexInput {
	@location(0) position: vec2<f32>,
	@location(1) color: vec3<f32>,
};

@vertex
fn vs_main(in: VertexInput) -> @builtin(position) vec4<f32> {
	// [...]
}
```

```rust
struct VertexInput {
	@location(0) position: vec2<f32>,
	@location(1) color: vec3<f32>,
};

struct VertexOutput {
	@builtin(position) position: vec4<f32>,
	@location(0) color: vec3<f32>,
};

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
    out.position = // [...]
    out.color = // [...]
    return out;
}
```

```rust
@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
	var out: VertexOutput;
	var p = in.position + 0.3 * vec2<f32>(cos(uMyUniforms.time), sin(uMyUniforms.time));
	out.position = vec4<f32>(p, 0.0, 1.0);
	out.color = in.color;
	return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	return vec4<f32>(in.color, 1.0);
}
```

![Triangles with color attribute](/images/color-attribute.png)

Index Buffers
-------------

Let's draw a square, which is made of 2 triangles.

```{image} /images/quad-light.svg
:align: center
:class: only-light
```

```{image} /images/quad-dark.svg
:align: center
:class: only-dark
```

A straightforward way:

```C++
std::vector<float> vertexData = {
	// Triangle #0
	-0.5, -0.5, // A
	+0.5, -0.5,
	+0.5, +0.5, // C

	// Triangle #1
	-0.5, -0.5, // A
	+0.5, +0.5, // C
	-0.5, +0.5,
};
```

But as you can see some data is duplicated. And this could be much worst on larger shapes with connected triangles.

So instead we can split the **position** from the **connectivity**:

```C++
// The de-duplicated list of point positions
std::vector<float> pointData = {
	-0.5, -0.5, // A
	+0.5, -0.5,
	+0.5, +0.5, // C
	-0.5, +0.5,
};

// This is a list of indices referencing positions in the pointData
std::vector<uint16_t> indexData = {
	0, 1, 2, // Triangle #0
	0, 2, 3  // Triangle #1
};

int indexCount = static_cast<int>(indexData.size());
```

```C++
// Create index buffer
bufferDesc.size = indexData.size() * sizeof(uint16_t);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Index;
bufferDesc.mappedAtCreation = false;
Buffer indexBuffer = device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
queue.writeBuffer(indexBuffer, 0, indexData.data(), bufferDesc.size);
```

```C++
renderPass.setIndexBuffer(indexBuffer, IndexFormat::Uint16, 0, indexData.size() * sizeof(uint16_t));

// Replace draw() with drawIndexed()
renderPass.drawIndexed(vertexCount, 1, 0, 0, 0);
```

```{figure} /images/deformed-quad.png
:align: center
:class: with-shadow
The square is deformed because its coordinates are expressed relative to the window's dimensions.
```

```rust
struct MyUniforms {
    color: vec4<f32>,
	resolution: vec2<f32>, // don't forget the alignment requirements!
	time: f32,
};

// [...]

var p = in.position * vec2<f32>(1.0, uMyUniforms.resolution.x / uMyUniforms.resolution.y);
```

```C++
struct MyUniforms {
	std::array<float, 4> color;
	std::array<float, 2> resolution;
	float time;
	float _pad[1];
};

// [...]

MyUniforms uniforms;
uniforms.time = 1.0f;
uniforms.color = { 0.0f, 1.0f, 0.4f, 1.0f };
uniforms.resolution = { 640.0f, 480.0f };
queue.writeBuffer(uniformBuffer, 0, &uniforms, sizeof(MyUniforms));
```

```{figure} /images/quad.png
:align: center
:class: with-shadow
The expected square
```

````{tab} With webgpu.hpp
*Resulting code:* [`step041`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step041)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step041-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step041-vanilla)
````

Loading from file
-----------------

```C++
[points]
# x   y      r   g   b

0.5   0.0    0.0 0.353 0.612
1.0   0.866  0.0 0.353 0.612
0.0   0.866  0.0 0.353 0.612

0.75  0.433  0.0 0.4   0.7
1.25  0.433  0.0 0.4   0.7
1.0   0.866  0.0 0.4   0.7

1.0   0.0    0.0 0.463 0.8
1.25  0.433  0.0 0.463 0.8
0.75  0.433  0.0 0.463 0.8

1.25  0.433  0.0 0.525 0.91
1.375 0.65   0.0 0.525 0.91
1.125 0.65   0.0 0.525 0.91

1.125 0.65   0.0 0.576 1.0
1.375 0.65   0.0 0.576 1.0
1.25  0.866  0.0 0.576 1.0

[indices]
 0  1  2
 3  4  5
 6  7  8
 9 10 11
12 13 14
```

```C++
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace wgpu;
namespace fs = std::filesystem;

bool loadGeometry(const fs::path& path, std::vector<float>& pointData, std::vector<uint16_t>& indexData) {
	std::ifstream file(path);
	if (!file.is_open()) {
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
			// Get x, y, r, g, b
			for (int i = 0; i < 5; ++i) {
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

```C++
#define DATA_DIR "../data"

bool success = loadGeometry(DATA_DIR "/webgpu.txt", pointData, indexData);
if (!success) {
	std::cerr << "Could not load geometry!" << std::endl;
	return 1;
}
```

TODO

![The WebGPU Logo](/images/loaded-webgpu-logo-colorspace-issue.png)

```rust
return vec4<f32>(pow(in.color, vec3<f32>(2.2)), 1.0);
```

![The WebGPU Logo](/images/loaded-webgpu-logo.png)

Conclusion
----------

TODO

````{tab} With webgpu.hpp
*Resulting code:* [`step042`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step042)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step042-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step042-vanilla)
````


