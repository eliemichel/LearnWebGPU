Loading from file (WIP)
=================

````{tab} With webgpu.hpp
*Resulting code:* [`step037`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step037-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-vanilla)
````

TODO

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
*Resulting code:* [`step037`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step037-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step037-vanilla)
````
