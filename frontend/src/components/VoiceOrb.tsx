"use client";

/**
 * CommerceMind VoiceCare AI — Voice Orb v2
 * Design brief: coral-orange core → black edges (warm duotone).
 * States: idle (4s breathe) | listening (audio-reactive) | thinking (fast pulse + ring) | speaking (amplitude sync)
 */

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface OrbMeshProps {
  isListening: boolean;
  isProcessing: boolean;
  audioLevel: number;
}

function OrbMesh({ isListening, isProcessing, audioLevel }: OrbMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null!);
  const materialRef = useRef<THREE.ShaderMaterial>(null!);

  // Coral-orange (#FF5A2B) → deep near-black at edges — warm duotone per design brief
  const uniforms = useMemo(
    () => ({
      uTime:        { value: 0 },
      uAudioLevel:  { value: 0 },
      uIsListening: { value: 0 },
      uIsProcessing:{ value: 0 },
      uColor1:      { value: new THREE.Color("#FF5A2B") }, // accent coral-orange core
      uColor2:      { value: new THREE.Color("#7A1E05") }, // deep burnt, mid-orb
      uColor3:      { value: new THREE.Color("#0B0B0C") }, // near-black at edges
    }),
    []
  );

  const vertexShader = `
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uIsListening;
    varying vec2 vUv;
    varying float vDisplacement;
    varying vec3 vNormal;

    // Simplex noise
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

    float snoise(vec3 v) {
      const vec2 C = vec2(1.0/6.0, 1.0/3.0);
      const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
      vec3 i  = floor(v + dot(v, C.yyy));
      vec3 x0 = v - i + dot(i, C.xxx);
      vec3 g  = step(x0.yzx, x0.xyz);
      vec3 l  = 1.0 - g;
      vec3 i1 = min(g.xyz, l.zxy);
      vec3 i2 = max(g.xyz, l.zxy);
      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy;
      vec3 x3 = x0 - D.yyy;
      i = mod289(i);
      vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
        + i.y + vec4(0.0, i1.y, i2.y, 1.0))
        + i.x + vec4(0.0, i1.x, i2.x, 1.0));
      float n_ = 0.142857142857;
      vec3  ns = n_ * D.wyz - D.xzx;
      vec4 j   = p - 49.0 * floor(p * ns.z * ns.z);
      vec4 x_  = floor(j * ns.z);
      vec4 y_  = floor(j - 7.0 * x_);
      vec4 x   = x_ * ns.x + ns.yyyy;
      vec4 y   = y_ * ns.x + ns.yyyy;
      vec4 h   = 1.0 - abs(x) - abs(y);
      vec4 b0  = vec4(x.xy, y.xy);
      vec4 b1  = vec4(x.zw, y.zw);
      vec4 s0  = floor(b0)*2.0 + 1.0;
      vec4 s1  = floor(b1)*2.0 + 1.0;
      vec4 sh  = -step(h, vec4(0.0));
      vec4 a0  = b0.xzyw + s0.xzyw*sh.xxyy;
      vec4 a1  = b1.xzyw + s1.xzyw*sh.zzww;
      vec3 p0  = vec3(a0.xy, h.x);
      vec3 p1  = vec3(a0.zw, h.y);
      vec3 p2  = vec3(a1.xy, h.z);
      vec3 p3  = vec3(a1.zw, h.w);
      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
      p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
    }

    void main() {
      vUv    = uv;
      vNormal= normal;

      // Idle: very small noise. Listening: high audio-reactive turbulence.
      float base  = 0.04;
      float audio = uAudioLevel * 0.28 * uIsListening;
      float noise = snoise(position * 2.0 + uTime * 0.4) * (base + audio);
      noise += snoise(position * 5.0 + uTime * 0.9) * 0.015;
      vDisplacement = noise;

      vec3 newPos = position + normal * noise;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos, 1.0);
    }
  `;

  const fragmentShader = `
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uIsListening;
    uniform float uIsProcessing;
    uniform vec3  uColor1;
    uniform vec3  uColor2;
    uniform vec3  uColor3;
    varying vec2  vUv;
    varying float vDisplacement;
    varying vec3  vNormal;

    void main() {
      // Fresnel: bright coral core, near-black at rim
      vec3 viewDir   = vec3(0.0, 0.0, 1.0);
      float fresnel  = 1.0 - abs(dot(normalize(vNormal), viewDir));
      fresnel        = pow(fresnel, 1.8);

      // Core: hot coral; rim: bg-base near-black
      vec3 coreColor = mix(uColor1, uColor2, vUv.y * 0.5 + vDisplacement * 2.0);
      vec3 color     = mix(coreColor, uColor3, fresnel * 0.85);

      // Listening: more vivid
      float vividness = 0.85 + uIsListening * 0.2 + uAudioLevel * uIsListening * 0.25;

      // Thinking: fast pulse (1.5s), distinct from listening
      float think = uIsProcessing * (1.0 - uIsListening) * (sin(uTime * 4.2) * 0.5 + 0.5) * 0.2;

      float brightness = vividness + think;

      gl_FragColor = vec4(color * brightness, 0.97);
    }
  `;

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    materialRef.current.uniforms.uTime.value        = t;
    materialRef.current.uniforms.uAudioLevel.value  = audioLevel;
    materialRef.current.uniforms.uIsListening.value = isListening ? 1.0 : 0.0;
    materialRef.current.uniforms.uIsProcessing.value= isProcessing ? 1.0 : 0.0;

    // Idle: breathe 1.0→1.04→1.0 over 4s
    // Listening: scale driven by audio level
    // Thinking: tighter 1.5s pulse
    let scale = 1.0;
    if (isListening) {
      scale = 1.0 + audioLevel * 0.18;
    } else if (isProcessing) {
      scale = 1.0 + Math.sin(t * (Math.PI * 2 / 1.5)) * 0.04;
    } else {
      scale = 1.0 + Math.sin(t * (Math.PI * 2 / 4.0)) * 0.04;
    }
    meshRef.current.scale.setScalar(scale);

    // Gentle rotation
    meshRef.current.rotation.y = t * 0.12;
    meshRef.current.rotation.x = Math.sin(t * 0.07) * 0.08;
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.2, 64]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent
      />
    </mesh>
  );
}

// Thinking ring: thin rotating ring, only during processing
function ThinkingRing({ isProcessing }: { isProcessing: boolean }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (!ref.current) return;
    ref.current.visible = isProcessing;
    ref.current.rotation.z = state.clock.getElapsedTime() * 2.0;
    ref.current.rotation.x = Math.PI / 2;
  });
  return (
    <mesh ref={ref}>
      <torusGeometry args={[1.5, 0.012, 8, 80]} />
      <meshBasicMaterial color="#FF5A2B" transparent opacity={0.5} />
    </mesh>
  );
}

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  audioLevel: number;
}

export default function VoiceOrb({ isListening, isProcessing, audioLevel }: VoiceOrbProps) {
  return (
    <div className="w-full h-full" style={{ minHeight: "300px" }}>
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.2} />
        {/* Warm key light from above-left, accent color */}
        <pointLight position={[3, 4, 3]}  intensity={1.2} color="#FF5A2B" />
        {/* Cooler fill from below */}
        <pointLight position={[-3, -3, 2]} intensity={0.3} color="#7A1E05" />
        <OrbMesh
          isListening={isListening}
          isProcessing={isProcessing}
          audioLevel={audioLevel}
        />
        <ThinkingRing isProcessing={isProcessing && !isListening} />
      </Canvas>
    </div>
  );
}
