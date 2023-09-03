/*

Usage: In the main loop:

{ // export video
	static int frame = 0;
	saveImage(resolvePath(frame), nextTexture);
	++frame;
	if (frame > 200) {
		break;
	}
}

*/
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define __STDC_LIB_EXT1__
#include "stb_image_write.h"

#include <webgpu/webgpu.hpp>

#include <filesystem>
#include <string>

// Save a texture to disk
bool saveTexture(const std::filesystem::path path, wgpu::Device device, wgpu::Texture texture);

// Saving a texture view requires to blit it into another texture, because only textures can be retrieved
bool saveTextureView(const std::filesystem::path path, wgpu::Device device, wgpu::TextureView textureView, uint32_t width, uint32_t height);

std::filesystem::path resolvePath(int frame) {
	std::filesystem::path base = "render/frame" + std::to_string(frame) + ".png";
	create_directories(base.parent_path());
	return std::filesystem::absolute(base);
}

class FileRenderer {
public:
	FileRenderer(wgpu::Device device, uint32_t width, uint32_t height);
	bool render(const std::filesystem::path path, wgpu::TextureView textureView) const;
	bool render(const std::filesystem::path path, wgpu::Texture texture) const;

private:
	wgpu::Device m_device;
	uint32_t m_width;
	uint32_t m_height;
	wgpu::BindGroupLayout m_bindGroupLayout = nullptr;
	wgpu::RenderPassDescriptor m_renderPassDesc;
	wgpu::RenderPipeline m_pipeline = nullptr;
	wgpu::Texture m_renderTexture = nullptr;
	wgpu::TextureDescriptor m_renderTextureDesc;
	wgpu::TextureView m_renderTextureView = nullptr;
	wgpu::Buffer m_pixelBuffer = nullptr;
	wgpu::BufferDescriptor m_pixelBufferDesc;
};

FileRenderer::FileRenderer(wgpu::Device device, uint32_t width, uint32_t height)
	: m_device(device)
	, m_width(width)
	, m_height(height)
{
	using namespace wgpu;

	// Create a texture onto which we blit the texture view
	TextureDescriptor renderTextureDesc;
	renderTextureDesc.dimension = TextureDimension::_2D;
	renderTextureDesc.format = TextureFormat::RGBA8Unorm;
	renderTextureDesc.mipLevelCount = 1;
	renderTextureDesc.sampleCount = 1;
	renderTextureDesc.size = { width, height, 1 };
	renderTextureDesc.usage = TextureUsage::RenderAttachment | TextureUsage::CopySrc;
	renderTextureDesc.viewFormatCount = 0;
	renderTextureDesc.viewFormats = nullptr;
	Texture renderTexture = device.createTexture(renderTextureDesc);

	TextureViewDescriptor renderTextureViewDesc;
	renderTextureViewDesc.aspect = TextureAspect::All;
	renderTextureViewDesc.baseArrayLayer = 0;
	renderTextureViewDesc.arrayLayerCount = 1;
	renderTextureViewDesc.baseMipLevel = 0;
	renderTextureViewDesc.mipLevelCount = 1;
	renderTextureViewDesc.dimension = TextureViewDimension::_2D;
	renderTextureViewDesc.format = renderTextureDesc.format;
	TextureView renderTextureView = renderTexture.createView(renderTextureViewDesc);

	// Create a buffer to get pixels
	BufferDescriptor pixelBufferDesc = Default;
	pixelBufferDesc.mappedAtCreation = false;
	pixelBufferDesc.usage = BufferUsage::MapRead | BufferUsage::CopyDst;
	pixelBufferDesc.size = 4 * width * height;
	Buffer pixelBuffer = device.createBuffer(pixelBufferDesc);

	// Shader
	ShaderModuleWGSLDescriptor shaderCodeDesc{};
	shaderCodeDesc.chain.next = nullptr;
	shaderCodeDesc.chain.sType = SType::ShaderModuleWGSLDescriptor;
	shaderCodeDesc.code = R"(
var<private> pos : array<vec2<f32>, 3> = array<vec2<f32>, 3>(
	vec2<f32>(-1.0, -1.0), vec2<f32>(-1.0, 3.0), vec2<f32>(3.0, -1.0)
);

@group(0) @binding(0) var texture: texture_2d<f32>;

@vertex
fn vs_main(@builtin(vertex_index) vertexIndex: u32) -> @builtin(position) vec4<f32> {
	return vec4(pos[vertexIndex], 1.0, 1.0);
}

@fragment
fn fs_main(@builtin(position) fragCoord: vec4<f32>) -> @location(0) vec4<f32> {
	let color = textureLoad(texture, vec2<i32>(fragCoord.xy), 0);
	let corrected_color = pow(color.rgb, vec3<f32>(1.0/2.2));
	return vec4<f32>(corrected_color, color.a);
}
)";
	ShaderModuleDescriptor shaderDesc{};
#ifdef WEBGPU_BACKEND_WGPU
	shaderDesc.hintCount = 0;
	shaderDesc.hints = nullptr;
#endif
	shaderDesc.nextInChain = &shaderCodeDesc.chain;
	ShaderModule shaderModule = device.createShaderModule(shaderDesc);

	// Bind group for input texture
	std::vector<BindGroupLayoutEntry> bindingLayoutEntries(1, Default);
	BindGroupLayoutEntry& bindingLayout = bindingLayoutEntries[0];
	bindingLayout.binding = 0;
	bindingLayout.visibility = ShaderStage::Fragment;
	bindingLayout.texture.sampleType = TextureSampleType::Float;
	bindingLayout.texture.viewDimension = TextureViewDimension::_2D;

	BindGroupLayoutDescriptor bindGroupLayoutDesc;
	bindGroupLayoutDesc.entryCount = (uint32_t)bindingLayoutEntries.size();
	bindGroupLayoutDesc.entries = bindingLayoutEntries.data();
	BindGroupLayout bindGroupLayout = device.createBindGroupLayout(bindGroupLayoutDesc);

	PipelineLayoutDescriptor layoutDesc{};
	layoutDesc.bindGroupLayoutCount = 1;
	layoutDesc.bindGroupLayouts = (WGPUBindGroupLayout*)&bindGroupLayout;
	PipelineLayout layout = device.createPipelineLayout(layoutDesc);

	// Create a pipeline
	RenderPipelineDescriptor pipelineDesc = Default;
	pipelineDesc.vertex.bufferCount = 0;
	pipelineDesc.vertex.buffers = nullptr;
	pipelineDesc.vertex.module = shaderModule;
	pipelineDesc.vertex.entryPoint = "vs_main";
	pipelineDesc.vertex.constantCount = 0;
	pipelineDesc.vertex.constants = nullptr;

	FragmentState fragmentState{};
	fragmentState.module = shaderModule;
	fragmentState.entryPoint = "fs_main";
	fragmentState.constantCount = 0;
	fragmentState.constants = nullptr;

	BlendState blendState{};
	blendState.color.srcFactor = BlendFactor::SrcAlpha;
	blendState.color.dstFactor = BlendFactor::OneMinusSrcAlpha;
	blendState.color.operation = BlendOperation::Add;
	blendState.alpha.srcFactor = BlendFactor::One;
	blendState.alpha.dstFactor = BlendFactor::Zero;
	blendState.alpha.operation = BlendOperation::Add;

	ColorTargetState colorTarget{};
	colorTarget.format = renderTextureDesc.format;
	colorTarget.blend = &blendState;
	colorTarget.writeMask = ColorWriteMask::All;

	fragmentState.targetCount = 1;
	fragmentState.targets = &colorTarget;
	pipelineDesc.fragment = &fragmentState;

	pipelineDesc.depthStencil = nullptr;
	pipelineDesc.layout = layout;

	RenderPipeline pipeline = device.createRenderPipeline(pipelineDesc);

	m_bindGroupLayout = bindGroupLayout;
	m_pipeline = pipeline;
	m_renderTexture = renderTexture;
	m_renderTextureDesc = renderTextureDesc;
	m_renderTextureView = renderTextureView;
	m_pixelBuffer = pixelBuffer;
	m_pixelBufferDesc = pixelBufferDesc;
}

bool FileRenderer::render(const std::filesystem::path path, wgpu::TextureView textureView) const {
	using namespace wgpu;
	auto device = m_device;
	auto bindGroupLayout = m_bindGroupLayout;
	auto pipeline = m_pipeline;
	auto renderTexture = m_renderTexture;
	auto renderTextureDesc = m_renderTextureDesc;
	auto renderTextureView = m_renderTextureView;
	auto pixelBuffer = m_pixelBuffer;
	auto pixelBufferDesc = m_pixelBufferDesc;

	// Create binding
	std::vector<BindGroupEntry> bindings(1);
	bindings[0].binding = 0;
	bindings[0].textureView = textureView;

	BindGroupDescriptor bindGroupDesc;
	bindGroupDesc.layout = bindGroupLayout;
	bindGroupDesc.entryCount = (uint32_t)bindings.size();
	bindGroupDesc.entries = bindings.data();
	BindGroup bindGroup = device.createBindGroup(bindGroupDesc);

	// Start encoding the commands
	CommandEncoder encoder = device.createCommandEncoder(Default);

	// Create a render pass to render the view
	RenderPassColorAttachment colorAttachment;
	colorAttachment.view = renderTextureView;
	colorAttachment.resolveTarget = nullptr;
	colorAttachment.loadOp = LoadOp::Clear;
	colorAttachment.storeOp = StoreOp::Store;
	colorAttachment.clearValue = Color{ 0.0, 0.0, 0.0, 0.0 };

	RenderPassDescriptor renderPassDesc = Default;
	renderPassDesc.colorAttachmentCount = 1;
	renderPassDesc.colorAttachments = &colorAttachment;
	renderPassDesc.depthStencilAttachment = nullptr;
	renderPassDesc.timestampWriteCount = 0;
	RenderPassEncoder renderPass = encoder.beginRenderPass(renderPassDesc);

	// Render a full screen quad
	renderPass.setPipeline(pipeline);
	renderPass.setBindGroup(0, bindGroup, 0, nullptr);
	renderPass.draw(3, 1, 0, 0);
	renderPass.end();

	// Issue commands
	Queue queue = device.getQueue();
	CommandBuffer command = encoder.finish(Default);
	queue.submit(command);

	encoder.release();
	command.release();
	queue.release();

	return render(path, renderTexture);
}

bool FileRenderer::render(const std::filesystem::path path, wgpu::Texture texture) const {
	using namespace wgpu;
	auto device = m_device;
	auto width = m_width;
	auto height = m_height;
	auto bindGroupLayout = m_bindGroupLayout;
	auto pipeline = m_pipeline;
	//auto renderTextureDesc = m_renderTextureDesc;
	auto pixelBuffer = m_pixelBuffer;
	auto pixelBufferDesc = m_pixelBufferDesc;

	// Start encoding the commands
	CommandEncoder encoder = device.createCommandEncoder(Default);

	// Get pixels
	ImageCopyTexture source = Default;
	source.texture = texture;
	ImageCopyBuffer destination = Default;
	destination.buffer = pixelBuffer;
	destination.layout.bytesPerRow = 4 * width;
	destination.layout.offset = 0;
	destination.layout.rowsPerImage = height;
	encoder.copyTextureToBuffer(source, destination, { width, height, 1 });

	// Issue commands
	Queue queue = device.getQueue();
	CommandBuffer command = encoder.finish(Default);
	queue.submit(command);

	encoder.release();
	command.release();

	// Map buffer
	std::vector<uint8_t> pixels;
	bool done = false;
	bool failed = false;
	auto callbackHandle = pixelBuffer.mapAsync(MapMode::Read, 0, pixelBufferDesc.size, [&](BufferMapAsyncStatus status) {
		if (status != BufferMapAsyncStatus::Success) {
			failed = true;
			done = true;
			return;
		}
		unsigned char* pixelData = (unsigned char*)pixelBuffer.getConstMappedRange(0, pixelBufferDesc.size);
		int bytesPerRow = 4 * width;
		int success = stbi_write_png(path.string().c_str(), (int)width, (int)height, 4, pixelData, bytesPerRow);

		pixelBuffer.unmap();

		failed = success == 0;
		done = true;
	});

	// Wait for mapping
	while (!done) {
#ifdef WEBGPU_BACKEND_WGPU
		wgpuQueueSubmit(queue, 0, nullptr);
#else
		device.tick();
#endif
	}

	queue.release();

	return !failed;
}

bool saveTexture(const std::filesystem::path path, wgpu::Device device, wgpu::Texture texture) {
	using namespace wgpu;
	uint32_t width = texture.getWidth();
	uint32_t height = texture.getHeight();

	static std::unique_ptr<FileRenderer> renderer = nullptr;
	if (!renderer) {
		renderer = std::make_unique<FileRenderer>(device, width, height);
	}

	return renderer->render(path, texture);
}

bool saveTextureView(const std::filesystem::path path, wgpu::Device device, wgpu::TextureView textureView, uint32_t width, uint32_t height) {
	using namespace wgpu;
	static std::unique_ptr<FileRenderer> renderer = nullptr;
	if (!renderer) {
		renderer = std::make_unique<FileRenderer>(device, width, height);
	}

	return renderer->render(path, textureView);
}
