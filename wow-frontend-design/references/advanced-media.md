# Advanced media system

Use this reference for Canvas, WebGL, Three.js, shaders, 3D assets, video, procedural sound, or other media runtimes. Spectacle is optional; fallback, meaning, control, and cleanup are not.

## 1. Write the media contract

```text
medium → product purpose → essential meaning → input/state → runtime/assets → loading/failure/static fallback → accessibility → reduced-data/motion → lifecycle → budget → source/license → evidence
```

Choose the cheapest medium that preserves the idea:

| Need | Prefer | Escalate only when |
| --- | --- | --- |
| texture, shape, simple illustration | CSS or SVG | pixel-level procedural rendering is meaningful |
| photographic/cinematic sequence | responsive image or encoded video | real-time input changes the result |
| many 2D marks/particles | Canvas 2D | retained DOM/SVG becomes a measured bottleneck |
| spatial model, lighting, camera, shader | WebGL/Three.js | the product genuinely benefits from depth or direct manipulation |
| authored linear vector scene | Lottie | the asset workflow is verified and cheaper than native animation |
| interactive vector state machine | Rive | its states replace meaningful application complexity |
| confirmation/atmosphere through sound | Web Audio or an audio asset | the user context supports sound and a silent equivalent exists |

Do not add 3D, particles, shader distortion, autoplay video, or sound only to imitate an award gallery. Tie the medium to a product noun, verb, space, material, data relationship, or emotional register.

## 2. Preserve a complete non-runtime result

- Render the title, explanation, controls, CTA, price/data, and state in semantic UI outside Canvas/WebGL/video.
- Provide a designed poster, still frame, raster/SVG fallback, or direct functional UI when initialization, decoding, GPU, WASM, or JavaScript fails.
- Loading UI reports a real blocking operation and offers recovery. Never manufacture a preloader to stage an entrance.
- Interactive media needs keyboard/touch alternatives, visible focus, instructions that do not rely on gesture alone, and announcements in DOM UI.
- Do not place factual charts, instructions, or product differences only in pixels. Provide a summary and values in text/structured data.

## 3. Control rendering and lifecycle

For Canvas/WebGL/Three.js:

- size from the actual container with `ResizeObserver` or platform equivalent; separate CSS size from backing-store size;
- cap device-pixel ratio and quality by measured target cost, not by assuming every mobile device is weak;
- render on demand for static scenes; if a loop is necessary, stop it off-screen, in hidden documents, under reduced motion when appropriate, and after teardown;
- cancel animation frames and observers; remove listeners; dispose geometries, materials, textures, render targets, loaders, audio nodes, workers, and renderer contexts owned by the view;
- handle resize, orientation, route remount, asset failure, and WebGL context loss/restoration;
- keep input hit targets and scroll/touch policy explicit; canvas gestures must not steal page navigation accidentally;
- budget draw calls, triangles, texture bytes/dimensions, shader variants, post-processing passes, CPU work, GPU memory, and asset decode—not only the JavaScript bundle.

For Three.js specifically:

- pin the exact Three.js minor and record the tested Three revision; inspect its renderer/addon import conventions before copying syntax because WebGL, WebGPU, color management, loaders, post-processing, and examples/addons paths are version-sensitive;
- current Three.js `WebGLRenderer` requires WebGL2; check capability before initialization and never claim an automatic WebGL1 fallback. A separately maintained renderer is required when WebGL1 support is a product requirement;
- size from the owning container, not `window`, and update camera projection, renderer/composer targets, and pointer normalization together;
- use one explicit render-loop owner. Render on demand when possible; otherwise use time deltas, cancel the frame handle, and stop mixers/controls on pause and teardown;
- register ownership for geometries, materials, textures, render targets, skeleton/mixer state, controls, composers/passes, PMREM/environment resources, workers, audio, and the renderer; dispose only resources owned by the view and handle shared caches deliberately;
- validate model/texture provenance, bounds, animation clips, material count, texture color space, camera near/far range, lights/shadows, compressed-decoder paths, and loader failure before revealing the canvas;
- use capability tests and measured quality tiers. Never enable/disable effects only through a mobile user-agent regex or assume a capped DPR alone establishes performance;
- profile each full-screen post-processing pass and render target. A fashionable bloom, blur, chromatic aberration, displacement, or noise pass needs a product role and a cheaper fallback;
- keep the poster visible through capability check, asset load, asynchronous shader compilation, and the first successful frame. Do not remove it when creating the canvas;
- register named `webglcontextcreationerror`, `webglcontextlost`, and `webglcontextrestored` handlers on the canvas before renderer construction. On loss, increment a restoration generation token, stop rendering/loads, and show the poster. If the product will attempt restoration, call `event.preventDefault()` in the loss handler; every asynchronous completion must compare the captured generation before mutating state. If restoration is not supported or its retry budget is exhausted, do not prevent the default—tear down owned work and keep the poster as the permanent result. On restoration, recreate every invalid GPU resource for the current generation and reveal only after another successful first frame;
- make teardown idempotent: clear the animation loop/RAF; abort loads; remove listeners/observers; dispose owned controls, passes/composer, render targets, skeletons, geometries, materials, textures and renderer; close owned `ImageBitmap`s; then remove the canvas;
- test context loss with `WEBGL_lose_context` or the renderer's supported force-loss helper plus forced unsupported/compile/asset failure. Scene removal is not disposal, and the DOM fallback remains available throughout.

For shaders:

- feature-detect and show the fallback on compile/link failure;
- bound uniforms and iteration counts; avoid NaN/Infinity cascades and precision assumptions;
- verify text and controls remain legible over every animated frame;
- do not use a large blur/noise/displacement pass when a small authored asset produces the same result.

Treat external glTF, HDR, textures, shaders and generated scene descriptions as untrusted. Allowlist source/origin and protocol; enforce CORS/CSP; bound download/decode bytes, dimensions, geometry/material/animation counts, shader length, time and memory; reject arbitrary executable GLSL/TSL/WGSL from user/CMS/AI input. A fixed object-count or DPR threshold from another machine is only a candidate tier—quality follows measured drawing-buffer pixels, frame time and target-device evidence.

For Lottie/dotLottie:

- keep authoring, runtime playback, and deployment ingestion as separate trust boundaries;
- pin the player/WASM/renderer and record a compatibility matrix for every shipped path such as Skottie, lottie-web SVG/Canvas, dotLottie, or native players; editor preview equivalence is not assumed;
- reject malformed JSON/ZIP, path traversal, external URLs, expressions or unsupported active features, and impossible compressed/decompressed bytes, dimensions, frame rate/range, layers, masks, paths, precomp recursion, images, fonts, or embedded data before player initialization;
- keep the named poster/static reduced-motion result available when parsing, WASM, font/image decode, renderer, or asset loading fails;
- record runtime, WASM, font, image, artwork, editor/export, and generated-asset licenses separately.

## 4. Use image-first media without faking 3D

For a WebGL hero or visual surface:

1. approve a 2D key visual, rights/provenance, focal point and safe crop;
2. ship an art-directed AVIF/WebP `<picture>` poster; keep heading, data and CTA as semantic HTML;
3. choose explicitly among poster-only, image plane/shader/2.5D displacement, or a real glTF scene—a single image cannot prove real geometry, depth or occlusion;
4. freeze camera, focus, depth layers, palette, motion envelope, seed/time and static/reduced result;
5. crossfade only after assets, async compile and the first successful frame; no-JS, reduced motion, constrained tier, CORS/asset failure and context loss keep the same poster;
6. if producing a poster from WebGL, render it at build time with pinned runtime, viewport, DPR, camera, seed and time. Do not keep `preserveDrawingBuffer: true` in production just for capture;
7. test poster LCP/CLS, loss/restoration, route unmount/remount, hidden/off-screen pause, and low/medium/high target devices.

## 5. Load assets intentionally

- Give visible first-frame/LCP media priority; lazy-load below-fold or optional experiences.
- Compress geometry, textures, video, and audio with formats supported by the target matrix; keep a tested fallback where required.
- Reserve aspect ratio and avoid replacing a lightweight poster with a blank runtime canvas before readiness.
- Abort stale asset requests and reject impossible byte, dimension, duration, node, and geometry counts.
- Cache/version first-party assets according to deployment policy. Do not hotlink mutable demos or assets with unknown rights.
- Record creator/source, asset license, runtime license, editor/export terms, modification, attribution, and generated-AI provenance where relevant.
- Treat generated shaders, vector scenes, SVG, models, textures, and provider responses as untrusted inputs. A remote AI provider is opt-in: disclose endpoint/operator, data sent, retention, cost, credential path, output-rights uncertainty, and fallback before transmitting project material. Never forward an API key to a user-configurable third-party base URL without explicit authorization.

## 6. Video and sound are user-controlled media

Video:

- provide captions for relevant speech/audio, transcript or description where required, and accessible controls;
- avoid autoplay with sound; do not make an autoplay background the only carrier of meaning;
- respect reduced motion/data intent with a poster or manual play path where continuous movement or bandwidth is not essential;
- verify crop, focal point, captions, controls, picture-in-picture/fullscreen policy, and failure at mobile/desktop sizes.

Sound:

- start only after a user gesture and clear product intent; expose mute/volume when sound persists;
- never make confirmation, warning, navigation, or game state available only through audio;
- stop/disconnect audio nodes and release buffers/listeners on teardown;
- test silent mode, assistive technology, repeated rapid input, background tabs, and environments where audio is inappropriate;
- avoid pretending generated sound is a licensed brand asset; record model/tool and usage rights.

## 7. Verify on constrained and failure paths

Minimum evidence:

- poster/static fallback before runtime and after forced initialization/asset failure;
- 390px touch, desktop pointer, keyboard, zoom/text resize, reduced motion, reduced-data policy where supported, and no-hover;
- performance trace on representative constrained hardware/profile: main-thread tasks, frame time, layout/paint, GPU/memory signals, network/decode, and LCP/CLS interaction;
- background/off-screen CPU reaches the declared idle behavior;
- repeated mount/unmount does not multiply loops, listeners, contexts, audio nodes, workers, or memory;
- context loss, orientation/resize, route transition, Back/Forward, modal/scroll, and tab visibility behavior;
- console and network failures, missing assets, and unsupported capability fallback;
- actual target-browser/device screenshots, not a desktop shader preview alone.

Release blockers:

- essential product meaning exists only in pixels, motion, video, or sound;
- blank or blocking experience on runtime failure;
- unbounded render/audio loop or leaked GPU/WASM/media resources;
- stolen scroll/zoom/gesture, inaccessible controls, or no reduced result;
- unknown asset, model, editor/export, library, or commercial license;
- claiming smoothness from an FPS overlay without a trace and target-device evidence.

Primary baselines: [Khronos WebGL 2](https://registry.khronos.org/webgl/specs/2.0.0/), [MDN WebGL best practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices), [Three.js WebGL compatibility](https://threejs.org/manual/en/webgl-compatibility-check.html), [Three.js disposal](https://threejs.org/manual/en/how-to-dispose-of-objects.html), [responsive rendering](https://threejs.org/manual/en/responsive.html), and [rendering on demand](https://threejs.org/manual/en/rendering-on-demand.html). Version-sensitive manual pages guide implementation; browser/device tests remain the evidence.
