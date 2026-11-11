/**
 * ds-pet 懒加载挂载器。
 * 只在需要时下载 21KB 组件与 2.9MB 精灵图；空态自动注入，其它页面手动/进入视口时挂载。
 * 素材与许可见同目录 NOTICE.md / LICENSE。
 */
(() => {
  const script = document.currentScript
  const base = ((script && script.dataset.base) || '/').replace(/\/?$/, '/')
  const asset = path => base + path
  let loading = null

  const load = () => {
    if (!loading) {
      loading = import(asset('vendor/ds-pet/web/jingjing-pet.js')).then(mod => {
        mod.registerJingjingPet()
        return mod
      })
    }
    return loading
  }

  const mount = target => {
    if (!target || target.dataset.petMounted) return Promise.resolve()
    target.dataset.petMounted = '1'
    const pet = document.createElement('jingjing-pet')
    pet.setAttribute('src', asset('vendor/ds-pet/codex/jingjing-spritesheet.png'))
    pet.setAttribute('storage-key', 'robowiki-jingjing')
    pet.style.setProperty('--pet-accent', 'var(--rw-primary)')
    pet.style.setProperty('--pet-text', 'var(--rw-ink)')
    pet.style.setProperty('--pet-muted', 'var(--rw-ink-3)')
    pet.style.setProperty('--pet-line', 'var(--rw-border)')
    pet.style.setProperty('--pet-surface', 'var(--rw-surface-2)')
    target.replaceChildren(pet)
    return load()
  }

  let queued = false
  const scanEmptyStates = () => {
    if (queued) return
    queued = true
    requestAnimationFrame(() => {
      queued = false
      document.querySelectorAll('[data-empty]:not([hidden])').forEach(card => {
        if (card.querySelector('[data-jingjing-mounted]')) return
        const box = document.createElement('div')
        box.dataset.jingjingMounted = ''
        box.className = 'mt-6'
        card.append(box)
        mount(box)
      })
    })
  }

  window.__rwPet = { load, mount, scanEmptyStates }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scanEmptyStates)
  else scanEmptyStates()

  new MutationObserver(scanEmptyStates).observe(document.documentElement, {
    subtree: true,
    attributes: true,
    attributeFilter: ['hidden'],
    childList: true,
  })
})()
