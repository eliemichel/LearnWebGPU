Lighting control <span class="bullet">🟡🟢</span>
================

````{tab} With webgpu.hpp
*Resulting code:* [`step100`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-vanilla)
````

```{important}
**November 17, 2024:** This chapter is marked with a secondary **green bullet 🟢** only to draw attention because there is a preview of the accompanying code available for a more recent version of Dawn and `wgpu-native`: [`step100-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-next). The content of this chapter still relies on older versions.
```

Now that we have elements of GUI, we can use them to expose for instance the **lighting settings** to the user. We want them to be able to **live tweak** the direction and color of our light sources.

Recap on basic shading
----------------------

Let's first recap what we have seen in the [Basic shading](../3d-meshes/basic-shading.md) chapter.

 - The shaded look of a surface element depends on its **normal**.
 - This look also depends on **light sources**, and in particular on their direction.
 - The most basic shading we tested with is `shading = max(0.0, dot(lightDirection, normal))`. This is a (lambertian) **diffuse** shading.

```{seealso}
For more details about the rational behind this simple diffuse model, you can consult this nice introduction on Scratchpixel: [Diffuse and Lambertian Shading](https://www.scratchapixel.com/lessons/3d-basic-rendering/introduction-to-shading/diffuse-lambertian-shading.html).
```

We can plug this with the texture sampling, by using the texture as the base color before applying the shading:

```rust
@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4f {
	// Compute shading
	let normal = normalize(in.normal);
	let lightDirection1 = vec3f(0.5, -0.9, 0.1);
	let lightDirection2 = vec3f(0.2, 0.4, 0.3);
	let lightColor1 = vec3f(1.0, 0.9, 0.6);
	let lightColor2 = vec3f(0.6, 0.9, 1.0);
	let shading1 = max(0.0, dot(lightDirection1, normal));
	let shading2 = max(0.0, dot(lightDirection2, normal));
	let shading = shading1 * lightColor1 + shading2 * lightColor2;
	
	// Sample texture
	let baseColor = textureSample(baseColorTexture, textureSampler, in.uv).rgb;

	// Combine texture and lighting
	let color = baseColor * shading;

	// Gamma-correction
	let corrected_color = pow(color, vec3f(2.2));
	return vec4f(corrected_color, uMyUniforms.color.a);
}
```

```{note}
I renamed what was called `gradientTexture` into `baseColorTexture`.
```

```{figure} /images/lit-boat.png
:align: center
:class: with-shadow
The boat model with some basic lighting.
```

Lighting uniforms
-----------------

To facilitate the further testing of lighting and materials in the next chatpers, let's **make the light sources dynamic** and connect them to our GUI.

Instead of hardcoding the light settings, we would like to pass them through a uniform:

```rust
/**
 * A structure holding the lighting settings
 */
struct LightingUniforms {
	directions: array<vec4f, 2>,
	colors: array<vec4f, 2>,
}

@group(0) @binding(3) var<uniform> uLighting: LightingUniforms;

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4f {
	// Compute shading
	let normal = normalize(in.normal);
	var shading = vec3f(0.0);
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
	let corrected_color = pow(color, vec3f(2.2));
	return vec4f(corrected_color, uMyUniforms.color.a);
}
```

For this, we need to:

 - Create a new **uniform buffer**.
 - Create a new **binding** in the bind group for this uniform.
 - Add this binding to the **bind group layout**.

### Uniforms

Before anything, we replicate the `LightingUniforms` struct in the C++ code:

```C++
#include <array>

// Before Application's private attributes
struct LightingUniforms {
	std::array<vec4, 2> directions;
	std::array<vec4, 2> colors;
};
static_assert(sizeof(LightingUniforms) % 16 == 0);
```

```{caution}
Note how I turned the direction and color to `vec4` instead of `vec3`. This is because of [alignment rules](https://www.w3.org/TR/WGSL/#alignment-and-size): a `vec3` is aligned as if it was a `vec4`.
```

We then use this structure to create an attribute, and define its GPU-side counterpart:

````{tab} With webgpu.hpp
```C++
wgpu::Buffer m_lightingUniformBuffer = nullptr;
LightingUniforms m_lightingUniforms;
```
````

````{tab} Vanilla webgpu.h
```C++
WGPUBuffer m_lightingUniformBuffer = nullptr;
LightingUniforms m_lightingUniforms;
```
````

And we create 3 methods to manage this new uniform buffer:

```C++
// In class Application:
bool initLightingUniforms(); // called in onInit()
void terminateLightingUniforms(); // called in onFinish()
void updateLightingUniforms(); // called when GUI is tweaked
```

These are very similar to our other uniforms:

````{tab} With webgpu.hpp
```C++
bool Application::initLightingUniforms() {
	// Create uniform buffer
	BufferDescriptor bufferDesc;
	bufferDesc.size = sizeof(LightingUniforms);
	bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Uniform;
	bufferDesc.mappedAtCreation = false;
	m_lightingUniformBuffer = m_device.createBuffer(bufferDesc);

	// Initial values
	m_lightingUniforms.directions[0] = { 0.5f, -0.9f, 0.1f, 0.0f };
	m_lightingUniforms.directions[1] = { 0.2f, 0.4f, 0.3f, 0.0f };
	m_lightingUniforms.colors[0] = { 1.0f, 0.9f, 0.6f, 1.0f };
	m_lightingUniforms.colors[1] = { 0.6f, 0.9f, 1.0f, 1.0f };

	updateLightingUniforms();

	return m_lightingUniformBuffer != nullptr;
}

void Application::terminateLightingUniforms() {
	m_lightingUniformBuffer.destroy();
	m_lightingUniformBuffer.release();
}

void Application::updateLightingUniforms() {
	m_queue.writeBuffer(m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
}
```
````

````{tab} Vanilla webgpu.h
```C++
bool Application::initLightingUniforms() {
	// Create uniform buffer
	WGPUBufferDescriptor bufferDesc = {};
	bufferDesc.size = sizeof(LightingUniforms);
	bufferDesc.usage = WGPUBufferUsage_CopyDst | WGPUBufferUsage_Uniform;
	bufferDesc.mappedAtCreation = false;
	m_lightingUniformBuffer = wgpuDeviceCreateBuffer(m_device, bufferDesc);

	// Initial values
	m_lightingUniforms.directions[0] = { 0.5f, -0.9f, 0.1f, 0.0f };
	m_lightingUniforms.directions[1] = { 0.2f, 0.4f, 0.3f, 0.0f };
	m_lightingUniforms.colors[0] = { 1.0f, 0.9f, 0.6f, 1.0f };
	m_lightingUniforms.colors[1] = { 0.6f, 0.9f, 1.0f, 1.0f };

	updateLightingUniforms();

	return m_lightingUniformBuffer != nullptr;
}

void Application::terminateLightingUniforms() {
	wgpuBufferDestroy(m_lightingUniformBuffer);
	wgpuBufferRelease(m_lightingUniformBuffer);
}

void Application::updateLightingUniforms() {
	wgpuQueueWriteBuffer(m_queue, m_lightingUniformBuffer, 0, &m_lightingUniforms, sizeof(LightingUniforms));
}
```
````

We will see later when to call `updateLightingUniforms()`, but before that we need to add bindings for this new uniform buffer.

### Bindings

In `initBindGroup`, add the new binding:

````{tab} With webgpu.hpp
```C++
std::vector<BindGroupEntry> bindings(4);
//                                   ^ This was a 3
// [...]

bindings[3].binding = 3;
bindings[3].buffer = m_lightingUniformBuffer;
bindings[3].offset = 0;
bindings[3].size = sizeof(LightingUniforms);
```
````

````{tab} Vanilla webgpu.h
```C++
std::vector<WGPUBindGroupEntry> bindings(4);
//                                       ^ This was a 3
// [...]

bindings[3].binding = 3;
bindings[3].buffer = m_lightingUniformBuffer;
bindings[3].offset = 0;
bindings[3].size = sizeof(LightingUniforms);
```
````

Of course we must also add this to the bind group **layout**! Since is is very common to change both the bind group and its layout, I like to create a `initBindGroupLayout()` method that sits next to the `initBindGroup()` in the code, althrough it is not called exactly before:

```C++
bool Application::onInit() {
	// [...]
	// Bind group layout is init before the pipeline
	if (!initBindGroupLayout()) return false;
	if (!initRenderPipeline()) return false;
	// [...]
	// Bind group is init after the resources it binds
	if (!initBindGroup()) return false;
	// [...]
}
```

Extract this from `initRenderPipeline()`, then add our new lighting uniform buffer:

```C++
bool Application::initBindGroupLayout() {
	std::vector<BindGroupLayoutEntry> bindingLayoutEntries(4, Default);
	//                                                     ^ This was a 3

	// [...]

	// The lighting uniform buffer binding
	BindGroupLayoutEntry& lightingUniformLayout = bindingLayoutEntries[3];
	lightingUniformLayout.binding = 3;
	lightingUniformLayout.visibility = ShaderStage::Fragment; // only Fragment is needed
	lightingUniformLayout.buffer.type = BufferBindingType::Uniform;
	lightingUniformLayout.buffer.minBindingSize = sizeof(LightingUniforms);

	// [...]
}
```

````{note}
Since we are adding a new uniform buffer, don't forget to update the required limits:

```C++
requiredLimits.limits.maxUniformBuffersPerShaderStage = 2;
```
````

### GUI

Let us now connect the GUI by replacing the "Hello, world" panel in `updateGui()`:

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

This changes the value of `m_lightingUniforms` when the user tweaks sliders. In order to reflect these changes in the GPU-side uniforms, we copy at each frame the values that the GUI manipulates to the GPU-side buffer.

```C++
void Application::onFrame() {
	updateLightingUniforms();
	// [...]
}
```

```{figure} /images/light-color-ui.png
:align: center
:class: with-shadow
The UI is connected to the lighting uniforms.
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
ImGui::DragDirection("Direction #0", m_lightingUniforms.directions[0]);
```

### Slight optimization

Instead of uploading the lighting uniform buffer at each frame even when nothing changes, we can get from ImGui the information of whether the fields changed:

```C++
// In class Application
bool m_lightingUniformsChanged = false;

// In Application.cpp
void Application::updateLighting() {
	if (m_lightingUniformsChanged) {
		// [...] Update uniforms
		m_lightingUniformsChanged = false;
	}
}

// In Application::updateGui:
bool changed = false;
ImGui::Begin("Lighting");
changed = ImGui::ColorEdit3("Color #0", glm::value_ptr(m_lightingUniforms.colors[0])) || changed;
changed = ImGui::DragDirection("Direction #0", m_lightingUniforms.directions[0]) || changed;
changed = ImGui::ColorEdit3("Color #1", glm::value_ptr(m_lightingUniforms.colors[1])) || changed;
changed = ImGui::DragDirection("Direction #1", m_lightingUniforms.directions[1]) || changed;
ImGui::End();
m_lightingUniformsChanged = changed;
```

Conclusion
----------

In this chapter we have:

 - Connected diffuse shading with textures,
 - Connected lighting with GUI.
 - Created a custom GUI.

Okay, we are now ready to dive into material models for real!

````{tab} With webgpu.hpp
*Resulting code:* [`step100`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step100-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step100-vanilla)
````
