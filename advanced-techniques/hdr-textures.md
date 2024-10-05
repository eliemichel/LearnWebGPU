High Dynamic Range Textures (<span class="bullet">🟠</span>WIP)
===========================

````{tab} With webgpu.hpp
*Resulting code:* [`step120`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step120)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step120-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step120-vanilla)
````

*(NB: This used to be placed right after [Image-Based Lighting](../basic-3d-rendering/lighting-and-material/ibl.md))*

High Dynamic Range
------------------

Load [`autumn_park_4k.exr`](../data/autumn_park_4k.exr):

```C++
if (!initTexture(RESOURCE_DIR "/autumn_park_4k.exr")) return false;
```

Since stb_image, the library we use to load PNGs, does not know EXR file, we use [tinyexr](https://github.com/syoyo/tinyexr), which is integrated in a similar spirit to our other dependencies.

Download [`tinyexr.h`](https://github.com/syoyo/tinyexr/raw/02310c77e5156c36fedf6cf810c4071e3f83906f/tinyexr.h), [`miniz.c`](https://raw.githubusercontent.com/syoyo/tinyexr/02310c77e5156c36fedf6cf810c4071e3f83906f/deps/miniz/miniz.c) and [`miniz.h`](https://raw.githubusercontent.com/syoyo/tinyexr/02310c77e5156c36fedf6cf810c4071e3f83906f/deps/miniz/miniz.h) into your source tree and add the following to `implementations.cpp`:

```C++
#define TINYEXR_IMPLEMENTATION
#include "tinyexr.h"
```

Also add `miniz.c` and (optionally) `miniz.h`/`tinyexr.h` to the CMakeLists:

```CMake
add_executable(App
	# [...]
	miniz.h
	miniz.c
	tinyexr.h
)
```

We also need some more tuning to our CMakeLists:

```CMake
# Same as adding #define NOMINMAX in all files
target_compile_definitions(App PRIVATE NOMINMAX)

if(MSVC)
	# /wd4706 and /wd4127 are required by tinyexr/miniz
	target_compile_options(App PRIVATE /wd4201 /wd4706 /wd4127)
endif(MSVC)
```

In the resource manager, we create a copy of `loadTexture` called `loadExrTexture` where we use TinyEXR instead of stb_image and load data as float rather than 8-bit integers, which affects the creation of mipmaps:

```C++
Texture ResourceManager::loadExrTexture(const path& path, Device device, TextureView* pTextureView) {
	int width, height;
	float* pixelData; // width * height * RGBA
	const char* err = nullptr;

	int ret = LoadEXR(&pixelData, &width, &height, path.string().c_str(), &err);
	if (ret != TINYEXR_SUCCESS) {
		if (err) {
			std::cerr << "Could not load EXR file '" << path << "': " << err << std::endl;
			FreeEXRErrorMessage(err); // release memory of error message.
		}
		return nullptr;
	}

	TextureDescriptor textureDesc;
	textureDesc.dimension = TextureDimension::_2D;
	textureDesc.format = TextureFormat::RGBA16Float;
	textureDesc.size = { (unsigned int)width, (unsigned int)height, 1 };
	textureDesc.mipLevelCount = bit_width(std::max(textureDesc.size.width, textureDesc.size.height));
	textureDesc.sampleCount = 1;
	textureDesc.usage = TextureUsage::TextureBinding | TextureUsage::CopyDst;
	textureDesc.viewFormatCount = 0;
	textureDesc.viewFormats = nullptr;
	Texture texture = device.createTexture(textureDesc);

	// Convert to 16-bit floats because it is enough for a HDR
	// and 32-bit would require to enable a particular device feature to be filterable
	// (see https://www.w3.org/TR/webgpu/#texture-format-caps)
	std::vector<float16_t> halfPixels(4 * width * height);
	for (int i = 0; i < halfPixels.size(); ++i) {
		halfPixels[i] = pixelData[i];
	}
	free(pixelData);

	writeMipMaps(device, texture, textureDesc.size, textureDesc.mipLevelCount, halfPixels.data());

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

Note that in order to avoid duplicating the mip-map creation part, I isolated this templated utility function:

```C++
template<typename component_t>
static void writeMipMaps(
	Device device,
	Texture texture,
	Extent3D textureSize,
	uint32_t mipLevelCount,
	const component_t* pixelData
) {
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
	std::vector<component_t> previousLevelPixels;
	Extent3D previousMipLevelSize;
	for (uint32_t level = 0; level < mipLevelCount; ++level) {
		std::vector<component_t> pixels(4 * mipLevelSize.width * mipLevelSize.height);
		if (level == 0) {
			// We cannot really avoid this copy since we need this
			// in previousLevelPixels at the next iteration
			memcpy(pixels.data(), pixelData, pixels.size() * sizeof(component_t));
		}
		else {
			// Create mip level data
			for (uint32_t i = 0; i < mipLevelSize.width; ++i) {
				for (uint32_t j = 0; j < mipLevelSize.height; ++j) {
					component_t* p = &pixels[4 * (j * mipLevelSize.width + i)];
					// Get the corresponding 4 pixels from the previous level
					component_t* p00 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 0))];
					component_t* p01 = &previousLevelPixels[4 * ((2 * j + 0) * previousMipLevelSize.width + (2 * i + 1))];
					component_t* p10 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 0))];
					component_t* p11 = &previousLevelPixels[4 * ((2 * j + 1) * previousMipLevelSize.width + (2 * i + 1))];
					// Average
					p[0] = (p00[0] + p01[0] + p10[0] + p11[0]) / (component_t)4;
					p[1] = (p00[1] + p01[1] + p10[1] + p11[1]) / (component_t)4;
					p[2] = (p00[2] + p01[2] + p10[2] + p11[2]) / (component_t)4;
					p[3] = (p00[3] + p01[3] + p10[3] + p11[3]) / (component_t)4;
				}
			}
		}

		// Upload data to the GPU texture
		destination.mipLevel = level;
		source.bytesPerRow = 4 * mipLevelSize.width * sizeof(component_t);
		source.rowsPerImage = mipLevelSize.height;
		queue.writeTexture(destination, pixels.data(), pixels.size() * sizeof(component_t), source, mipLevelSize);

		previousLevelPixels = std::move(pixels);
		previousMipLevelSize = mipLevelSize;
		mipLevelSize.width /= 2;
		mipLevelSize.height /= 2;
	}
}
```

All there is to do now is call in `initTexture` one or the other of these loading functions depending on the file extension:

```C++
bool Application::initTexture(const std::filesystem::path &path) {
	// Create a texture
	TextureView textureView = nullptr;
	Texture texture =
		path.extension() == ".exr"
		? ResourceManager::loadExrTexture(path, m_device, &textureView)
		: ResourceManager::loadTexture(path, m_device, &textureView);
	// [...]
}
```

```{important}
The [texture format capabilities table](https://www.w3.org/TR/webgpu/#texture-format-caps) shows that in order to allow filtering for float32 textures, we need to enable the `float32-filterable` **feature** when creating the device.
```

We use [`float16_t.hpp`](../data/float16_t.hpp) because C++ does not have a 16-bit float type out of the box.

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step120`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step120)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step120-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step120-vanilla)
````
