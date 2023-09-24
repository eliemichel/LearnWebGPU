Scene tree (🛑TODO)
==========

````{tab} With webgpu.hpp
*Resulting code:* [`step100-gltf`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-gltf-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf-vanilla)
````

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

Download [DamagedHelmet.glb](https://github.com/KhronosGroup/glTF-Sample-Models/raw/master/2.0/DamagedHelmet/glTF-Binary/DamagedHelmet.glb) into your resource directory and try to load it in the application:

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

WIP Outline:
 1. Refactor the geometry loading so that we have a Scene and GpuScene object, used for both loading and drawing.
 2. Switch this to GLFW.

````{tab} With webgpu.hpp
*Resulting code:* [`step100-gltf`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-gltf-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-gltf-vanilla)
````
