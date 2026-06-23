"use client";

/**
 * CommerceMind VoiceCare AI — Audio-Reactive Voice Orb
 * 3D animated orb using react-three-fiber that reacts to voice input.
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

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uAudioLevel: { value: 0 },
      uIsListening: { value: 0 },
      uIsProcessing: { value: 0 },
      uColor1: { value: new THREE.Color("#4F46E5") },
      uColor2: { value: new THREE.Color("#06B6D4") },
      uColor3: { value: new THREE.Color("#8B5CF6") },
    }),
    []
  );

  const vertexShader = `
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uIsListening;
    varying vec2 vUv;
    varying float vDisplacement;
    
    // Simplex noise
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
    
    float snoise(vec3 v) {
      const vec2 C = vec2(1.0/6.0, 1.0/3.0);
      const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
      vec3 i = floor(v + dot(v, C.yyy));
      vec3 x0 = v - i + dot(i, C.xxx);
      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
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
      vec3 ns = n_ * D.wyz - D.xzx;
      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_);
      vec4 x = x_ * ns.x + ns.yyyy;
      vec4 y = y_ * ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);
      vec4 b0 = vec4(x.xy, y.xy);
      vec4 b1 = vec4(x.zw, y.zw);
      vec4 s0 = floor(b0)*2.0 + 1.0;
      vec4 s1 = floor(b1)*2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));
      vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
      vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
      vec3 p0 = vec3(a0.xy, h.x);
      vec3 p1 = vec3(a0.zw, h.y);
      vec3 p2 = vec3(a1.xy, h.z);
      vec3 p3 = vec3(a1.zw, h.w);
      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
      p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
    }
    
    void main() {
      vUv = uv;
      float baseDisplacement = 0.05;
      float audioDisplacement = uAudioLevel * 0.3 * uIsListening;
      float noiseVal = snoise(position * 2.0 + uTime * 0.5) * (baseDisplacement + audioDisplacement);
      noiseVal += snoise(position * 4.0 + uTime * 0.8) * 0.02;
      vDisplacement = noiseVal;
      vec3 newPosition = position + normal * noiseVal;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `;

  const fragmentShader = `
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uIsListening;
    uniform float uIsProcessing;
    uniform vec3 uColor1;
    uniform vec3 uColor2;
    uniform vec3 uColor3;
    varying vec2 vUv;
    varying float vDisplacement;
    
    void main() {
      float mixFactor = vUv.y + sin(uTime * 0.5) * 0.2;
      vec3 color = mix(uColor1, uColor2, mixFactor);
      color = mix(color, uColor3, vDisplacement * 3.0 + 0.3);
      
      // Brighter when listening
      float brightness = 0.8 + uIsListening * 0.4 + uAudioLevel * 0.3;
      
      // Pulse when processing
      float pulse = uIsProcessing * sin(uTime * 3.0) * 0.15;
      brightness += pulse;
      
      // Fresnel-like edge glow
      float fresnel = pow(1.0 - abs(dot(vec3(0.0, 0.0, 1.0), normalize(vec3(vUv - 0.5, 0.5)))), 2.0);
      color += vec3(0.2, 0.4, 1.0) * fresnel * 0.3;
      
      gl_FragColor = vec4(color * brightness, 0.95);
    }
  `;

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    materialRef.current.uniforms.uTime.value = t;
    materialRef.current.uniforms.uAudioLevel.value = audioLevel;
    materialRef.current.uniforms.uIsListening.value = isListening ? 1.0 : 0.0;
    materialRef.current.uniforms.uIsProcessing.value = isProcessing ? 1.0 : 0.0;

    // Gentle rotation
    meshRef.current.rotation.y = t * 0.15;
    meshRef.current.rotation.x = Math.sin(t * 0.1) * 0.1;

    // Scale breathing
    const baseScale = 1.0;
    const breathe = Math.sin(t * 0.8) * 0.03;
    const audioScale = audioLevel * 0.15;
    const s = baseScale + breathe + audioScale;
    meshRef.current.scale.setScalar(s);
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

// Ambient particles
function Particles() {
  const count = 200;
  const ref = useRef<THREE.Points>(null!);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return pos;
  }, []);

  useFrame((state) => {
    ref.current.rotation.y = state.clock.getElapsedTime() * 0.02;
    ref.current.rotation.x = state.clock.getElapsedTime() * 0.01;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#6366F1"
        transparent
        opacity={0.4}
        sizeAttenuation
      />
    </points>
  );
}

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  audioLevel: number;
}

export default function VoiceOrb({
  isListening,
  isProcessing,
  audioLevel,
}: VoiceOrbProps) {
  return (
    <div className="w-full h-full" style={{ minHeight: "300px" }}>
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} intensity={0.8} color="#4F46E5" />
        <pointLight position={[-5, -5, 5]} intensity={0.4} color="#06B6D4" />
        <OrbMesh
          isListening={isListening}
          isProcessing={isProcessing}
          audioLevel={audioLevel}
        />
        <Particles />
      </Canvas>
    </div>
  );
}
