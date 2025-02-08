Loading from file <span class="bullet">🟡</span>
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step075`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step075-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075-vanilla)
````

The goal of this chapter is to **summarize everything we have done** to write a utility function `loadTexture` that creates a texture from a file.

````{tab} With webgpu.hpp
```C++
Texture loadTexture(const fs::path& path, Device device) {
	// [...]
}
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUTexture loadTexture(const fs::path& path, WGPUDevice device) {
	// [...]
}
```
````

## The stb_image library

Once again, to **load standard file format**, we better use existing code than study the specifications ourselves. We use here the `stb_image` single-header library, from the very handy [stb](https://github.com/nothings/stb) set of libraries. It supports all basic image types (png, jpg, bmp, ...).

Save [stb_image.h](https://raw.githubusercontent.com/nothings/stb/master/stb_image.h) in your source tree and include it in your main file:

```C++
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

This provides two functions: `stbi_load` and `stbi_image_free`, to be used as follows:

```C++
int width, height, channels;
unsigned char *data = stbi_load(path.string().c_str(), &width, &height, &channels, 0);
// If data is null, loading failed.

// Use the width, height, channels and data variables here
// [...]

stbi_image_free(data);
// (Do not use data after this)
```

````{note}
The stb_image library triggers a few warnings, that need to be deactivated if you want to treat warnings as errors.

```CMake
if (MSVC)
	# Disable warning C4244: conversion from 'int' to 'short', possible loss of data
	target_compile_options(App PUBLIC /wd4244)
endif (MSVC)
```

Note that this disables the warning for your files as well. A solution to only disable warnings for stb_image would be to have the file with `STB_IMAGE_IMPLEMENTATION` isolated in its own CMake target.
````

## loadTexture

With the dimensions of the texture in hand, we can create the texture object.

````{tab} With webgpu.hpp
```C++
Texture loadTexture(const fs::path& path, Device device) {
	int width, height, channels;
	unsigned char *pixelData = stbi_load(path.string().c_str(), &width, &height, &channels, 4 /* force 4 channels */);
	if (nullptr == pixelData) return nullptr;

	TextureDescriptor textureDesc;
	textureDesc.dimension = TextureDimension::_2D;
	textureDesc.format = TextureFormat::RGBA8Unorm; // by convention for bmp, png and jpg file. Be careful with other formats.
	textureDesc.mipLevelCount = 1;
	textureDesc.sampleCount = 1;
	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.usage = TextureUsage::TextureBinding | TextureUsage::CopyDst;
	textureDesc.viewFormatCount = 0;
	textureDesc.viewFormats = nullptr;
	Texture texture = device.createTexture(textureDesc);

	// Upload data to the GPU texture (to be implemented!)
	writeMipMaps(device, texture, textureDesc.size, textureDesc.mipLevelCount, pixelData);

	stbi_image_free(pixelData);

	return texture;
}
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUTexture loadTexture(const fs::path& path, WGPUDevice device) {
	int width, height, channels;
	unsigned char *pixelData = stbi_load(path.string().c_str(), &width, &height, &channels, 4 /* force 4 channels */);
	if (nullptr == pixelData) return nullptr;

	WGPUTextureDescriptor textureDesc = {};
	textureDesc.nextInChain = nullptr;
	textureDesc.dimension = WGPUTextureDimension_2D;
	textureDesc.format = WGPUTextureFormat_RGBA8Unorm; // by convention for bmp, png and jpg file. Be careful with other formats.
	textureDesc.mipLevelCount = 1;
	textureDesc.sampleCount = 1;
	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.usage = WGPUTextureUsage_TextureBinding | WGPUTextureUsage_CopyDst;
	textureDesc.viewFormatCount = 0;
	textureDesc.viewFormats = nullptr;
	WGPUTexture texture = wgpuDeviceCreateTexture(device, &textureDesc);

	// Upload data to the GPU texture (to be implemented!)
	writeMipMaps(device, texture, textureDesc.size, textureDesc.mipLevelCount, pixelData);

	stbi_image_free(pixelData);

	return texture;
}
```
````

We still need to write the `writeMipMaps` auxiliary function. The first mip level is easy, it can directly use the `data` vector:

````{tab} With webgpu.hpp
```C++
// Auxiliary function for loadTexture
static void writeMipMaps(
	Device device,
	Texture texture,
	Extent3D textureSize,
	[[maybe_unused]] uint32_t mipLevelCount, // not used yet
	const unsigned char* pixelData)
{
	ImageCopyTexture destination;
	destination.texture = texture;
	destination.mipLevel = 0;
	destination.origin = { 0, 0, 0 };
	destination.aspect = TextureAspect::All;

	TextureDataLayout source;
	source.offset = 0;
	source.bytesPerRow = 4 * textureSize.width;
	source.rowsPerImage = textureSize.height;

	Queue queue = device.getQueue();
	queue.writeTexture(destination, pixelData, 4 * textureSize.width * textureSize.height, source, textureSize);
	queue.release();
}
```
````

````{tab} Vanilla webgpu.h
```C++
// Auxiliary function for loadTexture
static void writeMipMaps(
	WGPUDevice device,
	WGPUTexture texture,
	WGPUExtent3D textureSize,
	[[maybe_unused]] uint32_t mipLevelCount, // not used yet
	const unsigned char* pixelData)
{
	WGPUImageCopyTexture destination = {};
	destination.texture = texture;
	destination.mipLevel = 0;
	destination.origin = { 0, 0, 0 };
	destination.aspect = WGPUTextureAspect_All;

	WGPUTextureDataLayout source = {};
	source.offset = 0;
	source.bytesPerRow = 4 * textureSize.width;
	source.rowsPerImage = textureSize.height;

	WGPUQueue queue = wgpuDeviceGetQueue(device);
	wgpuQueueWriteTexture(queue, destination, pixelData, 4 * textureSize.width * textureSize.height, source, textureSize);
	wgpuQueueRelease(queue);
}
```
````

## Texture view

Before dealing with mip maps, we'd like to test our `loadTexture` for mip level 0. But for this we still miss one part: the **texture view**.

To create the texture view that is used by the sampler, we need the **mip level count** and **format**. We can modify the `loadTexture` either to return this information or, as in this example, have it create an appropriate texture view and return it.

This is made **optional** by passing the returned view by a pointer, that is ignored if null.

````{tab} With webgpu.hpp
```C++
Texture loadTexture(const fs::path& path, Device device, TextureView* pTextureView = nullptr) {
	// [...]

	if (pTextureView) {
		TextureViewDescriptor textureViewDesc;
		textureViewDesc.aspect = TextureAspect::All;
		textureViewDesc.baseArrayLayer = 0;
		textureViewDesc.arrayLayerCount = 1;
		textureViewDesc.baseMipLevel = 0;
		textureViewDesc.mipLevelCount = textureDesc.mipLevelCount;
		textureViewDesc.dimension = TextureViewDimension::_2D;
		textureViewDesc.format = textureDesc.format;
		*pTextureView = texture.createView(textureViewDesc);
	}

	return texture;
}
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUTexture loadTexture(const fs::path& path, WGPUDevice device, WGPUTextureView* pTextureView = nullptr) {
	// [...]

	if (pTextureView) {
		TextureViewDescriptor textureViewDesc;
		textureViewDesc.aspect = WGPUTextureAspect_All;
		textureViewDesc.baseArrayLayer = 0;
		textureViewDesc.arrayLayerCount = 1;
		textureViewDesc.baseMipLevel = 0;
		textureViewDesc.mipLevelCount = textureDesc.mipLevelCount;
		textureViewDesc.dimension = WGPUTextureViewDimension_2D;
		textureViewDesc.format = textureDesc.format;
		*pTextureView = wgpuTextureCreateView(texture, &textureViewDesc);
	}

	return texture;
}
```
````

We can thus load our texture as follows:

````{tab} With webgpu.hpp
```C++
// Create a texture
TextureView textureView = nullptr;
Texture texture = loadTexture(RESOURCE_DIR "/texture.jpg", device, &textureView);
if (!texture) {
	std::cerr << "Could not load texture!" << std::endl;
	return 1;
}
// (remove the "Create and upload data" section from the init)
```
````

````{tab} Vanilla webgpu.h
```C++
// Create a texture
WGPUTextureView textureView = nullptr;
WGPUTexture texture = loadTexture(RESOURCE_DIR "/texture.jpg", device, &textureView);
if (!texture) {
	std::cerr << "Could not load texture!" << std::endl;
	return 1;
}
// (remove the "Create and upload data" section from the init)
```
````

Copy any image ([example](../../images/cobblestone_floor_08_diff_2k.jpg)) to `resources/texture.jpg` and you should see it loaded on the 3D plane! You may have to increase the maximum image size in the **device limits**:

```C++
// Allow textures up to 2K
requiredLimits.limits.maxTextureDimension1D = 2048;
requiredLimits.limits.maxTextureDimension2D = 2048;
```

```{note}
Here the texture view pointer passed to `loadTexture` is `&textureView`, namely the address of the variable `textureView`. Even if the variable itself is initialized to null, **its address**, called `pTextureView` in the function, **is not null**, and thus a view is created and returned.
```

## Generating mip-maps

Let us now come back on the `writeMipMaps` function. We can import in here the loop of `writeTexture` we implemented to load mip levels in the previous chapter:

````{tab} With webgpu.hpp
```C++
// Auxiliary function for loadTexture
static void writeMipMaps(
	Device device,
	Texture texture,
	Extent3D textureSize,
	uint32_t mipLevelCount,
	const unsigned char* pixelData)
{
	Queue queue = device.getQueue();

	// Arguments telling which part of the texture we upload to
	ImageCopyTexture destination;
	destination.texture = texture;
	destination.origin = { 0, 0, 0 };
	destination.aspect = TextureAspect::All;

	// Arguments telling how the C++ side pixel memory is laid out
	TextureDataLayout source;
	source.offset = 0;

	// Create image data
	Extent3D mipLevelSize = textureSize;
	std::vector<unsigned char> previousLevelPixels;
	Extent3D previousMipLevelSize;
	for (uint32_t level = 0; level < mipLevelCount; ++level) {
		// Pixel data for the current level
		std::vector<unsigned char> pixels(4 * mipLevelSize.width * mipLevelSize.height);
		if (level == 0) {
			// We cannot really avoid this copy since we need this
			// in previousLevelPixels at the next iteration
			memcpy(pixels.data(), pixelData, pixels.size());
		}
		else {
			// Create mip level data
			for (uint32_t i = 0; i < mipLevelSize.width; ++i) {
				for (uint32_t j = 0; j < mipLevelSize.height; ++j) {
					unsigned char* p = &pixels[4 * (j * mipLevelSize.width + i)];
					// Get the corresponding 4 pixels from the previous level
					unsigned char* p00 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 0))];
					unsigned char* p01 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 1))];
					unsigned char* p10 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 0))];
					unsigned char* p11 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 1))];
					// Average
					p[0] = (p00[0] + p01[0] + p10[0] + p11[0]) / 4;
					p[1] = (p00[1] + p01[1] + p10[1] + p11[1]) / 4;
					p[2] = (p00[2] + p01[2] + p10[2] + p11[2]) / 4;
					p[3] = (p00[3] + p01[3] + p10[3] + p11[3]) / 4;
				}
			}
		}

		// Upload data to the GPU texture
		destination.mipLevel = level;
		source.bytesPerRow = 4 * mipLevelSize.width;
		source.rowsPerImage = mipLevelSize.height;
		queue.writeTexture(destination, pixels.data(), pixels.size(), source, mipLevelSize);

		previousLevelPixels = std::move(pixels);
		previousMipLevelSize = mipLevelSize;
		mipLevelSize.width /= 2;
		mipLevelSize.height /= 2;
	}

	queue.release();
}
```
````

````{tab} Vanilla webgpu.h
```C++
// Auxiliary function for loadTexture
static void writeMipMaps(
	WGPUDevice device,
	WGPUTexture texture,
	WGPUExtent3D textureSize,
	uint32_t mipLevelCount,
	const unsigned char* pixelData)
{
	WGPUQueue queue = wgpuDeviceGetQueue(device);

	// Arguments telling which part of the texture we upload to
	WGPUImageCopyTexture destination = {};
	destination.texture = texture;
	destination.origin = { 0, 0, 0 };
	destination.aspect = WGPUTextureAspect_All;

	// Arguments telling how the C++ side pixel memory is laid out
	WGPUTextureDataLayout source = {};
	source.offset = 0;

	// Create image data
	WGPUExtent3D mipLevelSize = textureSize;
	std::vector<unsigned char> previousLevelPixels;
	WGPUExtent3D previousMipLevelSize;
	for (uint32_t level = 0; level < mipLevelCount; ++level) {
		// Pixel data for the current level
		std::vector<unsigned char> pixels(4 * mipLevelSize.width * mipLevelSize.height);
		if (level == 0) {
			// We cannot really avoid this copy since we need this
			// in previousLevelPixels at the next iteration
			memcpy(pixels.data(), pixelData, pixels.size());
		}
		else {
			// Create mip level data
			for (uint32_t i = 0; i < mipLevelSize.width; ++i) {
				for (uint32_t j = 0; j < mipLevelSize.height; ++j) {
					unsigned char* p = &pixels[4 * (j * mipLevelSize.width + i)];
					// Get the corresponding 4 pixels from the previous level
					unsigned char* p00 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 0))];
					unsigned char* p01 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 1))];
					unsigned char* p10 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 0))];
					unsigned char* p11 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 1))];
					// Average
					p[0] = (p00[0] + p01[0] + p10[0] + p11[0]) / 4;
					p[1] = (p00[1] + p01[1] + p10[1] + p11[1]) / 4;
					p[2] = (p00[2] + p01[2] + p10[2] + p11[2]) / 4;
					p[3] = (p00[3] + p01[3] + p10[3] + p11[3]) / 4;
				}
			}
		}

		// Upload data to the GPU texture
		destination.mipLevel = level;
		source.bytesPerRow = 4 * mipLevelSize.width;
		source.rowsPerImage = mipLevelSize.height;
		wgpuQueueWriteTexture(queue, destination, pixels.data(), pixels.size(), source, mipLevelSize);

		previousLevelPixels = std::move(pixels);
		previousMipLevelSize = mipLevelSize;
		mipLevelSize.width /= 2;
		mipLevelSize.height /= 2;
	}

	wgpuQueueRelease(queue);
}
```
````

Lastly, we **automatically infer the mip level count** from the texture size, as noted in the previous chapter:

````{tab} With webgpu.hpp
```C++
// Equivalent of std::bit_width that is available from C++20 onward
uint32_t bit_width(uint32_t m) {
	if (m == 0) return 0;
	else { uint32_t w = 0; while (m >>= 1) ++w; return w; }
}

Texture loadTexture(const fs::path& path, Device device) {
	// [...]

	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.mipLevelCount = bit_width(std::max(textureDesc.size.width, textureDesc.size.height));

	// [...]
}
```
````

````{tab} Vanilla webgpu.h
```C++
// Equivalent of std::bit_width that is available from C++20 onward
uint32_t bit_width(uint32_t m) {
	if (m == 0) return 0;
	else { uint32_t w = 0; while (m >>= 1) ++w; return w; }
}

WGPUTexture loadTexture(const fs::path& path, WGPUDevice device) {
	// [...]

	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.mipLevelCount = bit_width(std::max(textureDesc.size.width, textureDesc.size.height));

	// [...]
}
```
````

```{figure} /images/load-texture-from-file.jpg
:align: center
:class: with-shadow
A textured loaded from a file, with proper mip-mapping.
```

## Textured model

Let us finish this chapter with a nice textured 3D model. Unzip [fourareen.zip](../../data/fourareen.zip) in your resource directory (special thanks to Scottish Maritime Museum for [sharing this model](https://sketchfab.com/3d-models/venus-a-shetland-fourareen-ce4d6915e1d041459e08f2d8da521e86)!) and change the two loading lines:

````{tab} With webgpu.hpp
```C++
bool success = loadGeometryFromObj(RESOURCE_DIR "/fourareen.obj", vertexData);
// [...]
Texture texture = loadTexture(RESOURCE_DIR "/fourareen2K_albedo.jpg", device, &textureView);
```
````

````{tab} Vanilla webgpu.h
```C++
bool success = loadGeometryFromObj(RESOURCE_DIR "/fourareen.obj", vertexData);
// [...]
WGPUTexture texture = loadTexture(RESOURCE_DIR "/fourareen2K_albedo.jpg", device, &textureView);
```
````

If you try this, you'll see that the texture is not correctly projected onto the geometry. A first thing is to make sure you removed the UV multiplication we added in the previous chapter to explore the effect of the sampler:

```rust
out.uv = in.uv; // instead of in.uv * 6.0
```

We also need to increase again the vertex buffer size limit, because this mesh has almost 150k vertices:

```C++
requiredLimits.limits.maxBufferSize = 150000 * sizeof(VertexAttributes);
```

And finally here is a suggestion of view point:

```C++
// Matrices
uniforms.modelMatrix = mat4x4(1.0);
uniforms.viewMatrix = glm::lookAt(vec3(-2.0f, -3.0f, 2.0f), vec3(0.0f), vec3(0, 0, 1));
uniforms.projectionMatrix = glm::perspective(45 * PI / 180, 640.0f / 480.0f, 0.01f, 100.0f);
```

```{figure} /images/fourareen.png
:align: center
:class: with-shadow
A textured 3D model rendered in our WebGPU viewer.
```

Conclusion
----------

Even if the lighting model is quite basic, we are now able to load and display **complex 3D models with texture**!

The next part will help us **organize a bit our code base**, as it is getting too long to be left as a monolithic main. Once this is done, we'll proceed to the last part of building a basic real-time 3D renderer, namely **lighting**.

````{tab} With webgpu.hpp
*Resulting code:* [`step075`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step075-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075-vanilla)
````
