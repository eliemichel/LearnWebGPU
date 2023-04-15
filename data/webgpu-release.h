/**
 * This file is part of the "Learn WebGPU for C++" book.
 *   https://eliemichel.github.io/LearnWebGPU
 * 
 * MIT License
 * Copyright (c) 2022-2023 Elie Michel
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#pragma once
#include <webgpu/webgpu.h>

// Dawn and wgpu-native do not agree yet on the lifetime management
// of objects. We align on Dawn convention of calling "release" the
// methods that free memory for objects created with wgpuCreateSomething.
// (The key difference is that Dawn also offers a "reference" function to
// increment a reference counter, and release decreases this counter and
// actually frees memory only when the counter gets to 0)
#ifdef WEBGPU_BACKEND_WGPU
#include <webgpu/wgpu.h>
#define wgpuInstanceRelease wgpuInstanceDrop
#define wgpuAdapterRelease wgpuAdapterDrop
#define wgpuBindGroupRelease wgpuBindGroupDrop
#define wgpuBindGroupLayoutRelease wgpuBindGroupLayoutDrop
#define wgpuBufferRelease wgpuBufferDrop
#define wgpuCommandBufferRelease wgpuCommandBufferDrop
#define wgpuCommandEncoderRelease wgpuCommandEncoderDrop
#define wgpuRenderPassEncoderRelease wgpuRenderPassEncoderDrop
#define wgpuComputePassEncoderRelease wgpuComputePassEncoderDrop
#define wgpuRenderBundleEncoderRelease wgpuRenderBundleEncoderDrop
#define wgpuComputePipelineRelease wgpuComputePipelineDrop
#define wgpuDeviceRelease wgpuDeviceDrop
#define wgpuPipelineLayoutRelease wgpuPipelineLayoutDrop
#define wgpuQuerySetRelease wgpuQuerySetDrop
#define wgpuRenderBundleRelease wgpuRenderBundleDrop
#define wgpuRenderPipelineRelease wgpuRenderPipelineDrop
#define wgpuSamplerRelease wgpuSamplerDrop
#define wgpuShaderModuleRelease wgpuShaderModuleDrop
#define wgpuSurfaceRelease wgpuSurfaceDrop
#define wgpuSwapChainRelease wgpuSwapChainDrop
#define wgpuTextureRelease wgpuTextureDrop
#define wgpuTextureViewRelease wgpuTextureViewDrop
#endif
