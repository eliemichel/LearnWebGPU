Camera control <span class="bullet">🟡</span>
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step090`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step090-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090-vanilla)
````

The very first kind of interaction we usually need with a 3D scene is to **change the point of view**. There are many different types of camera control, depending on the use case, here are a few examples:

 - **First person:** The camera position is fixed, and its orientation follows the mouse cursor. This is what is used in first-person video games like shooters.
 - **Turntable:** This is what modeling tools typically use: the camera **orbits** around a focus point that it remains centered on.
 - **Trackball:** Unlike the turntable, the trackball does not give a particular meaning to the "up" axis. This enables one to orbit around an object without any form of [gimbal lock](https://en.wikipedia.org/wiki/Gimbal_lock).

```{note}
There are different flavors of *turntable* control depending on how the center of rotation is chosen: it may be fixed, or set as the point of the 3D surface that was clicked at the beginning of each interaction.
```

We focus here on the case of the **turntable** model, which I find the most confortable one for a 3D object viewer. Imho most real-life objects have a notion of "up" and "down", which justifies that the view controller does as well.

Event handlers
--------------

Similarly to what we did for the resize, we wire up 3 new GLFW window events:

```C++
class Application {
	// Mouse events
	void onMouseMove(double xpos, double ypos);
	void onMouseButton(int button, int action, int mods);
	void onScroll(double xoffset, double yoffset);
	// [...]
}
```

```C++
// Add window callbacks
glfwSetWindowUserPointer(m_window, this);
glfwSetFramebufferSizeCallback(m_window, /* [...] */);
glfwSetCursorPosCallback(m_window, [](GLFWwindow* window, double xpos, double ypos) {
	auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (that != nullptr) that->onMouseMove(xpos, ypos);
});
glfwSetMouseButtonCallback(m_window, [](GLFWwindow* window, int button, int action, int mods) {
	auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (that != nullptr) that->onMouseButton(button, action, mods);
});
glfwSetScrollCallback(m_window, [](GLFWwindow* window, double xoffset, double yoffset) {
	auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (that != nullptr) that->onScroll(xoffset, yoffset);
});
```

Camera state
------------

Instead of manipulating the camera view directly as a matrix made of 16 coefficients, we store a camera state that is **closer to what user input affects**:

```C++
// (After the definition of struct MyUniforms)
struct CameraState {
	// angles.x is the rotation of the camera around the global vertical axis, affected by mouse.x
	// angles.y is the rotation of the camera around its local horizontal axis, affected by mouse.y
	vec2 angles = { 0.8f, 0.5f };
	// zoom is the position of the camera along its local forward axis, affected by the scroll wheel
	float zoom = -1.2f;
};
```

We then add this struct as a state in our `Application` class.

```C++
// In the declaration of class Application
private:
	CameraState m_cameraState;
```

We then create a (private) method that converts this state into an actual matrix. We call this any time the camera state is modified:

````{tab} With webgpu.hpp
```C++
void Application::updateViewMatrix() {
	float cx = cos(m_cameraState.angles.x);
	float sx = sin(m_cameraState.angles.x);
	float cy = cos(m_cameraState.angles.y);
	float sy = sin(m_cameraState.angles.y);
	vec3 position = vec3(cx * cy, sx * cy, sy) * std::exp(-m_cameraState.zoom);
	m_uniforms.viewMatrix = glm::lookAt(position, vec3(0.0f), vec3(0, 0, 1));
	m_queue.writeBuffer(
		m_uniformBuffer,
		offsetof(MyUniforms, viewMatrix),
		&m_uniforms.viewMatrix,
		sizeof(MyUniforms::viewMatrix)
	);
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::updateViewMatrix() {
	float cx = cos(m_cameraState.angles.x);
	float sx = sin(m_cameraState.angles.x);
	float cy = cos(m_cameraState.angles.y);
	float sy = sin(m_cameraState.angles.y);
	vec3 position = vec3(cx * cy, sx * cy, sy) * std::exp(-m_cameraState.zoom);
	m_uniforms.viewMatrix = glm::lookAt(position, vec3(0.0f), vec3(0, 0, 1));
	wgpuQueueWriteBuffer(
		m_queue,
		m_uniformBuffer,
		offsetof(MyUniforms, viewMatrix),
		&m_uniforms.viewMatrix,
		sizeof(MyUniforms::viewMatrix)
	);
}
```
````

```{note}
You may invoke `updateViewMatrix()` at the end of `initUniforms()` to ensure that the original view matrix is consistent with the camera state.
```

Controller
----------

An interaction with the camera controller consists in the following sequence of events:

 - The mouse is **pressed**.
 - The mouse is **moved**.
 - The mouse is **moved**.
 - [...]
 - The mouse is **moved**.
 - The mouse is **released**.

When the mouse is pressed, we save some information about the current state, that we will need to update the view at each subsequent move. We call this the `DragState`.

When the mouse is released, we forget about this information to prevent new moves from affecting the view point.

```C++
struct DragState {
	// Whether a drag action is ongoing (i.e., we are between mouse press and mouse release)
	bool active = false;
	// The position of the mouse at the beginning of the drag action
	vec2 startMouse;
	// The camera state at the beginning of the drag action
	CameraState startCameraState;

	// Constant settings
	float sensitivity = 0.01f;
	float scrollSensitivity = 0.1f;
};

// In the declaration of class Application
DragState m_drag;
```

```C++
void Application::onMouseMove(double xpos, double ypos) {
	if (m_drag.active) {
		vec2 currentMouse = vec2(-(float)xpos, (float)ypos);
		vec2 delta = (currentMouse - m_drag.startMouse) * m_drag.sensitivity;
		m_cameraState.angles = m_drag.startCameraState.angles + delta;
		// Clamp to avoid going too far when orbitting up/down
		m_cameraState.angles.y = glm::clamp(m_cameraState.angles.y, -PI / 2 + 1e-5f, PI / 2 - 1e-5f);
		updateViewMatrix();
	}
}

void Application::onMouseButton(int button, int action, int /* modifiers */) {
	if (button == GLFW_MOUSE_BUTTON_LEFT) {
		switch(action) {
		case GLFW_PRESS:
			m_drag.active = true;
			double xpos, ypos;
			glfwGetCursorPos(m_window, &xpos, &ypos);
			m_drag.startMouse = vec2(-(float)xpos, (float)ypos);
			m_drag.startCameraState = m_cameraState;
			break;
		case GLFW_RELEASE:
			m_drag.active = false;
			break;
		}
	}
}
```

We also add a simple interaction when the use scrolls, to zoom in/out:

```C++
void Application::onScroll(double /* xoffset */, double yoffset) {
	m_cameraState.zoom += m_drag.scrollSensitivity * static_cast<float>(yoffset);
	m_cameraState.zoom = glm::clamp(m_cameraState.zoom, -2.0f, 2.0f);
	updateViewMatrix();
}
```

Bonus: Inertia
--------------

A nice addition to the **look & feel** of your viewer is to add some **momentum** to the interaction, to fade out the user's gesture.

For this we add to the drag state the current **velocity** of the angle rotation, and add a little bit of it to the rotation at the next frame.

```C++
struct DragState {
	// [...]
	
	// Inertia
	vec2 velocity = {0.0, 0.0};
	vec2 previousDelta;
	float inertia = 0.9f;
};
```

```C++
void Application::onMouseMove(double xpos, double ypos) {
	if (m_drag.active) {
		// [...]

		// Inertia
		m_drag.velocity = delta - m_drag.previousDelta;
		m_drag.previousDelta = delta;
	}
}
```

We need to define a `updateDragInertia()` that is called at each frame, not just when the user moves the mouse:

```C++
// In Application.h
class Application {
private:
	void updateDragInertia();
	// [...]
};
```

```C++
// In Application.cpp
void Application::onFrame() {
	updateDragInertia();
	// [...]
}

void Application::updateDragInertia() {
	constexpr float eps = 1e-4f;
	// Apply inertia only when the user released the click.
	if (!m_drag.active) {
		// Avoid updating the matrix when the velocity is no longer noticeable
		if (std::abs(m_drag.velocity.x) < eps && std::abs(m_drag.velocity.y) < eps) {
			return;
		}
		m_cameraState.angles += m_drag.velocity;
		m_cameraState.angles.y = glm::clamp(m_cameraState.angles.y, -PI / 2 + 1e-5f, PI / 2 - 1e-5f);
		// Dampen the velocity so that it decreases exponentially and stops
		// after a few frames.
		m_drag.velocity *= m_drag.inertia;
		updateViewMatrix();
	}
}
```

Conclusion
----------

The camera controller is an important step needed before moving on to lighting, because we will need to inspect our model in details.

Of course feel free to adapt this to your own camera model. With this example you can already do a lot and you should be able to easily add some keyboard interaction on your own using [`glfwSetKeyCallback`](https://www.glfw.org/docs/3.0/group__input.html#ga7e496507126f35ea72f01b2e6ef6d155).

Next we see the last bit of general purpose code, to get the base for a **user interface**, after which we'll move back to 3D-specific stuff!

````{tab} With webgpu.hpp
*Resulting code:* [`step090`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step090-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090-vanilla)
````
