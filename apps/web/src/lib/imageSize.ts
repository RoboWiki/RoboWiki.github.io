import fs from 'node:fs'
import path from 'node:path'

export type ImageSize = { width: number; height: number; type: string }

/** 从 public/ 下的本地图片读尺寸；外链或读不到时返回 null。 */
export function imageSize(src: string, base = ''): ImageSize | null {
  let p = String(src || '').trim()
  if (!p || /^https?:\/\//i.test(p) || p.startsWith('//')) return null
  if (base && p.startsWith(base)) p = p.slice(base.length)
  if (!p.startsWith('/')) p = `/${p}`
  const file = path.join(process.cwd(), 'public', p)
  let buf: Buffer
  try {
    buf = fs.readFileSync(file)
  } catch {
    return null
  }
  const ext = path.extname(p).toLowerCase()
  const type = ext === '.png' ? 'image/png'
    : ext === '.webp' ? 'image/webp'
      : ext === '.gif' ? 'image/gif'
        : 'image/jpeg'
  if (buf.length > 24 && buf.readUInt32BE(0) === 0x89504e47) {
    return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20), type: 'image/png' }
  }
  if (buf.length > 12 && buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WEBP') {
    const chunk = buf.toString('ascii', 12, 16)
    if (chunk === 'VP8X' && buf.length >= 30) {
      return { width: 1 + buf.readUIntLE(24, 3), height: 1 + buf.readUIntLE(27, 3), type }
    }
    if (chunk === 'VP8 ' && buf.length >= 30) {
      return { width: buf.readUInt16LE(26) & 0x3fff, height: buf.readUInt16LE(28) & 0x3fff, type }
    }
    if (chunk === 'VP8L' && buf.length >= 25) {
      return {
        width: 1 + (((buf[21] & 0x3f) << 8) | buf[20]),
        height: 1 + (((buf[23] & 0xf) << 10) | (buf[22] << 2) | ((buf[21] & 0xc0) >> 6)),
        type,
      }
    }
  }
  if (buf.length > 4 && buf[0] === 0xff && buf[1] === 0xd8) {
    let i = 2
    while (i + 8 < buf.length) {
      if (buf[i] !== 0xff) { i += 1; continue }
      const marker = buf[i + 1]
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { width: buf.readUInt16BE(i + 7), height: buf.readUInt16BE(i + 5), type }
      }
      i += 2 + buf.readUInt16BE(i + 2)
    }
  }
  return null
}
