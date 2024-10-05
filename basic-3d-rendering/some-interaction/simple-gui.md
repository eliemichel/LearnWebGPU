Simple GUI <span class="bullet">🟡</span>
==========

````{tab} With webgpu.hpp
*Resulting code:* [`step095`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````

````{tab} With Dawn
*Resulting code:* [`step095-dawn`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````

Multiple solutions exist for writing *graphical user interfaces* (GUI), i.e., buttons, text inputs, value sliders and so on.

For applications that are mostly about these inputs, it is common to use **a whole *framework*** as a base, like [Qt](https://www.qt.io/), [GTK](https://www.gtk.org/), [wxWidgets](https://www.wxwidgets.org/), [WinUI](https://microsoft.github.io/microsoft-ui-xaml/), etc. These usually manage the main application loop by themselves and are heavy dependencies.

But in the case of video games or prototypes like ours, one usually turns towards **more lightweights solutions**, among which [Dear ImGui](https://github.com/ocornut/imgui) is a very popular choice.

```{note}
ImGui does not try to give a OS-native look to your app. Instead, it focuses on being very **easy to integrate** to any existing project, and **easy to program with**.

This also comes at the price of redrawing the whole GUI from scratch at each frame while frameworks usually only update what is needed.
```

Setting up ImGui
----------------

ImGui fully supports using WebGPU as a backend with both wgpu-native and Dawn since its [version 1.89.8](https://github.com/ocornut/imgui/archive/refs/tags/v1.89.8.zip). Unzip it as a `imgui/` directory, remove `examples`, `doc` and `.github` (or keep them but we don't need them).

ImGui does not provide a `CMakeLists.txt` but it is straightforward to write it ourselves (still in the `imgui/` directory):

```CMake
# Define an ImGui target that fits our use case
add_library(imgui STATIC
	# Among the different backends available, we are interested in connecting
	# the GUI to GLFW andWebGPU:
	backends/imgui_impl_wgpu.h
	backends/imgui_impl_wgpu.cpp
	backends/imgui_impl_glfw.h
	backends/imgui_impl_glfw.cpp

	# Bonus to add some C++ specific features (the core ImGUi is a C library)
	misc/cpp/imgui_stdlib.h
	misc/cpp/imgui_stdlib.cpp

	# The core ImGui files
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
```

Then in your root `CMakeLists.txt`, as usual:

```CMake
add_subdirectory(imgui)

# [...]

target_link_libraries(App PRIVATE glfw webgpu glfw3webgpu imgui)
```

Usage
-----

### Overview

ImGui interface is redrawn at each frame, following a very imperative style:


```C++
#include <imgui.h>

void Application::onFrame() {
	// [...]

	// [...] Init ImGui frame

	ImGui::Begin("Hello, world!");
	ImGui::Text("This is some useful text.");
	if (ImGui::Button("Click me")) {
		// do something
	}
	ImGui::End();

	// [...] Draw ImGui frame
}
```

Available functions can be found in [`imgui.h`](https://github.com/ocornut/imgui/blob/master/imgui.h), and additional help is given in [their wiki](https://github.com/ocornut/imgui/wiki).

### Setup

We however **need to set-up some boilerplate**, both when starting the application and before/after defining the GUI at each frame.

To make things clearer, we isolate GUI-related code into specific methods (note that we need to access the render pass in `updateGui`):

```C++
// In Application.h
class Application {
private:
	bool initGui(); // called in onInit
	void terminateGui(); // called in onFinish
	void updateGui(wgpu::RenderPassEncoder renderPass); // called in onFrame
};

// In Application.cpp
void Application::onInit() {
	// [...]
	if (!initGui()) return false;
	return true;
}

void Application::onFinish() {
	terminateGui();
	// [...]
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

Here comes the boilerplate itself. For each step (global init, frame init, frame render) there is usually the "pure" ImGui function as well as the backend functions. Things are decoupled this way because ImGui can be used together with other libraries than GLFW and WebGPU.

```C++
// In Application.cpp
#include <imgui.h>
#include <backends/imgui_impl_wgpu.h>
#include <backends/imgui_impl_glfw.h>

bool Application::initGui() {
	// Setup Dear ImGui context
	IMGUI_CHECKVERSION();
	ImGui::CreateContext();
	ImGui::GetIO();

	// Setup Platform/Renderer backends
	ImGui_ImplGlfw_InitForOther(m_window, true);
	ImGui_ImplWGPU_Init(m_device, 3, m_swapChainFormat, m_depthTextureFormat);
	return true;
}

void Application::terminateGui() {
	ImGui_ImplGlfw_Shutdown();
	ImGui_ImplWGPU_Shutdown();
}

void Application::updateGui(RenderPassEncoder renderPass) {
	// Start the Dear ImGui frame
	ImGui_ImplWGPU_NewFrame();
	ImGui_ImplGlfw_NewFrame();
	ImGui::NewFrame();

	// [...] Build our UI

	// Draw the UI
	ImGui::EndFrame();
	// Convert the UI defined above into low-level drawing commands
	ImGui::Render();
	// Execute the low-level drawing commands on the WebGPU backend
	ImGui_ImplWGPU_RenderDrawData(ImGui::GetDrawData(), renderPass);
}
```

### Example of GUI

This ImGui's basic example, that shows some **typical use cases**.

Note that variables are defined as **static** here, so that they are initialized only once and then **"remembered"** across frames.

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

ImGuiIO& io = ImGui::GetIO();
ImGui::Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / io.Framerate, io.Framerate);
ImGui::End();
```

### Capabilities

Using ImGUI requires `maxBindGroups` to be at least 2.

```C++
requiredLimits.limits.maxBindGroups = 2;
//                                    ^ This was a 1
```

Misc
----

You may have noticed when playing with sliders that while ImGui is reacting to your mouse, **the camera controller also receives the events**, which is a bit annoying.

To prevent this, we can use the `io.WantCaptureMouse` variable that ImGui turns to true when it detected that the user interacts with the widgets. When so, we ignore mouse clicks in the camera controller:

```C++
void Application::onMouseButton(int button, int action, int mods) {
	ImGuiIO& io = ImGui::GetIO();
	if (io.WantCaptureMouse) {
		// Don't rotate the camera if the mouse is already captured by an ImGui
		// interaction at this frame.
		return;
	}

	// [...]
}
```

```{figure} /images/first-imgui.png
:align: center
:class: with-shadow
A basic GUI with ImGUI
```

Conclusion
----------

Congratulations, we now have all the tools we need to easily test various parameters and interact with the 3D scene, we can then move on to the lighting and materials!

````{tab} With webgpu.hpp
*Resulting code:* [`step095`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step095-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````

````{tab} With Dawn
*Resulting code:* [`step095-dawn`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step095-vanilla)
````
