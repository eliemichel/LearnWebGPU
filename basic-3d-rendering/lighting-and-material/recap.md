Recap
=====

````{tab} With webgpu.hpp
*Resulting code:* [`step100`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-vanilla)
````

In this first part, we connect the dots that we already have, so that we can focus in the next chapters on the material and lighting models.

Basic shading
-------------

Let's recap what we have seen in the [Basic shading](../3d-meshes/basic-shading.md) chapter.

 - The shaded look of a surface element depends on its **normal**.
 - This look also depends on **light sources**, and in particular on their direction.
 - The most basic shading we tested with is `shading = max(0.0, dot(lightDirection, normal))`. This is a (lambertian) **diffuse** shading.

```{seealso}
For more details about the rational behind this simple diffuse model, you can consult this nice introduction on Scratchpixel: [Diffuse and Lambertian Shading](https://www.scratchapixel.com/lessons/3d-basic-rendering/introduction-to-shading/diffuse-lambertian-shading.html).
```

We can plug this with the texture sampling, by using the texture as the base color before applying the shading:

```rust
@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	// Compute shading
	let normal = normalize(in.normal);
	let lightDirection1 = vec3<f32>(0.5, -0.9, 0.1);
	let lightDirection2 = vec3<f32>(0.2, 0.4, 0.3);
	let lightColor1 = vec3<f32>(1.0, 0.9, 0.6);
	let lightColor2 = vec3<f32>(0.6, 0.9, 1.0);
	let shading1 = max(0.0, dot(lightDirection1, normal));
	let shading2 = max(0.0, dot(lightDirection2, normal));
	let shading = shading1 * lightColor1 + shading2 * lightColor2;
	
	// Sample texture
	let baseColor = textureSample(baseColorTexture, textureSampler, in.uv).rgb;

	// Combine texture and lighting
	let color = baseColor * shading;

	// Gamma-correction
	let corrected_color = pow(color, vec3<f32>(2.2));
	return vec4<f32>(corrected_color, uMyUniforms.color.a);
}
```

```{figure} /images/lit-boat.png
:align: center
:class: with-shadow
The boat model with some basic lighting.
```

Interaction
-----------

To facilitate the further testing of lighting and materials, let's make the light sources dynamic and connect them to our GUI.

### Lighting uniforms

We are going to create 2 private methods to contain all the light-related code. We also create a new independent uniform buffer:

````{tab} With webgpu.hpp
```C++
// In class Application:

// Private methods
void initLighting();
void updateLighting();

// Private attributes
struct LightingUniforms {
	std::array<glm::vec4, 2> directions;
	std::array<glm::vec4, 2> colors;
};
static_assert(sizeof(LightingUniforms) % 16 == 0);
wgpu::Buffer m_lightingUniformBuffer = nullptr;
LightingUniforms m_lightingUniforms;
```
````

````{tab} Vanilla webgpu.h
```C++
// In class Application:

// Private methods
void initLighting();
void updateLighting();

// Private attributes
struct LightingUniforms {
	std::array<glm::vec4, 2> directions;
	std::array<glm::vec4, 2> colors;
};
static_assert(sizeof(LightingUniforms) % 16 == 0);
WGPUBuffer m_lightingUniformBuffer = nullptr;
LightingUniforms m_lightingUniforms;
```
````

The `initLighting()` method must be called **after** all the basic WebGPU objects have been initialized (e.g., the device) **but before** finalizing the bind group and its layout.

Since this init needs to modify the `bindingLayoutEntries` and `bindings` vectors, we make them attributes instead of variables local to `onInit()`.

````{tab} With webgpu.hpp
```C++
// Private attributes
std::vector<wgpu::BindGroupLayoutEntry> m_bindingLayoutEntries;
std::vector<wgpu::BindGroupEntry> m_bindings;
```
````

````{tab} Vanilla webgpu.h
```C++
// Private attributes
std::vector<WGPUBindGroupLayoutEntry> m_bindingLayoutEntries;
std::vector<WGPUBindGroupEntry> m_bindings;
```
````

Overall the order in `onInit()` should look like:

```C++
bool Application::onInit() {
	// [...] Init window, device, swap chain
	// [...] Init resources (shader, geometry, texture, sampler, depth buffer)
	// [...] Init binding entries and their layout
	initLighting();
	// [...] Create render pipeline and bind group
	// [...] Init GUI
	return true;
}
```

```{caution}
Note how I turned the direction and color to `vec4` instead of `vec3`. This is because of [alignment rules](https://www.w3.org/TR/WGSL/#alignment-and-size): a `vec3` is aligned as if it was a `vec4`.
```

We can now reproduces the initialization of `MyUniform` to prepare our new `LightingUniforms` buffer:

````{tab} With webgpu.hpp
```C++
void Application::initLighting() {
	Queue queue = m_device.getQueue();

	// Create uniform buffer
	BufferDescriptor bufferDesc;
	bufferDesc.size = sizeof(LightingUniforms);
	bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;
	bufferDesc.mappedAtCreation = false;
	m_lightingUniformBuffer = m_device.createBuffer(bufferDesc);

	// Upload the initial value of the uniforms
	m_lightingUniforms.directions = {
		vec4{0.5, -0.9, 0.1, 0.0},
		vec4{0.2, 0.4, 0.3, 0.0}
	};
	m_lightingUniforms.colors = {
		vec4{1.0, 0.9, 0.6, 1.0},
		vec4{0.6, 0.9, 1.0, 1.0}
	};

	queue.writeBuffer(m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));

	// Setup binding
	uint32_t bindingIndex = (uint32_t)m_bindingLayoutEntries.size();
	BindGroupLayoutEntry bindingLayout = Default;
	bindingLayout.binding = bindingIndex;
	bindingLayout.visibility = ShaderStage::Fragment;
	bindingLayout.buffer.type = BufferBindingType::Uniform;
	bindingLayout.buffer.minBindingSize = sizeof(LightingUniforms);
	m_bindingLayoutEntries.push_back(bindingLayout);

	BindGroupEntry binding = Default;
	binding.binding = bindingIndex;
	binding.buffer = m_lightingUniformBuffer;
	binding.offset = 0;
	binding.size = sizeof(LightingUniforms);
	m_bindings.push_back(binding);
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::initLighting() {
	WGPUQueue queue = wgpuDeviceGetQueue(m_device);

	// Create uniform buffer
	WGPUBufferDescriptor bufferDesc;
	bufferDesc.nextInChain = nullptr;
	bufferDesc.size = sizeof(LightingUniforms);
	bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;
	bufferDesc.mappedAtCreation = false;
	m_lightingUniformBuffer = wgpuDeviceCreateBuffer(m_device, &bufferDesc);

	// Upload the initial value of the uniforms
	m_lightingUniforms.directions = {
		vec4{0.5, -0.9, 0.1, 0.0},
		vec4{0.2, 0.4, 0.3, 0.0}
	};
	m_lightingUniforms.colors = {
		vec4{1.0, 0.9, 0.6, 1.0},
		vec4{0.6, 0.9, 1.0, 1.0}
	};

	wgpuQueueWriteBuffer(queue, m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));

	// Setup binding
	uint32_t bindingIndex = (uint32_t)m_bindingLayoutEntries.size();
	WGPUBindGroupLayoutEntry bindingLayout;
	setDefaults(bindingLayout);
	bindingLayout.binding = bindingIndex;
	bindingLayout.visibility = WGPUShaderStage_Fragment;
	bindingLayout.buffer.type = WGPUBufferBindingType_Uniform;
	bindingLayout.buffer.minBindingSize = sizeof(LightingUniforms);
	m_bindingLayoutEntries.push_back(bindingLayout);

	WGPUBindGroupEntry binding;
	setDefaults(binding);
	binding.binding = bindingIndex;
	binding.buffer = m_lightingUniformBuffer;
	binding.offset = 0;
	binding.size = sizeof(LightingUniforms);
	m_bindings.push_back(binding);
}
```
````

````{note}
Since we are adding a new uniform buffer, don't forget to update the required limits:

```C++
requiredLimits.limits.maxUniformBuffersPerShaderStage = 2;
```
````

On the shader side, we reorganize to use this new uniform buffer and make the code more flexible to the introduction of more light sources:

```rust
/**
 * A structure holding the lighting settings
 */
struct LightingUniforms {
	directions: array<vec4<f32>, 2>,
	colors: array<vec4<f32>, 2>,
}

@group(0) @binding(3) var<uniform> uLighting: LightingUniforms;

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
	// Compute shading
	let normal = normalize(in.normal);
	var shading = vec3<f32>(0.0);
	for (var i: i32 = 0; i < 2; i++) {
		let direction = normalize(uLighting.directions[i].xyz);
		let color = uLighting.colors[i].rgb;
		shading += max(0.0, dot(direction, normal)) * color;
	}
	
	// Sample texture
	let baseColor = textureSample(baseColorTexture, textureSampler, in.uv).rgb;

	// Combine texture and lighting
	let color = baseColor * shading;

	// Gamma-correction
	let corrected_color = pow(color, vec3<f32>(2.2));
	return vec4<f32>(corrected_color, uMyUniforms.color.a);
}
```

Finally, let's connect the GUI by replacing the "Hello, world" panel in `updateGui()`:

```C++
// In Application::updateGui:
ImGui::Begin("Lighting");
ImGui::ColorEdit3("Color #0", glm::value_ptr(m_lightingUniforms.colors[0]));
ImGui::DragFloat3("Direction #0", glm::value_ptr(m_lightingUniforms.directions[0]));
ImGui::ColorEdit3("Color #1", glm::value_ptr(m_lightingUniforms.colors[1]));
ImGui::DragFloat3("Direction #1", glm::value_ptr(m_lightingUniforms.directions[1]));
ImGui::End();
```

```{note}
The `glm::value_ptr` function returns a pointer to where the glm object's raw data is stored, which is what ImGui needs to operate. In practice for vectors it is equivalent to using the address of the vector object itself.
```

And at each frame we copy the values that the GUI manipulates to the GPU-side buffer.

````{tab} With webgpu.hpp
```C++
void Application::updateLighting() {
	Queue queue = m_device.getQueue();
	queue.writeBuffer(m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::updateLighting() {
	WGPUQueue queue = wgpuDeviceGetQueue(m_device);
	wgpuQueueWriteBuffer(queue, m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
}
```
````

```{figure} /images/light-color-ui.png
:align: center
:class: with-shadow
The UI is connected to the lighting uniforms.
```

### Multiple textures

We are soon going to use more than one texture. Since we are doing a bit of a refactoring in this chapter, let us also make our code flexible to the addition of new textures.

We move the texture loading and associated binding in a dedicated method:

````{tab} With webgpu.hpp
```C++
bool Application::initTexture(const std::filesystem::path &path) {
	// Create a texture
	TextureView textureView = nullptr;
	Texture texture = ResourceManager::loadTexture(path, m_device, &textureView);
	if (!texture) {
		std::cerr << "Could not load texture!" << std::endl;
		return false;
	}
	m_textures.push_back(texture);

	// Setup binding
	uint32_t bindingIndex = (uint32_t)m_bindingLayoutEntries.size();
	BindGroupLayoutEntry bindingLayout = Default;
	bindingLayout.binding = bindingIndex;
	bindingLayout.visibility = ShaderStage::Fragment;
	bindingLayout.texture.sampleType = TextureSampleType::Float;
	bindingLayout.texture.viewDimension = TextureViewDimension::_2D;
	m_bindingLayoutEntries.push_back(bindingLayout);

	BindGroupEntry binding = Default;
	binding.binding = bindingIndex;
	binding.textureView = textureView;
	m_bindings.push_back(binding);

	return true;
}
```
````

````{tab} Vanilla webgpu.h
```C++
bool Application::initTexture(const std::filesystem::path &path) {
	// Create a texture
	WGPUTextureView textureView = nullptr;
	WGPUTexture texture = ResourceManager::loadTexture(path, m_device, &textureView);
	if (!texture) {
		std::cerr << "Could not load texture!" << std::endl;
		return false;
	}
	m_textures.push_back(texture);

	// Setup binding
	uint32_t bindingIndex = (uint32_t)m_bindingLayoutEntries.size();
	WGPUBindGroupLayoutEntry bindingLayout;
	setDefaults(bindingLayout);
	bindingLayout.binding = bindingIndex;
	bindingLayout.visibility = WGPUShaderStage_Fragment;
	bindingLayout.texture.sampleType = WGPUTextureSampleType_Float;
	bindingLayout.texture.viewDimension = WGPUTextureViewDimension_2D;
	m_bindingLayoutEntries.push_back(bindingLayout);

	WGPUBindGroupEntry binding;
	setDefaults(binding)
	binding.binding = bindingIndex;
	binding.textureView = textureView;
	m_bindings.push_back(binding);

	return true;
}
```
````

The init simply becomes, just before `initLighting()`:

```C++
// In onInit()
if (!initTexture(RESOURCE_DIR "/fourareen2K_albedo.jpg")) return false;
```

Note that this also assumes that the `m_texture` attribute is replaced by a vector:

````{tab} With webgpu.hpp
```C++
// In Application class:
std::vector<wgpu::Texture> m_textures;

// In Application.cpp
void Application::onFinish() {
	for (auto texture : m_textures) {
		texture.destroy();
	}
	// [...]
}
```
````

````{tab} Vanilla webgpu.h
```C++
// In Application class:
std::vector<WGPUTexture> m_textures;

// In Application.cpp
void Application::onFinish() {
	for (auto texture : m_textures) {
		wgpuTextureDestroy(texture);
	}
	// [...]
}
```
````

And I swapped the binding of the sampler and the texture, so that textures can be consecutive (not that it is a technical requirements, but it was easier to organize this way).

```rust
@group(0) @binding(1) var textureSampler: sampler;
//                 ^ Was 2
@group(0) @binding(2) var baseColorTexture: texture_2d<f32>;
//                 ^ Was 1
```

Complement
----------

### Custom GUI input

This `ImGui::DragFloat3` input is not ideal for a direction. It is not so intuitive, and does not ensure that the direction vector always has a length of 1. We can easily create our own input `ImGui::DragDirection` to expose the direction as 2 polar angles:

```C++
#include <glm/gtx/polar_coordinates.hpp>

namespace ImGui {
bool DragDirection(const char* label, vec4& direction) {
	vec2 angles = glm::degrees(glm::polar(vec3(direction)));
	bool changed = ImGui::DragFloat2(label, glm::value_ptr(angles));
	direction = vec4(glm::euclidean(glm::radians(angles)), direction.w);
	return changed;
}
} // namespace ImGui
```

It can be used as follows:

```C++
changed = ImGui::DragDirection("Direction #0", m_lightingUniforms.directions[0]) || changed;
```

### Slight optimization

Instead of uploading the lighting uniform buffer at each frame even when nothing changes, we can get from ImGui the information of whether the fields changed:

````{tab} With webgpu.hpp
```C++
// In class Application
bool m_lightingUniformsChanged = false;

// In Application.cpp
void Application::updateLighting() {
	if (m_lightingUniformsChanged) {
		Queue queue = m_device.getQueue();
		queue.writeBuffer(m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
	}
}

// In Application::updateGui:
bool changed = false;
ImGui::Begin("Lighting");
changed = ImGui::ColorEdit3("Color #0", glm::value_ptr(m_lightingUniforms.colors[0])) || changed;
changed = ImGui::DragFloat3("Direction #0", glm::value_ptr(m_lightingUniforms.directions[0])) || changed;
changed = ImGui::ColorEdit3("Color #1", glm::value_ptr(m_lightingUniforms.colors[1])) || changed;
changed = ImGui::DragFloat3("Direction #1", glm::value_ptr(m_lightingUniforms.directions[1])) || changed;
ImGui::End();
m_lightingUniformsChanged = changed;
```
````

````{tab} Vanilla webgpu.h
```C++
// In class Application
bool m_lightingUniformsChanged = false;

// In Application.cpp
void Application::updateLighting() {
	if (m_lightingUniformsChanged) {
		WGPUQueue queue = wgpuDeviceGetQueue(m_device);
		wgpuQueueWriteBuffer(queue, m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
	}
}

// In Application::updateGui:
bool changed = false;
ImGui::Begin("Lighting");
changed = ImGui::ColorEdit3("Color #0", glm::value_ptr(m_lightingUniforms.colors[0])) || changed;
changed = ImGui::DragFloat3("Direction #0", glm::value_ptr(m_lightingUniforms.directions[0])) || changed;
changed = ImGui::ColorEdit3("Color #1", glm::value_ptr(m_lightingUniforms.colors[1])) || changed;
changed = ImGui::DragFloat3("Direction #1", glm::value_ptr(m_lightingUniforms.directions[1])) || changed;
ImGui::End();
m_lightingUniformsChanged = changed;
```
````

Conclusion
----------

In this chapter we have:

 - Connected diffuse shading with textures,
 - Connected lighting with GUI.
 - Created a custom GUI.
 - Refactored a bit the code to make room for more textures.

Okey, this was again a bit about organizing things... but we can now dive into material models for real!

````{tab} With webgpu.hpp
*Resulting code:* [`step100`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-vanilla)
````
