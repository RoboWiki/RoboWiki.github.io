// 简介拆段：按句聚成短段，避免整块长文堆在一起。
const SENTENCES = /[^。！？；]+[。！？；]?/g
const CLAUSES = /[^，、：]+[，、：]?/g
const MAX_PARA = 120

// 单句超长（规格枚举常见）时按逗号级子句再切，保证每段不超过上限。
function clauseUnits(sentence: string): string[] {
  if (sentence.length <= MAX_PARA) return [sentence]
  const out: string[] = []
  let buf = ''
  for (const clause of sentence.match(CLAUSES) ?? [sentence]) {
    if (buf && buf.length + clause.length > MAX_PARA) {
      out.push(buf)
      buf = ''
    }
    buf += clause
  }
  if (buf) out.push(buf)
  return out
}

export function splitIntro(text: string): string[] {
  const out: string[] = []
  const blocks = text
    .replace(/\r\n?/g, '\n')
    .split(/\n+/)
    .map(b => b.trim())
    .filter(Boolean)
  blocks.forEach((trimmed, bi) => {
    const sentences = (trimmed.match(SENTENCES) ?? [trimmed])
      .map(s => s.trim())
      .filter(Boolean)
      .flatMap(clauseUnits)
    let rest = sentences
    // 首句独立成领读段，先给读者一个落脚点；子句切出的半句不做领读。
    if (bi === 0 && sentences.length > 1 && sentences[0].length <= 60 && /[。！？；]$/.test(sentences[0])) {
      out.push(sentences[0])
      rest = sentences.slice(1)
    }
    let buf = ''
    for (const sentence of rest) {
      if (buf && (buf.length >= 48 || buf.length + sentence.length > MAX_PARA)) {
        out.push(buf)
        buf = ''
      }
      buf += sentence
    }
    if (buf) {
      // 收尾残句并入上一段，避免孤儿短段；但不得突破段长上限。
      const last = out[out.length - 1]
      if (buf.length < 24 && last && last.length + buf.length <= MAX_PARA) out[out.length - 1] = last + buf
      else out.push(buf)
    }
  })
  return out
}

// 先转义再只引入自有标签：简介里的 **粗体** 与 `code` 此前被原样显示。
export function introInline(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}