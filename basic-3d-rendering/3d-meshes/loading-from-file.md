Loading from file
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step058`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step058)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step058-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step058-vanilla)
````

This time, we are ready to load **an actual 3D file format**, so that you can play with any model you'd like.

In this chapter we load 3D models from the [OBJ](https://en.wikipedia.org/wiki/Wavefront_.obj_file) format. This is a very common format for storing 3D meshes with extra attributes (vertex colors, normals, but also texture coordinates and any other arbitrary data). You can for instance create an OBJ file by exporting it from [Blender](https://www.blender.org/).

## TinyOBJLoader

Instead of manually parsing OBJ files, we use the [TinyOBJLoader](https://github.com/tinyobjloader/tinyobjloader) library. The file format is not that complex, but parsing files is not the main point of this tutorial series, and this library has been intensively tested and has a very small footprint.

Similarly to [our `webgpu.hpp` wrapper](/getting-started/cpp-idioms.md), TinyOBJLoader is made of a single file [`tiny_obj_loader.h`](https://raw.githubusercontent.com/tinyobjloader/tinyobjloader/release/tiny_obj_loader.h) that you may simply save next to your `main.cpp`. Exactly one of your source files must define `TINYOBJLOADER_IMPLEMENTATION` before including it:

```C++
#define TINYOBJLOADER_IMPLEMENTATION // add this to exactly 1 of your C++ files
#include "tiny_obj_loader.h"
```

We create a new loading function:

```C++
bool loadGeometryFromObj(const fs::path& path, std::vector<VertexAttributes>& vertexData);
```

We can use [the example code](https://github.com/tinyobjloader/tinyobjloader#example-code-deprecated-api) from TinyOBJLoader's README as a base, that shows how to call the `LoadObj` function it provides:

```C++
bool loadGeometryFromObj(const fs::path& path, std::vector<VertexAttributes>& vertexData) {
	tinyobj::attrib_t attrib;
	std::vector<tinyobj::shape_t> shapes;
	std::vector<tinyobj::material_t> materials;

	std::string warn;
	std::string err;

	bool ret = tinyobj::LoadObj(&attrib, &shapes, &materials, &warn, &err, path.string().c_str());

	if (!warn.empty()) {
		std::cout << warn << std::endl;
	}

	if (!err.empty()) {
		std::cerr << err << std::endl;
	}

	if (!ret) {
		return false;
	}

	// Fill in vertexData here

	return true;
}
```

Once the tinyobj-specific structures are filled in (`shape_t`, `attrib_t`), we can extract our vertex array data:

```C++
// Filling in vertexData:
const auto& shape = shapes[0]; // look at the first shape only

vertexData.resize(shape.mesh.indices.size());
for (int i = 0; i < vertexData.size(); ++i) {
	const tinyobj::index_t& idx = shape.mesh.indices[i];

	vertexData[i].position = {
		attrib.vertices[3 * idx.vertex_index + 0],
		attrib.vertices[3 * idx.vertex_index + 1],
		attrib.vertices[3 * idx.vertex_index + 2]
	};

	vertexData[i].normal = {
		attrib.normals[3 * idx.normal_index + 0],
		attrib.normals[3 * idx.normal_index + 1],
		attrib.normals[3 * idx.normal_index + 2]
	};

	vertexData[i].color = {
		attrib.colors[3 * idx.vertex_index + 0],
		attrib.colors[3 * idx.vertex_index + 1],
		attrib.colors[3 * idx.vertex_index + 2]
	};
}
```

We can generalize to all the parts of the model by iterating over `shapes`:

```C++
vertexData.clear();
for (const auto& shape : shapes) {
	size_t offset = vertexData.size();
	vertexData.resize(offset + shape.mesh.indices.size());
	// [...]
	vertexData[offset + i].position = /* ... */;
	vertexData[offset + i].normal = /* ... */;
	vertexData[offset + i].color = /* ... */;
}
```

## Loading a first object

We stop using indexed drawing but switch to a vector of `VertexAttributes` rather than a blind vector of `float` for the vertex buffer data:

```C++
std::vector<VertexAttributes> vertexData;
bool success = loadGeometryFromObj(RESOURCE_DIR "/pyramid.obj", vertexData);
if (!success) {
	std::cerr << "Could not load geometry!" << std::endl;
	return 1;
}
// [...]
bufferDesc.size = vertexData.size() * sizeof(VertexAttributes);
// [...]
queue.writeBuffer(vertexBuffer, 0, vertexData.data(), bufferDesc.size);
// [...]
int indexCount = static_cast<int>(vertexData.size());
// (remove 'Create index buffer')
// [...]
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexData.size() * sizeof(VertexAttributes));
// (remove renderPass.setIndexBuffer)
// [...]
renderPass.draw(indexCount, 1, 0, 0);
```

Test this with [pyramid.obj](../../data/pyramid.obj), which is the same pyramid but with beveled (smoothed) edges:

```{figure} /images/pyramid-obj-yup.png
:align: center
:class: with-shadow
The 3D model is correctly loaded but not oriented as expected.
```

## Vertical axis convention

There is **no consensus** among 3D modeling and 3D rendering tools, but file formats usually impose a convention. In the case of the OBJ format, it is specified that **the Y axis represents the upward vertical direction**.

Since we have been implicitly following the convention that **Z is the vertical in our code**, we need to either change our convention (by changing the view matrix) or convert upon loading. I chose the latter:

```C++
vertexData[i].position = {
	attrib.vertices[3 * idx.vertex_index + 0],
	-attrib.vertices[3 * idx.vertex_index + 2], // Add a minus to avoid mirroring
	attrib.vertices[3 * idx.vertex_index + 1]
};

// Also apply the transform to normals!!
vertexData[i].normal = {
	attrib.normals[3 * idx.normal_index + 0],
	-attrib.normals[3 * idx.normal_index + 2],
	attrib.normals[3 * idx.normal_index + 1]
};
```

```{figure} /images/pyramid-obj.png
:align: center
:class: with-shadow
The loaded 3D model, correctly oriented.
```

## Another example

Want something a bit more interesting? Try [mammoth.obj](../../data/mammoth.obj)! And thank the Smithsonian for [sharing the model](https://sketchfab.com/3d-models/mammuthus-primigenius-blumbach-229976b3db4646b39c44e57a7e3d8744).

```{figure} /images/mammoth.png
:align: center
:class: with-shadow
A complex 3D model.
```

Conclusion
----------

This chapter concludes this part about loading and rendering 3D meshes. It was quite of a part, congratulations for having followed so far!

From now on we will see how to improve on top of this base, but feel free to take some time to **play around**.

You can now load your own models (going through Blender to convert them if you get them in a different file format), animate the position of different objects, change the lighting (even animate it using uniforms), etc.

````{tab} With webgpu.hpp
*Resulting code:* [`step058`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step058)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step058-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step058-vanilla)
````

