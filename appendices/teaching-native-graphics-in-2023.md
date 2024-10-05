Teaching native graphics in 2023 <span class="bullet">🟢</span>
================================

*This is a more detailed explaination of the section [Why WebGPU](../introduction.md#why-webgpu) of the lecture's introduction.*

My interest for using WebGPU for native development grew while looking for **the best graphics API to teach** in a computer graphics curriculum.

```{important}
Graphics API evolved very quickly over the last 20 years (think of how OpenGL 1.1 looked like for those of you who know it), so it is important lectures follow at a reasonable pace this evolution.
```

For a long time, I had been teaching **OpenGL**. This was a perfectly standard and cross-platform API for interacting with GPUs. But over the years this API and its idioms started to become **legacy**.
First, Apple stopped supporting it after version 4.1 (leaving me with the frustration of not being able to use [DSA](https://www.khronos.org/opengl/wiki/Direct_State_Access) in the lectures, among other things), and **deprecated** it all together from macOS 10.14 onward (since 2018). Basically, they could drop it at any time, so teaching OpenGL now is really **not a future-proof bet**.

Secondly, it is clear that there will be no new version of OpenGL anyways. Its steering consortium is now working on **Vulkan**. Vulkan was meant to remain a cross-platform API, despite its whole new design, and even unify desktop and mobile platforms, thus being able to fully **replace OpenGL** on the long run. **But**... here comes Apple again.

Like many actors of the graphics world, **Apple** felt in the early 2010s the need to evolve from the design of OpenGL (which had diverged too much from the way the hardware had evolved), and started their own API called **Metal**. Unlike the others though, they **refused to join** efforts into the Vulkan initiative. So, although there are [ways to use Vulkan on Apple devices](https://www.lunarg.com/wp-content/uploads/2021/06/The-State-of-Vulkan-on-Apple-03June-2021.pdf), we cannot really consider Vulkan as cross-platform enough. I don't want my lecture to feel a bit of a hack to macOS users.

This scattered state of the graphics APIs is a **source of concern** for all software vendors who try to support both Linux, Windows and macOS (not to mention mobile platforms). They are forced to implement the same processes in different APIs, and while factorizing these parallel implementations, a lot of them spontaneously end up writing **custom graphics abstraction** libraries.

**Should we teach such an abstraction library?** I am quite reluctant at doing this. A lot of them make domain-specific choices related to the context in which they have been developed. And they are very often incomplete because not enough time can be invested into making them reusable. The longevity of these libraries is likely much shorter than the one of more standardized APIs (which are themselves dying too fast already). They might enforce specific idioms that are uncommon, making the transition to other graphics APIs harder.

The **Web consortium** faced the same issue when trying to expose a unified GPU abstraction to JavaScript code, and they drafted [WebGPU](https://gpuweb.github.io/gpuweb).

This API has a growing developer/documentation base, is general purpose, cross-platform and future-oriented, which thus makes it a good candidate even for desktop applications! This is why Google Chrome's implementation of this API has been designed as a separate code base, called [Dawn](https://dawn.googlesource.com/dawn), and that can be linked by other applications.
