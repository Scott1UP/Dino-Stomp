import * as THREE from 'three';

/**
 * The three-band gradient every toon material shares. Nearest filtering with
 * no mipmaps keeps the steps crisp; the default filtering would smooth them
 * back into a soft gradient.
 */
export const toonGradient = (() => {
  const texture = new THREE.DataTexture(new Uint8Array([120, 195, 255]), 3, 1, THREE.RedFormat);
  texture.minFilter = THREE.NearestFilter;
  texture.magFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  return texture;
})();

/**
 * Multiply a greyscale detail texture over a toon material's lighting, so flat
 * colours pick up roof tiles, brick courses, planks or a ground weave.
 *
 * It rides on three's ambient-occlusion slot (which already carries its own UV
 * set), but applies to all the light, not just the ambient part.
 *
 * `perVertex`: the mesh's vertex colour picks which channel of the texture a
 * face uses (or none). Otherwise the red channel is used everywhere.
 */
export function addDetail(material: THREE.MeshToonMaterial, texture: THREE.Texture, perVertex: boolean) {
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.NoColorSpace;
  texture.channel = perVertex ? 1 : 0;
  texture.needsUpdate = true;
  material.aoMap = texture;
  material.vertexColors = perVertex;
  material.onBeforeCompile = (shader) => {
    const sample = perVertex
      ? `vec3 detailTexel = texture2D( aoMap, vAoMapUv ).rgb;
         float detailWeight = clamp( vColor.r + vColor.g + vColor.b, 0.0, 1.0 );
         float detail = mix( 1.0, dot( detailTexel, vColor.rgb ), detailWeight );`
      : `float detail = texture2D( aoMap, vAoMapUv ).r;`;
    shader.fragmentShader = shader.fragmentShader
      // The vertex colour is a pattern selector here, not a tint.
      .replace('#include <color_fragment>', '')
      .replace(
        '#include <aomap_fragment>',
        `${sample}
         reflectedLight.directDiffuse *= detail;
         reflectedLight.indirectDiffuse *= detail;`,
      );
  };
  material.needsUpdate = true;
  return material;
}

/** A soft blotchy weave for the ground, made in code: it repeats every few metres to add close-up texture. */
export function groundWeave() {
  const size = 128;
  const data = new Uint8Array(size * size * 4);
  let seed = 7;
  const random = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < size * size; i++) {
    const x = i % size;
    const y = Math.floor(i / size);
    // A woven look: faint crossing threads plus grain.
    const weave = (Math.sin((x / size) * Math.PI * 16) + Math.sin((y / size) * Math.PI * 16)) * 0.012;
    const value = Math.round(255 * Math.min(1, 0.94 + weave + random() * 0.07));
    data[i * 4] = data[i * 4 + 1] = data[i * 4 + 2] = value;
    data[i * 4 + 3] = 255;
  }
  const texture = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  return texture;
}
