Scene tree (<span class="bullet">🔴</span>TODO)
==========

````{tab} With webgpu.hpp
*Resulting code:* [`step100-gltf`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-gltf-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf-vanilla)
````

Multiple objects
----------------

Before moving on to a whole scene tree, let us start organizing our code to draw **more than a single mesh**.

TODO

Loading GLTF
------------

A very common format for representing 3D scenes made of a hierarchy of multiple (potentially animated) objects is [GLTF](https://github.com/KhronosGroup/glTF). In this chapter, we see how to load a GLTF file into our example application.

We use the popular [TinyGLTF](https://github.com/syoyo/tinygltf) library: it is header-only (thus easy to integrate), well maintained, and relies on dependencies that we are already using for texture loading: `stb_image.h`.

```{note}
This chapter is based on `step100`.
```

Download [`tiny_gltf.h`](https://github.com/syoyo/tinygltf/blob/release/tiny_gltf.h), [`json.hpp`](https://github.com/syoyo/tinygltf/blob/release/json.hpp) and [`stb_image_write.h`](https://github.com/syoyo/tinygltf/blob/release/stb_image_write.h) (you should already have `stb_image.h`).

Similarly to all the tiny libraries that we have been using, add the following to `implementations.cpp` (or any other cpp file as long as it is **only in one** of them).

```C++
// In implementations.cpp
// TinyGLTF must be **before** stb_image and stb_image_write
#define TINYGLTF_IMPLEMENTATION
#include "tiny_gltf.h"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"
```

In order to get familiarized with this new loading library, let us do as if it was only loading a single mesh, like our OBJ loading function. Create a new static method in the `ResourceManager` class:

```C++
class ResourceManager {
	// [...]
	// Load an 3D mesh from a standard .gltf file into a vertex data buffer
	static bool loadGeometryFromGltf(const path& path, std::vector<VertexAttributes>& vertexData);
};
```

We start by simply checking that we load the file correctly:

```C++
#include "tiny_gltf.h"

bool ResourceManager::loadGeometryFromGltf(const path& path, std::vector<VertexAttributes>& vertexData) {
	using namespace tinygltf;

	Model model;
	TinyGLTF loader;
	std::string err;
	std::string warn;

	bool success = false;
	if (path.extension() == ".glb") {
		success = loader.LoadBinaryFromFile(&model, &err, &warn, path.string());
	}
	else {
		success = loader.LoadASCIIFromFile(&model, &err, &warn, path.string());
	}

	if (!warn.empty()) {
		std::cout << "Warning: " << warn << std::endl;
	}

	if (!err.empty()) {
		std::cerr << "Error: " << err << std::endl;
	}

	return success;
}
```

As an example, we will use the typical Sci-Fi Helmet:

<div class="sketchfab-embed-wrapper"> <iframe title="Battle Damaged Sci-fi Helmet - PBR" frameborder="0" allowfullscreen mozallowfullscreen="true" webkitallowfullscreen="true" allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking execution-while-out-of-viewport execution-while-not-rendered web-share src="https://sketchfab.com/models/b81008d513954189a063ff901f7abfe4/embed?dnt=1"> </iframe> </div>

Download [DamagedHelmet.glb](https://github.com/KhronosGroup/glTF-Sample-Models/raw/main/2.0/DamagedHelmet/glTF-Binary/DamagedHelmet.glb) into your resource directory and try to load it in the application:

```C++
bool Application::initGeometry() {
	// [...]
	bool success = ResourceManager::loadGeometryFromGltf(RESOURCE_DIR "/DamagedHelmet.glb", vertexData);
	// [...]
}
```

```{note}
GLTF files can have either the `.gltf` or `.glb` extension. The latter has a 'b' for **binary** and is more compact, but less human-readable. It also embeds all its dependencies, whereas a .gltf
```

Uploading Scene Data
--------------------

Now that we have loaded the GLTF data in its native representation on CPU, we must organize it to fit our render pipeline, and upload all we need to the GPU.

In order to **avoid unneeded copies** and data processing, we try to let the GLTF scene drive our rendering process. There are however a few points that are driven by the need of our shader:

 - The list of **input vertex attributes** that we support and expect.

Initializing the GPU counterpart of the CPU model data consists in:

 1. Uploading resources (buffers and images), assuming that they are all needed (otherwise we can eventually add a step to clean up the GLTF data). Create mipmaps for textures (called "images" in GLTF terminology).
 2. Create samplers (on to one mapping of the concept of mappings in GLTF)
 3. Create a Material bind group for each material
 4. Create one Node bind group per mesh node
 5. Store vertex buffer indices for all mesh primitives

WIP Outline:
 1. Refactor the geometry loading so that we have a Scene and GpuScene object, used for both loading and drawing.
 2. Switch this to GLFW.

```{note}
The existence of a vertex attribute binding must depend on what the shader uses, but the layout itself depends on the GLTF data.
```

### Debug Renderer

We start with a simple debug renderer that draws one frame per node in the scene tree.

```C++
/**
 * A renderer that draws debug frame axes for each node of a GLTF scene.
 * 
 * You must call create() before draw(), and destroy() at the end of the
 * program. If create() is called twice, the previously created data gets
 * destroyed.
 */
class GltfDebugRenderer {
public:
	// Create from a CPU-side tinygltf model
	void create(wgpu::Device device, const tinygltf::Model& model);

	// Draw all nodes that use a given renderPipeline
	void draw(wgpu::RenderPassEncoder renderPass);

	// Destroy and release all resources
	void destroy();
};
```

Let us start by what we want to draw. As we said, we want one frame per node in the scene tree:

```C++
// We do as if we had all the variable we need, like 'm_nodeCount',
// 'm_vertexCount', 'm_vertexBuffer', 'm_vertexBufferByteSize' and 'm_pipeline'
void GltfDebugRenderer::draw(wgpu::RenderPassEncoder renderPass) {
	// Activate our pipeline dedicated to drawing frame axes
	renderPass.setPipeline(m_pipeline);
	// Activate the vertex buffer holding frame axes data
	renderPass.setVertexBuffer(0, m_vertexBuffer, 0, m_vertexBufferByteSize);

	// Iterate over all nodes of the scene tree
	for (uint32_t i = 0 ; i < m_nodeCount ; ++i) {
		// Draw a frame, i.e., a mesh of size 'm_vertexCount'
		renderPass.draw(m_vertexCount, 1, 0, 0);
	}
}
```

```{note}
We do not use instancing here on purpose. It is true that for drawing the very same geometry at each node like we do here it is a waste not to use instancing, but we will use this simplified example as a base for drawing a different mesh at each node. I will show afterwards how to switch to instancing in this debug renderer.
```

Now that we know what we are looking for, let us define our required attributes and initialize them in the `create` method:

```C++
// In GltfDebugRenderer.h
class GltfDebugRenderer {
	// [...]
private:
	wgpu::Device m_device = nullptr;
	wgpu::RenderPipeline m_pipeline = nullptr;
	wgpu::Buffer m_vertexBuffer = nullptr;
	uint64_t m_vertexBufferByteSize = 0;
	uint32_t m_nodeCount = 0;
	uint32_t m_vertexCount = 0;
};
```

Note that we keep a reference to the device, in order to use it in various methods. It is also used as a mean to tell that the renderer has been initialized when it is not null.

```C++
// In GltfDebugRenderer.cpp
void GltfDebugRenderer::create(wgpu::Device device, const tinygltf::Model& model) {
	if (m_device != nullptr) destroy();
	m_device = device;
	m_device.reference(); // increase reference counter to make sure the device remains valid
	// [...] Initialize things here
}

void GltfDebugRenderer::destroy() {
	// [...] Destroy things here
	m_device.release(); // decrease reference counter
	m_device = nullptr;
}
```

We then create init/terminate methods for the various elements of our renderer:

```C++
// In GltfDebugRenderer.h
class GltfDebugRenderer {
	// [...]
private:
	void initVertexBuffer();
	void terminateVertexBuffer();

	void initNodeData(const tinygltf::Model& model);
	void terminateNodeData();

	void initPipeline();
	void terminatePipeline();
	// [...]
};
```

````{tab} With webgpu.hpp
*Resulting code:* [`step100-gltf`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-gltf-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf-vanilla)
````
