Loading from file (WIP)
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step075`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step075-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075-vanilla)
````

TODO

We use the stb_image single-header library to load basic image types (png, jpg, bmp, ...).

Save [stb_image.h](https://raw.githubusercontent.com/nothings/stb/master/stb_image.h) in your source tree and include it in your main file:

```C++
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
```

Basic use:

```C++
int width, height, channels;
unsigned char *data = stbi_load(path.string().c_str(), &width, &height, &channels, 0);

// [...]

stbi_image_free(data);
```

```C++
Texture loadTexture(const fs::path& path, Device device) {
	int width, height, channels;
	unsigned char *pixelData = stbi_load(path.string().c_str(), &width, &height, &channels, 4 /* force 4 channels */);
	if (nullptr == pixelData) return nullptr;

	TextureDescriptor textureDesc;
	textureDesc.dimension = TextureDimension::_2D;
	textureDesc.format = TextureFormat::RGBA8Unorm;
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

	device.getQueue().writeTexture(destination, pixelData, 4 * width * height, source, textureDesc.size);

	stbi_image_free(pixelData);

	return texture;
}
```

```C++
// Fix the UV convention
vertexData[offset + i].uv = {
	attrib.texcoords[2 * idx.texcoord_index + 0],
	1 - attrib.texcoords[2 * idx.texcoord_index + 1]
};
```

Unzip [fourareen.zip](../../data/fourareen.zip) in your resource directory (special thanks to Scottish Maritime Museum for [sharing this model](https://sketchfab.com/3d-models/venus-a-shetland-fourareen-ce4d6915e1d041459e08f2d8da521e86)!).

```C++
bool success = loadGeometryFromObj(RESOURCE_DIR "/fourareen.obj", vertexData);
// [...]
Texture texture = loadTexture(RESOURCE_DIR "/fourareen2K_albedo.jpg", device);
```

```{figure} /images/fourareen.png
:align: center
:class: with-shadow

```

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step075`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step075-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step075-vanilla)
````
