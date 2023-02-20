Camera control (WIP)
==============

````{tab} With webgpu.hpp
*Resulting code:* [`step090`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step090-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step090-vanilla)
````

TODO

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
glfwSetWindowUserPointer(window, this);
glfwSetFramebufferSizeCallback(window, onWindowResize);
glfwSetCursorPosCallback(window, onWindowMouseMove);
glfwSetMouseButtonCallback(window, onWindowMouseButton);
glfwSetScrollCallback(window, onWindowScroll);
```

```C++
// NB: We prefix new private attributes with 'm_'
bool m_isDragging = false;
glm::vec2 m_startDragMouse;
glm::vec2 m_startDragCameraEulerAngles;
glm::vec2 m_cameraEulerAngles = {0.8f, 0.5f};
float m_zoom = -1.2f;
```

```C++
void Application::onMouseMove(double xpos, double ypos) {
	constexpr float sensitivity = 0.01f;
	if (m_isDragging) {
		vec2 delta = vec2(-(float)xpos, (float)ypos);
		m_cameraEulerAngles = m_startDragCameraEulerAngles + (delta - m_startDragMouse) * sensitivity;
		m_cameraEulerAngles.y = std::min(std::max(-PI / 2, m_cameraEulerAngles.y), PI / 2);
		updateViewMatrix();
	}
}

void Application::onMouseButton(int button, int action, int mods) {
	(void)mods;
	if (button == GLFW_MOUSE_BUTTON_LEFT) {
		switch(action) {
		case GLFW_PRESS:
			m_isDragging = true;
			double xpos, ypos;
			glfwGetCursorPos(window, &xpos, &ypos);
			m_startDragMouse = vec2(-(float)xpos, (float)ypos);
			m_startDragCameraEulerAngles = m_cameraEulerAngles;
			break;
		case GLFW_RELEASE:
			m_isDragging = false;
			break;
		}
	}
}

void Application::onScroll(double xoffset, double yoffset) {
	(void)xoffset;
	m_zoom += 0.1f * (float)yoffset;
	updateViewMatrix();
}

void Application::updateViewMatrix() {
	float cx = cos(m_cameraEulerAngles.x);
	float sx = sin(m_cameraEulerAngles.x);
	float cy = cos(m_cameraEulerAngles.y);
	float sy = sin(m_cameraEulerAngles.y);
	vec3 position = vec3(cx * cy, sx * cy, sy) * std::exp(-m_zoom);
	uniforms.viewMatrix = uniforms.viewMatrix = glm::lookAt(position, vec3(0.0f), vec3(0, 0, 1));
	device.getQueue().writeBuffer(uniformBuffer, offsetof(MyUniforms, viewMatrix), &uniforms.viewMatrix, sizeof(MyUniforms::viewMatrix));
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
