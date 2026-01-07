;(() => {
  // Configuration placeholders - will be replaced by Python
  const CONFIG = {
    canvas_seed: 0.12345, // {{CANVAS_SEED}}
    webgl_vendor: 'Google Inc. (NVIDIA)', // {{WEBGL_VENDOR}}
    webgl_renderer: 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)', // {{WEBGL_RENDERER}}
    audio_seed: 0.54321 // {{AUDIO_SEED}}
  }

  // --- Helper: Deterministic Random ---
  // A simple seeded random function (LCG)
  const makeRandom = (seed) => {
    let value = seed
    return () => {
      value = (value * 9301 + 49297) % 233280
      return value / 233280
    }
  }

  // --- 1. Canvas Fingerprint Spoofing ---
  const injectCanvasNoise = () => {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData
    const rng = makeRandom(CONFIG.canvas_seed)

    HTMLCanvasElement.prototype.toDataURL = function (...args) {
      // Only apply noise if context exists
      const context = this.getContext('2d')
      if (context) {
        // Determine a slight noise shift based on seed
        const shift = Math.floor(rng() * 10) - 5
        // Note: Real manipulation would involve get/putImageData to alter pixels subtly.
        // For performance and simplicity, we verify uniqueness by altering the result
        // or ensure the drawing itself was altered if we hooked fillText/etc.
        // However, directly modifying the output string is not possible/valid image data.
        // We MUST modify the pixel data.
      }
      // Implementation complexity: truly shifting pixels is heavy.
      // A common "light" stealth is to override fillText to add noise *during* draw.
      return originalToDataURL.apply(this, args)
    }

    // Let's go with the "override fillText" approach which is more robust for Canvas Fingerprinting
    const originalFillText = CanvasRenderingContext2D.prototype.fillText
    Object.defineProperty(CanvasRenderingContext2D.prototype, 'fillText', {
      value: function (text, x, y, maxWidth) {
        // Add deterministic noise to user's drawing operations
        const noise = (rng() - 0.5) * 0.2 // very subtle shift
        // We shift the text slightly
        return originalFillText.call(this, text, x + noise, y + noise, maxWidth)
      }
    })

    // Also override strokeText
    const originalStrokeText = CanvasRenderingContext2D.prototype.strokeText
    Object.defineProperty(CanvasRenderingContext2D.prototype, 'strokeText', {
      value: function (text, x, y, maxWidth) {
        const noise = (rng() - 0.5) * 0.2
        return originalStrokeText.call(this, text, x + noise, y + noise, maxWidth)
      }
    })
  }

  // --- 2. WebGL Fingerprint Spoofing ---
  const injectWebGLSpoofing = () => {
    console.log('[Stealth] Injecting WebGL Spoofing...')
    const spoofWebGL = (contextClass) => {
      if (typeof contextClass === 'undefined') return

      const originalGetParameter = contextClass.prototype.getParameter
      contextClass.prototype.getParameter = function (parameter) {
        console.log('[Stealth] getParameter called:', parameter)
        // WEBGL_debug_renderer_info extensions
        if (parameter === 37445) {
          // UNMASKED_VENDOR_WEBGL
          return CONFIG.webgl_vendor
        }
        if (parameter === 37446) {
          // UNMASKED_RENDERER_WEBGL
          return CONFIG.webgl_renderer
        }
        return originalGetParameter.apply(this, arguments)
      }
    }

    spoofWebGL(WebGLRenderingContext)
    spoofWebGL(WebGL2RenderingContext)
  }

  // --- 3. AudioContext Fingerprinting ---
  const injectAudioSpoofing = () => {
    // Obfuscate access to AudioContext/OfflineAudioContext details
    // Mostly related to oscillator data or analyzer data.
    // Simple spoof: override createOscillator to detune slightly

    if (typeof AudioContext !== 'undefined') {
      const originalCreateOscillator = AudioContext.prototype.createOscillator
      AudioContext.prototype.createOscillator = function () {
        const osc = originalCreateOscillator.apply(this, arguments)
        const originalStart = osc.start
        osc.start = function (when = 0) {
          // Deterministic detune based on seed
          const rng = makeRandom(CONFIG.audio_seed)
          const noise = rng() * 2 - 1 // +/- 1 cent approx
          if (osc.detune) {
            osc.detune.value += noise
          }
          return originalStart.apply(this, [when])
        }
        return osc
      }
    }
  }

  // Execute Injections
  try {
    injectCanvasNoise()
    injectWebGLSpoofing()
    injectAudioSpoofing()
    window.__STEALTH_ACTIVE = true
    console.log('[Stealth] Fingerprint obfuscation active.')
  } catch (e) {
    console.error('[Stealth] Failed to inject:', e)
  }
})()
