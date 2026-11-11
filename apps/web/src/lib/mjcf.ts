export type MjcfInput = {
  type: 'quadruped' | 'wheel_legged' | 'humanoid' | 'arm'
  dof: number
  mass_kg: number
  tau_peak_Nm: number
  modelName: string
}

type JointSpec = {
  name: string
  axis: 'x' | 'y' | 'z'
  range: [number, number]
  length: number
  radius: number
  mass: number
}

const num = (v: number) => String(parseFloat(v.toPrecision(4)))

function jointXml(j: JointSpec, continuous = false): string {
  const axis = j.axis === 'x' ? '1 0 0' : j.axis === 'y' ? '0 1 0' : '0 0 1'
  const range = continuous ? '' : ` range="${num(j.range[0])} ${num(j.range[1])}"`
  return `<joint name="${j.name}" type="${continuous ? 'continuous' : 'hinge'}" axis="${axis}"${range}/>`
}


export function buildMjcf(input: MjcfInput): string {
  const { type, mass_kg: mass, tau_peak_Nm: tau, modelName } = input
  const scale = Math.cbrt(Math.max(mass, 0.5) / 20)
  const trunkMass = Math.max(0.2, mass * 0.55)
  const limbMass = Math.max(0.05, (mass - trunkMass) / Math.max(4, input.dof))
  const thighLen = 0.24 * scale
  const calfLen = 0.24 * scale
  const thighRadius = 0.035 * scale
  const pelvisZ = type === 'arm' ? 0.2 : 0.35 * scale + thighLen + calfLen



  const leg = (prefix: string, side: number, forward: number): string => {
    const hipRoll: JointSpec = { name: `${prefix}_hip_roll`, axis: 'x', range: [-0.6, 0.6], length: 0.04 * scale, radius: thighRadius * 0.8, mass: limbMass }
    const hipPitch: JointSpec = { name: `${prefix}_hip_pitch`, axis: 'y', range: [-1.2, 1.2], length: thighLen, radius: thighRadius, mass: limbMass * 2 }
    const knee: JointSpec = { name: `${prefix}_knee`, axis: 'y', range: [-2.4, 0.2], length: calfLen, radius: thighRadius * 0.8, mass: limbMass * 1.6 }
    const wheel: JointSpec = { name: `${prefix}_wheel`, axis: 'y', range: [0, 0], length: 0.08, radius: 0.08 * scale, mass: limbMass }
    const parts = [hipRoll, hipPitch, knee]
    if (type === 'wheel_legged') parts.push(wheel)
    let xml = `<body name="${prefix}_leg" pos="${num(0.18 * scale * forward)} ${num(0.12 * scale * side)} 0">`
    let close = ''
    let pos = '0 0 0'
    parts.forEach((j, i) => {
      const isWheel = j.name.endsWith('_wheel')
      const tail = isWheel
        ? `<geom name="${j.name}_geom" type="cylinder" axis="0 1 0" size="${num(j.radius)} ${num(0.03 * scale)}" mass="${num(j.mass)}"/>`
        : (i === parts.length - 1
          ? `<geom name="${j.name}_geom" type="capsule" fromto="0 0 0 0 0 ${num(-j.length)}" size="${num(j.radius)}" mass="${num(j.mass)}"/>`
          : '')
      xml += `<body name="${prefix}_${j.name}_link" pos="${pos}">${jointXml(j, isWheel)}${tail}`
      close = '</body>' + close
      pos = `0 0 ${num(-j.length)}`
    })
    return xml + close + '</body>'
  }

  let xml = ''
  const motors: string[] = []
  let hingeCount = 0

  if (type === 'quadruped' || type === 'wheel_legged') {
    xml += `<body name="base" pos="0 0 ${num(pelvisZ)}">`
    xml += `<freejoint name="root"/>`
    xml += `<geom name="trunk" type="box" size="${num(0.3 * scale)} ${num(0.14 * scale)} ${num(0.08 * scale)}" mass="${num(trunkMass)}"/>`
    xml += `<site name="imu" pos="0 0 0" size="0.01"/>`
    xml += leg('FL', 1, 1) + leg('FR', -1, 1) + leg('RL', 1, -1) + leg('RR', -1, -1)
    xml += '</body>'
    for (const p of ['FL', 'FR', 'RL', 'RR']) {
      const names = type === 'wheel_legged'
        ? [`${p}_hip_roll`, `${p}_hip_pitch`, `${p}_knee`, `${p}_wheel`]
        : [`${p}_hip_roll`, `${p}_hip_pitch`, `${p}_knee`]
      for (const n of names) { motors.push(n); hingeCount++ }
    }
  } else if (type === 'humanoid') {
    const armPerSide = Math.max(1, Math.min(5, Math.floor((input.dof - 13) / 2)))
    const humanLeg = (prefix: string, side: number): string => {
      let s = `<body name="${prefix}_leg" pos="0 ${num(0.1 * scale * side)} 0">`
      let close = ''
      let pos = '0 0 0'
      const joints: JointSpec[] = [
        { name: 'hip_roll', axis: 'x', range: [-0.4, 0.4], length: 0.03 * scale, radius: thighRadius * 0.7, mass: limbMass },
        { name: 'hip_pitch', axis: 'y', range: [-1.4, 1.0], length: thighLen, radius: thighRadius, mass: limbMass * 2 },
        { name: 'hip_yaw', axis: 'z', range: [-0.6, 0.6], length: 0.02 * scale, radius: thighRadius * 0.6, mass: limbMass },
        { name: 'knee', axis: 'y', range: [-2.3, 0.1], length: calfLen, radius: thighRadius * 0.8, mass: limbMass * 1.5 },
        { name: 'ankle_pitch', axis: 'y', range: [-0.9, 0.5], length: 0.04 * scale, radius: thighRadius * 0.5, mass: limbMass * 0.6 },
        { name: 'ankle_roll', axis: 'x', range: [-0.3, 0.3], length: 0.02 * scale, radius: thighRadius * 0.4, mass: limbMass * 0.4 },
      ]
      joints.forEach((j, i) => {
        const tail = i === joints.length - 1
          ? `<geom name="${prefix}_${j.name}_geom" type="capsule" fromto="0 0 0 0 0 ${num(-j.length)}" size="${num(j.radius)}" mass="${num(j.mass)}"/>`
          : ''
        s += `<body name="${prefix}_${j.name}_link" pos="${pos}">${jointXml(j)}${tail}`
        close = '</body>' + close
        pos = `0 0 ${num(-j.length)}`
      })
      return s + close + '</body>'
    }
    const arm = (prefix: string, side: number): string => {
      let s = `<body name="${prefix}_arm" pos="0 ${num(0.18 * scale * side)} ${num(0.04 * scale)}">`
      let close = ''
      let pos = '0 0 0'
      const names = ['shoulder_pitch', 'shoulder_roll', 'shoulder_yaw', 'elbow', 'wrist']
      names.slice(0, armPerSide).forEach((n, i) => {
        const j: JointSpec = {
          name: `${prefix}_${n}`, axis: i === 0 ? 'y' : i === 1 ? 'x' : i === 2 ? 'z' : 'y',
          range: [-1.5, 1.5], length: 0.12 * scale, radius: thighRadius * 0.5, mass: limbMass * 0.8,
        }
        const tail = i === armPerSide - 1
          ? `<geom name="${j.name}_geom" type="capsule" fromto="0 0 0 0 0 ${num(-j.length)}" size="${num(j.radius)}" mass="${num(j.mass)}"/>`
          : ''
        s += `<body name="${j.name}_link" pos="${pos}">${jointXml(j)}${tail}`
        close = '</body>' + close
        pos = `0 0 ${num(-j.length)}`
      })
      return s + close + '</body>'
    }
    xml += `<body name="base" pos="0 0 ${num(pelvisZ)}"><freejoint name="root"/>`
    xml += `<geom name="pelvis" type="box" size="${num(0.12 * scale)} ${num(0.18 * scale)} ${num(0.08 * scale)}" mass="${num(trunkMass * 0.6)}"/>`
    xml += `<site name="imu" pos="0 0 0" size="0.01"/>`
    xml += `<body name="torso" pos="0 0 ${num(0.1 * scale)}"><joint name="torso_yaw" axis="0 0 1" range="-0.8 0.8"/><geom name="torso_geom" type="box" size="${num(0.14 * scale)} ${num(0.2 * scale)} ${num(0.2 * scale)}" mass="${num(trunkMass * 0.4)}"/>`
    xml += `<body name="head" pos="0 0 ${num(0.25 * scale)}"><geom name="head_geom" type="sphere" size="${num(0.07 * scale)}" mass="${num(limbMass * 2)}"/></body>`
    xml += arm('L', 1) + arm('R', -1)
    xml += '</body>' + humanLeg('L', 1) + humanLeg('R', -1) + '</body>'
    motors.push('torso_yaw'); hingeCount++
    for (const p of ['L', 'R']) {
      for (const n of ['hip_roll', 'hip_pitch', 'hip_yaw', 'knee', 'ankle_pitch', 'ankle_roll']) {
        motors.push(`${p}_${n}`); hingeCount++
      }
      for (const n of ['shoulder_pitch', 'shoulder_roll', 'shoulder_yaw', 'elbow', 'wrist'].slice(0, armPerSide)) {
        motors.push(`${p}_${n}`); hingeCount++
      }
    }
  } else {
    // 6 轴机械臂：固定基座 + 竖直链。
    xml += `<body name="base" pos="0 0 ${num(pelvisZ)}"><geom name="base_geom" type="cylinder" size="${num(0.08 * scale)} ${num(0.05 * scale)}" mass="${num(trunkMass)}"/>`
    let close = ''
    let pos = '0 0 0'
    const names = ['j1', 'j2', 'j3', 'j4', 'j5', 'j6']
    names.slice(0, input.dof).forEach((n, i) => {
      const j: JointSpec = {
        name: n, axis: i % 2 === 0 ? 'z' : 'y', range: [-2.8, 2.8],
        length: 0.18 * scale, radius: 0.03 * scale, mass: limbMass * 1.5,
      }
      const tail = i === Math.min(input.dof, 6) - 1
        ? `<geom name="${n}_geom" type="capsule" fromto="0 0 0 0 0 ${num(-j.length)}" size="${num(j.radius)}" mass="${num(j.mass)}"/>`
        : ''
      xml += `<body name="${n}_link" pos="${pos}">${jointXml(j)}${tail}`
      close = '</body>' + close
      pos = `0 0 ${num(-j.length)}`
      motors.push(n); hingeCount++
    })
    xml += close + '</body>'
  }

  const actuator = motors.map(n => `    <motor name="${n}_motor" joint="${n}" ctrlrange="${num(-tau)} ${num(tau)}" gear="1"/>`).join('\n')

  return `<mujoco model="${modelName}">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <default>
    <joint damping="0.5" armature="0.01"/>
  </default>
  <!-- 由 RoboWiki 选型台生成：几何为胶囊/盒体占位，质量和扭矩来自参考机型与所选执行器；不是 CAD 模型。 -->
  <worldbody>
    <light name="key" pos="0 0 3" dir="0 0 -1" directional="true"/>
    <geom name="floor" type="plane" size="6 6 0.1" rgba="0.9 0.9 0.9 1"/>
${xml.split('\n').map(l => '    ' + l).join('\n')}
  </worldbody>
  <actuator>
${actuator}
  </actuator>
  <keyframe>
    <key name="home" qpos="${Array(hingeCount + (type === 'arm' ? 0 : 7)).fill('0').join(' ')}"/>
  </keyframe>
</mujoco>
`
}
