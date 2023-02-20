Camera control (WIP)
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step090`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step090-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090-vanilla)
````

TODO

Events
------

Similarly to what we did for the resize, we wire up 3 new GLFW window events:

```C++
class Application {
public:
	// Mouse events
	void onMouseMove(double xpos, double ypos);
	void onMouseButton(int button, int action, int mods);
	void onScroll(double xoffset, double yoffset);
	// [...]
}
```

```C++
void onWindowMouseMove(GLFWwindow* window, double xpos, double ypos) {
	auto pApp = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (pApp != nullptr) pApp->onMouseMove(xpos, ypos);
}
void onWindowMouseButton(GLFWwindow* window, int button, int action, int mods) {
	auto pApp = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (pApp != nullptr) pApp->onMouseButton(button, action, mods);
}
void onWindowScroll(GLFWwindow* window, double xoffset, double yoffset) {
	auto pApp = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (pApp != nullptr) pApp->onScroll(xoffset, yoffset);
}
```

```C++
// Add window callbacks
glfwSetWindowUserPointer(m_window, this);
glfwSetFramebufferSizeCallback(m_window, onWindowResize);
glfwSetCursorPosCallback(m_window, onWindowMouseMove);
glfwSetMouseButtonCallback(m_window, onWindowMouseButton);
glfwSetScrollCallback(m_window, onWindowScroll);
```

Camera state
------------

Instead of manipulating the camera view directly as a matrix made of 16 coefficients, we store a camera state that is closer to what user input affects:

```C++
struct CameraState {
	// angles.x is the rotation of the camera around the global vertical axis, affected by mouse.x
	// angles.y is the rotation of the camera around its local horizontal axis, affected by mouse.y
	vec2 angles = { 0.8f, 0.5f };
	// zoom is the position of the camera along its local forward axis, affected by the scroll wheel
	float zoom = -1.2f;
};
```

We add such a state to our Application class (note that I know prefix attribute with `m_` to better distinguish them from local variables).

```C++
// In the declaration of class Application
CameraState m_cameraState;
```

We then create a (private) method that converts this state into an actual matrix. We call this any time the camera state is modified:

```C++
void Application::updateViewMatrix() {
	float cx = cos(m_cameraState.angles.x);
	float sx = sin(m_cameraState.angles.x);
	float cy = cos(m_cameraState.angles.y);
	float sy = sin(m_cameraState.angles.y);
	vec3 position = vec3(cx * cy, sx * cy, sy) * std::exp(-m_cameraState.zoom);
	m_uniforms.viewMatrix = glm::lookAt(position, vec3(0.0f), vec3(0, 0, 1));
	m_device.getQueue().writeBuffer(m_uniformBuffer, offsetof(MyUniforms, viewMatrix), &m_uniforms.viewMatrix, sizeof(MyUniforms::viewMatrix));
}
```

Controller
----------

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
		m_cameraState.angles.y = glm::clamp(m_cameraState.angles.y, -PI / 2 + 1e-5f, PI / 2 - 1e-5f);
		updateViewMatrix();
	}
}

void Application::onMouseButton(int button, int action, int mods) {
	(void)mods;
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

void Application::onScroll(double xoffset, double yoffset) {
	(void)xoffset;
	m_cameraState.zoom += m_drag.scrollSensitivity * (float)yoffset;
	m_cameraState.zoom = glm::clamp(m_cameraState.zoom, -2.0f, 2.0f);
	updateViewMatrix();
}
```

Inertia
-------

```C++
class Application {
private:
	void updateDragInertia();

	struct DragState {
		// [...]
		
		// Inertia
		vec2 velocity = {0.0, 0.0};
		vec2 previousDelta;
		float intertia = 0.9f;
	};

	// [...]
};
```

```C++
void Application::onFrame() {
	updateDragInertia();
	// [...]
}

void Application::updateDragInertia() {
	constexpr float eps = 1e-4f;
	if (!m_drag.active) {
		if (std::abs(m_drag.velocity.x) < eps && std::abs(m_drag.velocity.y) < eps) {
			return;
		}
		m_cameraState.angles += m_drag.velocity;
		m_cameraState.angles.y = glm::clamp(m_cameraState.angles.y, -PI / 2 + 1e-5f, PI / 2 - 1e-5f);
		m_drag.velocity *= m_drag.intertia;
		updateViewMatrix();
	}
}
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

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step090`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step090-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090-vanilla)
````
