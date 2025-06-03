Loading from file <span class="bullet">🟢</span>
=================

```{lit-setup}
:tangle-root: 037 - Loading from file - Next - vanilla
:parent: 034 - Index Buffer - Next - vanilla
:alias: Vanilla
```

```{lit-setup}
:tangle-root: 037 - Loading from file - Next
:parent: 034 - Index Buffer - Next
```

````{tab} With webgpu.hpp
*Resulting code:* [`step037-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step037-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-vanilla-next)
````

Now that we are familiar with the representation of geometric data that the GPU expect, we can load it from a file instead of hard-coding it in the source code. This is the occasion to introduce some basic **resource file management** to our project (although this is not specific to WebGPU).

File format
-----------

### Example

The file format I introduce here is not standard, but it is simple enough to parse. Here is the content of `webgpu.txt`, which I put in a `resources/` directory:

```{lit} C++, file: resources/webgpu.txt (also for tangle root "Vanilla")
# in resources/webgpu.txt
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

It is basically the content of the `pointData` and `indexData` defined previously directly in our C++ code (in `Application::InitializeBuffers()`), where a line of the form `[section name]` introduces each section. Lines that are empty or starting with a `#` are ignored.

### Parser

I am not going to detail the parser. I believe it is rather simple to understand, and it is **not the core topic** of this lecture.

```{note}
Once we'll start using **3D data** we will switch to a more **standard format** anyways.
```

You may simply copy this `loadGeometry` function at the beginning of the `Application.cpp` file (we will later on move this to a dedicated `ResourceManager.cpp`):

```C++
#include <vector>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <iostream>

bool loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData
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

Loading resources from disc
---------------------------

### Basic approach

We can replace the definition of the `pointData` and `indexData` vectors by a call to our new `loadGeometry` function in `Application::InitializeBuffers()`.

```{lit} C++, InitializeBuffers method (hidden, replace, also for tangle root "Vanilla")
bool Application::InitializeBuffers() {
	// 1. Load from disk into CPU-side vectors pointData and indexData
	{{Load geometry data from file}}

	// 2. Create GPU buffers and upload data to them
	{{Create point buffer}}
	{{Create index buffer}}
	return true;
}
```

```{lit} C++, Load geometry data from file (also for tangle root "Vanilla")
// At the beginning of InitializeBuffers()
// Define data vectors, but without filling them in
std::vector<float> pointData;
std::vector<uint16_t> indexData;
// Here we use the new 'loadGeometry' function:
bool success = loadGeometry("resources/webgpu.txt", pointData, indexData);
if (!success) return false;

m_indexCount = static_cast<uint32_t>(indexData.size());
```

A **problem** we have with this hard-coded relative path is that its interpretation depends on the directory from which you run your executable:

```
my_project> ./build/App
(Working all right)
my_project> cd build
my_project/build> ./App
Could not load geometry!
```

In the second case, your program tries to open `my_project/build/resources/webgpu.txt`, which does not exist. There are a few options to address this:

 - **Option A:** Don't care, just call your program **from the right directory**. It could be annoying, and the problem is that IDEs usually run the executable from `build/` or even a subdirectory of `build/`.
 - **Option B:** Use an **absolute path**. This will only work on your machine, which is quite of a limitation.
 - **Option C:** Use an absolute path that is **automatically generated** thanks to CMake. This is what we'll do.
 - **Option D:** Use a **command line argument** to tell the program where to find the resource directory. This is an interesting option, which can be used in combination with *Option C*, but requires a bit more work.
 - **Option E:** Automatically **copy the resources** in the directory from which your IDE launches the program. This will be a problem once we try to modify resources on-the-fly while the program is running (which is quite handy when writing shaders).

I suggest we go for **Option C** for development, while enabling the possibility to easily switch to **Option A** when you want to distribute your program.

### Resource path resolution

We will do something like this:

```C++
#define RESOURCE_DIR "/home/me/src/my_project/resources"
loadGeometry(RESOURCE_DIR "/webgpu.txt", pointData, indexData);
```

Except that the `#define RESOURCE_DIR` will be added by CMake rather than being explicitly written in our source code!

```{tip}
When putting two *string literals* next to each others in a C or C++ source code, like in `loadGeometry("resource" "/webgpu.txt"`, ...), they are **automatically concatenated**. This is precisely meant for our use case to work!
```

To define `RESOURCE_DIR` in the `CMakeLists.txt` you can add this after creating the `App` target:

```{lit} CMake, Set the RESOURCE_DIR define (also for tangle root "Vanilla")
target_compile_definitions(App PRIVATE
	RESOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/resources"
)
```

The expression `${CMAKE_CURRENT_SOURCE_DIR}` is replaced by the content of CMake's variable [`CMAKE_CURRENT_SOURCE_DIR`](https://cmake.org/cmake/help/latest/variable/CMAKE_CURRENT_SOURCE_DIR.html), which is a built-in variable containing the full path to the parent directory of the `CMakeLists.txt` file that you are editing.

```{note}
When writing a CMake *function*, the `CMAKE_CURRENT_SOURCE_DIR` variable contains the directory of the `CMakeLists.txt` that is currently calling the function. If you want to refer to the directory of the `CMakeLists.txt` that defines the function, use [`CMAKE_CURRENT_LIST_DIR`](https://cmake.org/cmake/help/latest/variable/CMAKE_CURRENT_LIST_DIR.html) instead.
```

```{figure} /images/loading-from-file/transform-issue.png
:align: center
:class: with-shadow
It should now load the data file and display something like this. We'll get back to the translation issue later on!
```

Hardly recognized the WebGPU logo? Don't worry, we will re-center it soon!

### Portability

> 😒 Hey but in the end our executable uses an **absolute path**, so we have this **portability issue** when trying to share it, right?

Yes indeed, but we can easily add an option to globally change the resource directory when building a release that we want to be able to distribute:

```{lit} CMake, Set the RESOURCE_DIR define (replace, also for tangle root "Vanilla")
# We add an option to enable different settings when developing the app than
# when distributing it.
option(DEV_MODE "Set up development helper settings" ON)

if(DEV_MODE)
	# In dev mode, we load resources from the source tree, so that when we
	# dynamically edit resources (like shaders), these are correctly
	# versionned.
	target_compile_definitions(App PRIVATE
		RESOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/resources"
	)
else()
	# In release mode, we just load resources relatively to wherever the
	# executable is launched from, so that the binary is portable
	target_compile_definitions(App PRIVATE
		RESOURCE_DIR="./resources"
	)
endif()
```

You can then have 2 different builds of your project in two different directories:

```
cmake -B build-dev -DDEV_MODE=ON -DCMAKE_BUILD_TYPE=Debug
cmake -B build-release -DDEV_MODE=OFF -DCMAKE_BUILD_TYPE=Release
```

The first one for comfort of development, the second one for the portability of a release.

```{tip}
The `CMAKE_BUILD_TYPE` option is a built-in option of CMake that is very commonly used. Set it to `Debug` to compile your program with **debugging symbols** (see [debugging](/appendices/debugging.md)), at the expense of a slower and heavier executable. Set it to `Release` to have a **fast and lightweight** executable with no debugging safe-guard.

When using some CMake generators, like the Visual Studio one, this is ignored because the generated solution can switch from `Debug` to `Release` mode directly within the IDE instead of asking CMake.
```

### Building for the Web

> 😒 It is still not working when I try to build with emscripten!

Indeed, a Web page **does not have access to one's filesystem** (for good security reasons), plus it does not even make sense because the client will not have these files.

What we need to do in this case is to **ask emscripten to bundle the files within the application**. This is easily done with the [`--preload-file`](https://emscripten.org/docs/porting/files/packaging_files.html) link option, that preloads our content in a **virtual filesystem**.

```{lit} CMake, Emscripten-specific options (append, also for tangle root "Vanilla")
target_link_options(App PRIVATE
	--preload-file "${CMAKE_CURRENT_SOURCE_DIR}/resources"
)
```

This approach enables our C++ code to behave **as if there were files on a disk**, while in reality it is just a portion of data shipped with the app.

````{note}
We could precise `@resources` at the end of the `--preload-file` option to mean that the directory must be mounted at path `/resources` in the virtual filesystem. By default, the path of the preloaded file relative to `CMakeLists.txt` is used.

```CMake
target_link_options(App PRIVATE
	-sASYNCIFY
	--preload-file "${CMAKE_CURRENT_SOURCE_DIR}/resources@resources"
	#                                                    ^^^^^^^^^^ here
)
```
````

Resource Manager
----------------

In order to keep our project organized, I suggest we create a new `ResourceManager` class dedicated to all our resource **input/output procedures**, and in particular our new `loadGeometry`.

As advised when adding a C++ class, we add both a header file `ResourceManager.h` and an implementation file `ResourceManager.cpp`. We can already list them in our `CMakeLists.txt`:

```{lit} CMake, Define app target (replace, hidden, also for tangle root "Vanilla")
{{Dependency subdirectories}}

add_executable(App
	{{App source files}}
)

{{Link libraries}}

{{Set the RESOURCE_DIR define}}
```

```{lit} bash, App source files (append, also for tangle root "Vanilla")
# In the list of files of add_executable(App ...):
ResourceManager.h
ResourceManager.cpp
```

### Header file

The structure of a class header file always looks like this:

```{lit} C++, file: ResourceManager.h (also for tangle root "Vanilla")
// ResourceManager.h
#pragma once
{{ResourceManager.h includes}}

class ResourceManager {
public:
	{{Public ResourceManager members}}

private:
	{{Private ResourceManager members}}
};
```

````{note}
We do not have any `private` member for now, but we will later on.

```{lit} C++, Private ResourceManager members (hidden, also for tangle root "Vanilla")
```
````

We can declare in `public` members our `loadGeometry` function:

```{lit} C++, Public ResourceManager members (hidden, also for tangle root "Vanilla")
{{Declaration of ResourceManager::loadGeometry}}
```

```{lit} C++, Declaration of ResourceManager::loadGeometry (also for tangle root "Vanilla")
/**
 * Load a file from `path` using our ad-hoc format and populate the `pointData`
 * and `indexData` vectors.
 */
static bool loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData
);
```

```{note}
This method (like other loading methods of this guide) is defined as `static` so that **we do not need an instance** of the `ResourceManager` class. The `ResourceManager` class is actually only used as **some kind of namespace** here. I leave it as a class anyways because in a more advanced scenario you may want to turn this into a instantiable class.
```

Note that we need to add these includes:

```{lit} C++, ResourceManager.h includes (also for tangle root "Vanilla")
// Add to ResourceManager.h includes
#include <vector>
#include <filesystem>
```

### Implementation file

The implementation file only contains the definition of our `loadGeometry` function. **Do not forget** to prefix it with `ResourceManager::` and to include `"ResourceManager.h"`:

```C++
// In ResourceManager.cpp
#include "ResourceManager.h"

#include <fstream>
#include <sstream>
#include <string>
#include <iostream>

bool ResourceManager::loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData
) {
	// [...] Copy the content of the `loadGeometry()` defined above.
}
```

```{lit} C++, file: ResourceManager.cpp (hidden, also for tangle root "Vanilla")
// ResourceManager.cpp
#include "ResourceManager.h"
{{Other ResourceManager.cpp includes}}

{{ResourceManager member implementations}}
```

```{lit} C++, Other ResourceManager.cpp includes (hidden, also for tangle root "Vanilla")
// Add to ResourceManager.cpp includes
#include <fstream>
#include <sstream>
#include <string>
#include <iostream>
```

```{lit} C++, ResourceManager member implementations (hidden, also for tangle root "Vanilla")
{{Implementation of ResourceManager::loadGeometry}}
```

```{lit} C++, Implementation of ResourceManager::loadGeometry (hidden, also for tangle root "Vanilla")
bool ResourceManager::loadGeometry(
	const std::filesystem::path& path,
	std::vector<float>& pointData,
	std::vector<uint16_t>& indexData
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

### Usage

To use this new class in our `main.cpp` file, we must take care of including its header file:

```{lit} C++, Includes in Application.cpp (append, also for tangle root "Vanilla")
// In main.cpp
#include "ResourceManager.h"
```

And we must prefix `loadGeometry` with `ResourceManager::` when calling our static method:

```C++
bool success = ResourceManager::loadGeometry(RESOURCE_DIR "/webgpu.txt", pointData, indexData);
//             ^^^^^^^^^^^^^^^^^ don't forget this
```

```{lit} C++, Load geometry data from file (hidden, replace, also for tangle root "Vanilla")
// Define data vectors, but without filling them in
std::vector<float> pointData;
std::vector<uint16_t> indexData;
// Here we use the new 'loadGeometry' function:
bool success = ResourceManager::loadGeometry(RESOURCE_DIR  "/webgpu.txt", pointData, indexData);
if (!success) return false;

m_indexCount = static_cast<uint32_t>(indexData.size());
```

### Loading shaders

Now that we have a basic resource management mechanism, I strongly suggest we also use it to **load our shader code**, instead of hard-coding it in the C++ source as we have been doing from the beginning. We can even include the whole shader module creation boilerplate in our new `ResourceManager::loadShaderModule()`.

Let us first declare it in `ResourceManager.h`:

```{lit} C++, Public ResourceManager members (append, also for tangle root "Vanilla")
{{Declaration of ResourceManager::loadShaderModule}}
```

````{tab} With webgpu.hpp
```{lit} C++, Declaration of ResourceManager::loadShaderModule
/**
 * Create a shader module for a given WebGPU `device` from a WGSL shader source
 * loaded from file `path`.
 */
static wgpu::ShaderModule loadShaderModule(
	const std::filesystem::path& path,
	wgpu::Device device
);
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Declaration of ResourceManager::loadShaderModule (for tangle root "Vanilla")
/**
 * Create a shader module for a given WebGPU `device` from a WGSL shader source
 * loaded from file `path`.
 */
static WGPUShaderModule loadShaderModule(
	const std::filesystem::path& path,
	WGPUDevice device
);
```
````

We must not forget to include the webgpu header in `ResourceManager.h`:

`````{tab} With webgpu.hpp
```{lit} C++, ResourceManager.h includes (append)
#include <webgpu/webgpu.hpp>
```

````{caution}
Do **not** call `using namespace wgpu` in a **header file**, otherwise it forces all files that include this header to accept to use the `wgpu` namespace, which may create conflicts. This is why we prefix with `wgpu::` in the header, but of course we may call this in the implementation (.cpp) file:

```{lit} C++, Other ResourceManager.cpp includes (append)
using namespace wgpu;
```
````
`````

````{tab} Vanilla webgpu.h
```{lit} C++, ResourceManager.h includes (append, for tangle root "Vanilla")
#include <webgpu/webgpu.h>
```
````

And we may now define it in `ResourceManager.cpp`:

```{lit} C++, ResourceManager member implementations (hidden, append, also for tangle root "Vanilla")
{{Implementation of ResourceManager::loadShaderModule}}
```

````{tab} With webgpu.hpp
```{lit} C++, Implementation of ResourceManager::loadShaderModule
ShaderModule ResourceManager::loadShaderModule(const std::filesystem::path& path, Device device) {
	std::ifstream file(path);
	if (!file.is_open()) {
		std::cerr << "Could not load shader!" << std::endl;
		return nullptr;
	}
	file.seekg(0, std::ios::end);
	size_t size = file.tellg();
	std::string shaderSource(size, ' ');
	file.seekg(0);
	file.read(shaderSource.data(), size);

	ShaderSourceWGSL wgslDesc = Default;
    wgslDesc.code = StringView(shaderSource);
    ShaderModuleDescriptor shaderDesc = Default;
    shaderDesc.nextInChain = &wgslDesc.chain;
    shaderDesc.label = StringView(path.string());
    return device.createShaderModule(shaderDesc);
}
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Implementation of ResourceManager::loadShaderModule (for tangle root "Vanilla")
WGPUShaderModule ResourceManager::loadShaderModule(const std::filesystem::path& path, WGPUDevice device) {
	std::ifstream file(path);
	if (!file.is_open()) {
		std::cerr << "Could not load geometry!" << std::endl;
		return nullptr;
	}
	file.seekg(0, std::ios::end);
	size_t size = file.tellg();
	std::string shaderSource(size, ' ');
	file.seekg(0);
	file.read(shaderSource.data(), size);

	WGPUShaderSourceWGSL wgslDesc = WGPU_SHADER_SOURCE_WGSL_INIT;
    wgslDesc.code = toWgpuStringView(shaderSource);
    WGPUShaderModuleDescriptor shaderDesc = WGPU_SHADER_MODULE_DESCRIPTOR_INIT;
    shaderDesc.nextInChain = &wgslDesc.chain;
    shaderDesc.label = toWgpuStringView(path.string());
    return wgpuDeviceCreateShaderModule(device, &shaderDesc);
}
```
````

````{note}
With the *Vanilla webgpu.h* option, we use `toWgpuStringView`, so we need to include `webgpu-utils.h`:

```{lit} C++, Other ResourceManager.cpp includes (append, for tangle root "Vanilla")
// ResourceManager.cpp
#include "webgpu-utils.h"
```
````

We then move the original content of the shaderSource variable into `resources/shader.wgsl`:

```{lit} rust, file: resources/shader.wgsl (also for tangle root "Vanilla")
// In a new file 'resources/shader.wgsl'
// Move the content of the global `shaderSource` variable (and remove that variable from main.cpp)
{{Shader source}}
```

```{lit} C++, Shader source literal (hidden, replace, also for tangle root "Vanilla")
```

And we replace the module creation step in `Application::InitializePipeline()` by:

````{tab} With webgpu.hpp
```{lit} C++, Create Shader Module (replace)
std::cout << "Creating shader module..." << std::endl;
ShaderModule shaderModule = ResourceManager::loadShaderModule(RESOURCE_DIR "/shader.wgsl", m_device);
std::cout << "Shader module: " << shaderModule << std::endl;

// Check for errors
if (shaderModule == nullptr) return false;
```
````

````{tab} Vanilla webgpu.h
```{lit} C++, Create Shader Module (replace, for tangle root "Vanilla")
std::cout << "Creating shader module..." << std::endl;
WGPUShaderModule shaderModule = ResourceManager::loadShaderModule(RESOURCE_DIR "/shader.wgsl", m_device);
std::cout << "Shader module: " << shaderModule << std::endl;

// Check for errors
if (shaderModule == nullptr) return false;
```
````

This way, you **no longer need to rebuild** the application when you only want to change the shader!

Adjustment
-----------

So, as we noticed earlier, our shape is not well centered:

```{figure} /images/loading-from-file/transform-issue.png
:align: center
:class: with-shadow
Our loaded shape is a bit off, we should move it to better center it!
```

So how do we "move" the object? Similarly to how we fixed the ratio issue in the previous chapter, we can do it in the **vertex shader**, by adding something to the `x` and `y` coordinates:

```{lit} rust, Vertex shader position( replace, also for tangle root "Vanilla")
let ratio = 640.0 / 480.0; // The width and height of the target surface
let offset = vec2f(-0.6875, -0.463); // The offset that we want to apply to the position
out.position = vec4f(in.position.x + offset.x, (in.position.y + offset.y) * ratio, 0.0, 1.0);
```

```{note}
It is important to apply the scene transform **before** the viewport transform (the ratio). We will get back on this more in detail when adding the 3D to 2D projection transform needed for [drawing 3D meshes](/basic-3d-rendering/3d-meshes/index.md)!
```

```{figure} /images/loading-from-file/webgpu.png
:align: center
:class: with-shadow
The WebGPU Logo loaded from the file, with wrong colors.
```

Conclusion
----------

Loading geometric data from a file was an apparently simple change, but it was actually a good way to introduce multiple concerns that can easily become a nightmare if we don't pay attention to them:

 - Resource path resolution
 - File format
 - Transform (ratio, position)

We are going to come back on these from time to time to refine them. We are now ready to move on to a way to avoid hard-coded values in the shader and add a lot of flexibility, namely **uniforms**.

````{tab} With webgpu.hpp
*Resulting code:* [`step037-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-next)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step037-vanilla-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-vanilla-next)
````
