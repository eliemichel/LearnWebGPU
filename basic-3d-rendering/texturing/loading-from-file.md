Loading from file
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step076`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step076)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step076-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step076-vanilla)
````

The goal of this chapter is to summarize everything we have done to write a utility function `loadTexture` that creates a texture from a file.

## stb_image

Once again, to load standard file format, we better use existing code than study the specifications ourselves. We use here the `stb_image` single-header library, from the very handy [stb](https://github.com/nothings/stb) set of libraries. It supports all basic image types (png, jpg, bmp, ...).

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

## loadTexture

This `data` vector is our mip level 0, so if we do not need mip-mapping the procedure to get a texture out of it is pretty straightforward:

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

	ImageCopyTexture destination;
	destination.texture = texture;
	destination.mipLevel = 0;
	destination.origin = { 0, 0, 0 };
	destination.aspect = TextureAspect::All;

	TextureDataLayout source;
	source.offset = 0;
	source.bytesPerRow = 4 * textureDesc.size.width;
	source.rowsPerImage = textureDesc.size.height;

	// Upload data to the GPU texture
	device.getQueue().writeTexture(destination, pixelData, 4 * width * height, source, textureDesc.size);

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

	WGPUImageCopyTexture destination = {};
	destination.nextInChain = nullptr;
	destination.texture = texture;
	destination.mipLevel = 0;
	destination.origin = { 0, 0, 0 };
	destination.aspect = WGPUTextureAspect_All;

	WGPUTextureDataLayout source;
	source.nextInChain = nullptr;
	source.offset = 0;
	source.bytesPerRow = 4 * textureDesc.size.width;
	source.rowsPerImage = textureDesc.size.height;

	// Upload data to the GPU texture
	WGPUQueue queue = wgpuDeviceGetQueue(device);
	wgpuQueueWriteTexture(queue, &destination, pixelData, 4 * width * height, &source, &textureDesc.size);

	stbi_image_free(pixelData);

	return texture;
}
```
````

## Generating mip-maps

We automatically infer the mip level count from the texture size, as noted in the previous chapter. Then we upload each level one by one, filling each level by averaging the previous one.

````{tab} With webgpu.hpp
```C++
Texture loadTexture(const fs::path& path, Device device) {
	// [...]
	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.mipLevelCount = bit_width(std::max(textureDesc.size.width, textureDesc.size.height));

	// [...]

	// Create image data
	Extent3D mipLevelSize = textureDesc.size;
	std::vector<uint8_t> previousLevelPixels;
	Extent3D previousMipLevelSize;
	for (uint32_t level = 0; level < textureDesc.mipLevelCount; ++level) {
		std::vector<uint8_t> pixels(4 * mipLevelSize.width * mipLevelSize.height);
		if (level == 0) {
			// We cannot really avoid this copy since we need this
			// in previousLevelPixels at the next iteration
			memcpy(pixels.data(), pixelData, pixels.size());
		}
		else {
			// Create mip level data
			for (uint32_t i = 0; i < mipLevelSize.width; ++i) {
				for (uint32_t j = 0; j < mipLevelSize.height; ++j) {
					uint8_t* p = &pixels[4 * (j * mipLevelSize.width + i)];
					// Get the corresponding 4 pixels from the previous level
					uint8_t* p00 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 0))];
					uint8_t* p01 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 1))];
					uint8_t* p10 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 0))];
					uint8_t* p11 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 1))];
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
		device.getQueue().writeTexture(destination, pixels.data(), pixels.size(), source, mipLevelSize);

		// Prepare for next iteration
		previousLevelPixels = std::move(pixels);
		previousMipLevelSize = mipLevelSize;
		mipLevelSize.width /= 2;
		mipLevelSize.height /= 2;
	}

	stbi_image_free(pixelData);

	return texture;
}
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUTexture loadTexture(const fs::path& path, WGPUDevice device) {
	// [...]
	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.mipLevelCount = bit_width(std::max(textureDesc.size.width, textureDesc.size.height));

	// [...]

	// Create image data
	WGPUQueue queue = wgpuDeviceGetQueue(device);
	WGPUExtent3D mipLevelSize = textureDesc.size;
	std::vector<uint8_t> previousLevelPixels;
	WGPUExtent3D previousMipLevelSize;
	for (uint32_t level = 0; level < textureDesc.mipLevelCount; ++level) {
		std::vector<uint8_t> pixels(4 * mipLevelSize.width * mipLevelSize.height);
		if (level == 0) {
			// We cannot really avoid this copy since we need this
			// in previousLevelPixels at the next iteration
			memcpy(pixels.data(), pixelData, pixels.size());
		}
		else {
			// Create mip level data
			for (uint32_t i = 0; i < mipLevelSize.width; ++i) {
				for (uint32_t j = 0; j < mipLevelSize.height; ++j) {
					uint8_t* p = &pixels[4 * (j * mipLevelSize.width + i)];
					// Get the corresponding 4 pixels from the previous level
					uint8_t* p00 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 0))];
					uint8_t* p01 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 1))];
					uint8_t* p10 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 0))];
					uint8_t* p11 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 1))];
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
		wgpuQueueWriteTexture(queue, &destination, pixelData, 4 * width * height, &source, &mipLevelSize);

		// Prepare for next iteration
		previousLevelPixels = std::move(pixels);
		previousMipLevelSize = mipLevelSize;
		mipLevelSize.width /= 2;
		mipLevelSize.height /= 2;
	}

	stbi_image_free(pixelData);

	return texture;
}
```
````

## Texture view

To create the texture view that is used by the sampler, we need the *mip level count* and *format*. We can modify the `loadTexture` either to return these information, or as I do here to create an appropriate texture view and return it.

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
```
````

Copy any image to `resources/texture.jpg` and you should see it loaded on the 3D plane!

```{note}
Here the texture view pointer passed to `loadTexture` is `&textureView`, namely the address of the variable `textureView`. Even if the variable itself is initialized to null, **its address**, called `pTextureView` in the function, **is not null**, and thus a view is created and returned.
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

But that's not it. We also need to convert the UV coordinates from the OpenGL-like convention used by the OBJ file format to the WebGPU/Direct3D/Metal convention that we are using. In `loadGeometryFromObj` replace the $v$ coordinate by $1 - v$:

```C++
// Fix the UV convention
vertexData[offset + i].uv = {
	attrib.texcoords[2 * idx.texcoord_index + 0],
	1 - attrib.texcoords[2 * idx.texcoord_index + 1]
};
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

Even if the lighting model is quite basic, we are now able to load and display complex 3D models with texture!

The next part will help us organize a bit our code base, as it is getting too long to be left as a monolithic main. Once this is done, we'll proceed to the last part of building a basic real-time 3D renderer: lighting.

````{tab} With webgpu.hpp
*Resulting code:* [`step076`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step076)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step076-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step076-vanilla)
````
