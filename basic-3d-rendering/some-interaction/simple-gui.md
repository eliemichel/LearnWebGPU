Simple GUI (WIP)
==========

````{tab} With webgpu.hpp
*Resulting code:* [`step095`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````

TODO

Setting up ImGUI
----------------

We use [ImGUI](https://github.com/ocornut/imgui), which is clearly the most used tool for lightweight UI in graphics prototypes and utility tools. And it already supports WebGPU as a backend!

Unzip https://github.com/ocornut/imgui/archive/refs/tags/v1.89.3.zip as `imgui`, remove examples and doc (or keep them), and replace the files `backend/imgui_impl_wgpu.*` with the ones from [this zip](../../data/imgui_impl_wgpu.zip). Also add this `CMakeLists.txt` in the directory:

```CMake
# Define an ImGUI target that uses the WebGPU backend
add_library(imgui STATIC
	backends/imgui_impl_wgpu.h
	backends/imgui_impl_wgpu.cpp
	backends/imgui_impl_glfw.h
	backends/imgui_impl_glfw.cpp

	misc/cpp/imgui_stdlib.h
	misc/cpp/imgui_stdlib.cpp

	imconfig.h
	imgui.h
	imgui.cpp
	imgui_draw.cpp
	imgui_internal.h
	imgui_tables.cpp
	imgui_widgets.cpp
	imstb_rectpack.h
	imstb_textedit.h
	imstb_truetype.h
)

target_include_directories(imgui PUBLIC .)
target_link_libraries(imgui PUBLIC webgpu glfw)
# TODO: this should be provided by the webgpu target instead
target_compile_definitions(imgui PUBLIC WEBGPU_BACKEND_WGPU)
```

Then in your root `CMakeLists.txt`:

```CMake
add_subdirectory(imgui)

# [...]

target_link_libraries(App PRIVATE glfw webgpu glfw3webgpu imgui)
```

Usage
-----

Skeleton:

```C++
// In Application.h
class Application {
private:
	void initGui(); // called in onInit
	void updateGui(wgpu::RenderPassEncoder renderPass); // called in onFrame
};

// In Application.cpp
void Application::onInit() {
	// [...]
	initGui();
	return true;
}

void Application::onFrame() {
	// [...]

	renderPass.draw(m_indexCount, 1, 0, 0);

	// We add the GUI drawing commands to the render pass
	updateGui(renderPass);

	renderPass.end();

	// [...]
}
```

Boilerplate:

```C++
// In Application.cpp
#include <imgui.h>
#include <backends/imgui_impl_wgpu.h>
#include <backends/imgui_impl_glfw.h>

void Application::initGui() {
	// Setup Dear ImGui context
	IMGUI_CHECKVERSION();
	ImGui::CreateContext();
	ImGuiIO& io = ImGui::GetIO(); (void)io;

	// Setup Platform/Renderer backends
	ImGui_ImplGlfw_InitForOther(m_window, true);
	ImGui_ImplWGPU_Init(m_device, 3, m_swapChainFormat, m_depthTextureFormat);
}

void Application::updateGui(RenderPassEncoder renderPass) {
	// Start the Dear ImGui frame
	ImGui_ImplWGPU_NewFrame();
	ImGui_ImplGlfw_NewFrame();
	ImGui::NewFrame();

	// Build our UI
	// [...]

	ImGui::Render();
	ImGui_ImplWGPU_RenderDrawData(ImGui::GetDrawData(), renderPass);
}
```

ImGui code:

```C++
// Build our UI
static float f = 0.0f;
static int counter = 0;
static bool show_demo_window = true;
static bool show_another_window = false;
static ImVec4 clear_color = ImVec4(0.45f, 0.55f, 0.60f, 1.00f);

ImGui::Begin("Hello, world!");                                // Create a window called "Hello, world!" and append into it.

ImGui::Text("This is some useful text.");                     // Display some text (you can use a format strings too)
ImGui::Checkbox("Demo Window", &show_demo_window);            // Edit bools storing our window open/close state
ImGui::Checkbox("Another Window", &show_another_window);

ImGui::SliderFloat("float", &f, 0.0f, 1.0f);                  // Edit 1 float using a slider from 0.0f to 1.0f
ImGui::ColorEdit3("clear color", (float*)&clear_color);       // Edit 3 floats representing a color

if (ImGui::Button("Button"))                                  // Buttons return true when clicked (most widgets return true when edited/activated)
	counter++;
ImGui::SameLine();
ImGui::Text("counter = %d", counter);

ImGui::Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / ImGui::GetIO().Framerate, ImGui::GetIO().Framerate);
ImGui::End();
```

### Capabilities

Using ImGUI requires to increment `maxBindGroups` by 1.

Misc
----

To avoid interaction conflict with our camera controller:

```C++
void Application::onMouseButton(int button, int action, int mods) {
	ImGuiIO& io = ImGui::GetIO(); (void)io;
	if (io.WantCaptureMouse) {
		return;
	}

	// [...]
}
```

Conclusion
----------

```{figure} /images/first-imgui.png
:align: center
:class: with-shadow
A basic GUI with ImGUI
```

````{tab} With webgpu.hpp
*Resulting code:* [`step095`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````
